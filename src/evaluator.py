"""Agent evaluator: predict-then-act loop with fitness scoring.

Supports any OpenAI-compatible API (OpenAI, Anthropic via proxy, Gemini, local models via ollama/vllm).
Configure via environment variables:
  - OPENAI_API_KEY / OPENAI_BASE_URL / MODEL_NAME  (default)
  - Or pass base_url/api_key/model to configure_client()
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from .genome import AgentGenome
from .tasks import Task, TaskType

logger = logging.getLogger(__name__)

# Module-level config — set via configure_client() or env vars
_client: AsyncOpenAI | None = None
_model_name: str = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-V3.1")


def configure_client(
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> None:
    """Configure the LLM client. Call before running evaluations.

    Works with any OpenAI-compatible API:
      - OpenAI: just set OPENAI_API_KEY
      - Gemini: base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=GEMINI_KEY
      - Local (ollama): base_url="http://localhost:11434/v1", api_key="ollama"
      - Local (vllm): base_url="http://localhost:8000/v1", api_key="none"
      - OpenRouter: base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY
    """
    global _client, _model_name
    if model:
        _model_name = model

    kwargs: dict = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key

    _client = AsyncOpenAI(**kwargs) if kwargs else None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        # Fall back to env-var-based defaults
        kwargs: dict = {}
        base = os.environ.get("OPENAI_BASE_URL")
        if base:
            kwargs["base_url"] = base
        _client = AsyncOpenAI(**kwargs)
    return _client


def get_model() -> str:
    return _model_name


@dataclass
class EvalResult:
    genome_id: str
    task_id: str
    predicted_confidence: float  # 0-1: agent's raw predicted chance of getting it right
    predicted_answer: str
    actual_answer: str
    ground_truth: str
    is_correct: bool
    raw_calibration: float  # 1 - |raw_confidence - outcome|, no bias adjustment
    prediction_accuracy: float  # 1 - |adjusted_confidence - outcome|, with bias
    fitness: float


def _parse_prediction(text: str) -> tuple[float, str]:
    """Extract confidence (0-1) and predicted answer from agent prediction response.

    Uses multiple fallback patterns to robustly extract confidence and answer.
    """
    confidence = 0.5
    confidence_found = False
    answer = ""

    # Try multiple confidence patterns in order of specificity
    confidence_patterns = [
        # Standard format: "Confidence: 75%"
        r"confidence[:\s]*(\d+(?:\.\d+)?)\s*%",
        # Alternative: "75% confident"
        r"(\d+(?:\.\d+)?)\s*%\s*confiden",
        # Fraction format: "Confidence: 0.75"
        r"confidence[:\s]*(0\.\d+)",
        # Natural language: "I'm 75 percent confident"
        r"(?:i\s*(?:am|'m)\s*)?(\d+(?:\.\d+)?)\s*percent\s*confiden",
        # Standalone percentage early in text
        r"^.*?(\d+(?:\.\d+)?)\s*%",
    ]

    for pattern in confidence_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            val = float(match.group(1))
            # Convert to 0-1 range if needed
            confidence = val / 100.0 if val > 1.0 else val
            confidence = max(0.0, min(1.0, confidence))
            confidence_found = True
            break

    # Try multiple answer patterns
    answer_patterns = [
        # Standard format: "Answer: xyz"
        r"(?:answer|prediction):\s*(.+?)(?:\n|$)",
        # After "is" format: "The answer is xyz" (not "is:")
        r"(?:answer|prediction)\s+is:?\s+(.+?)(?:\n|$)",
        # Direct assertion: "It's xyz" or "This is xyz"
        r"(?:it\s*(?:is|'s)|this\s*is)\s+(.+?)(?:\n|$)",
        # After colon without keyword: ": xyz" on answer line
        r":\s*([A-Z][^\n]+?)(?:\n|$)",
    ]

    for pattern in answer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            answer = match.group(1).strip().strip('"').strip("'").strip('.')
            break

    # Fallback: last non-empty line if no structured answer found
    if not answer:
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        answer = lines[-1] if lines else ""

    # Final cleanup
    answer = answer.strip().strip('"').strip("'")

    # Log if confidence parsing failed (still using default 0.5)
    if not confidence_found and "confiden" in text.lower():
        logger.warning(f"Failed to parse confidence from text (using default 0.5): {text[:200]}")

    return confidence, answer


def _check_correct(actual: str, ground_truth: str, task_type: TaskType) -> bool:
    """Check if an answer is correct, with type-appropriate tolerance."""
    actual_clean = actual.lower().strip().rstrip(".").strip('"').strip("'")
    truth_clean = ground_truth.lower().strip().rstrip(".").strip('"').strip("'")

    # numeric tolerance for estimation tasks — check this FIRST
    if task_type == TaskType.ESTIMATION:
        try:
            actual_num = float(re.search(r"[\d,.]+", actual_clean).group().replace(",", ""))
            truth_num = float(re.search(r"[\d,.]+", truth_clean).group().replace(",", ""))
            return abs(actual_num - truth_num) / max(abs(truth_num), 1) < 0.10
        except (AttributeError, ValueError):
            pass

    # for short ground truths (<=3 chars), require word-boundary or exact match
    # to avoid "1" matching inside "210"
    if len(truth_clean) <= 3:
        # try exact match first
        if actual_clean == truth_clean:
            return True
        # word-boundary match
        pattern = r'(?:^|[\s,;:.()\[\]{}])' + re.escape(truth_clean) + r'(?:$|[\s,;:.()\[\]{}])'
        if re.search(pattern, actual_clean):
            return True
        return False

    # longer ground truths: substring match is safe
    if truth_clean in actual_clean or actual_clean in truth_clean:
        return True

    return False


def _score_fitness(
    predicted_confidence: float,
    is_correct: bool,
    confidence_bias: float,
    task_difficulty: float,
) -> tuple[float, float, float]:
    """
    Score fitness based on prediction calibration and task performance.

    Returns (raw_calibration, prediction_accuracy, fitness).

    Fitness = 60% calibration + 40% task accuracy

    This split is intentional (not arbitrary):
    - 60% calibration: Primary objective — agents must know what they know
    - 40% accuracy: Grounding constraint — prevents degenerate "always hedge" strategies

    See FITNESS_FUNCTION_RATIONALE.md for full justification.

    Fitness rewards:
    - Correct answers (weighted by difficulty)
    - Calibrated confidence (predicted confidence close to actual outcome)
    - Penalizes overconfidence on wrong answers
    """
    outcome = 1.0 if is_correct else 0.0

    # Raw calibration: how well the LLM's own confidence matches reality (Brier score)
    raw_calibration = 1.0 - (predicted_confidence - outcome) ** 2

    # Apply confidence bias from genome
    adjusted_confidence = max(0.0, min(1.0, predicted_confidence + confidence_bias))

    # Adjusted prediction accuracy: used for fitness (Brier score — proper scoring rule)
    prediction_accuracy = 1.0 - (adjusted_confidence - outcome) ** 2

    # Task performance: bonus for correct answers scaled by difficulty
    task_score = outcome * (0.5 + 0.5 * task_difficulty)

    # Combined fitness: 60% prediction calibration, 40% task performance
    fitness = 0.6 * prediction_accuracy + 0.4 * task_score

    return raw_calibration, prediction_accuracy, fitness


PREDICTION_PROMPT = """You are being tested on your predictive ability. You will be asked a question.

FIRST: Predict how confident you are that you can answer correctly.
THEN: Provide your answer.

Respond in EXACTLY this format:
Confidence: <number 0-100>%
Answer: <your answer>

Be honest about your confidence. Overconfidence is penalized.

Question: {question}"""


async def run_agent_on_task(genome: AgentGenome, task: Task, max_retries: int = 2) -> EvalResult:
    """Run one agent on one task: predict confidence, answer, score fitness.

    Args:
        genome: The agent configuration to evaluate
        task: The task to evaluate on
        max_retries: Number of retries if parsing fails (default 2)
    """
    oai = get_client()

    system_msg = genome.build_system_message()
    user_msg = PREDICTION_PROMPT.format(question=task.prompt)

    text = ""
    predicted_confidence = 0.5
    predicted_answer = ""

    for attempt in range(max_retries + 1):
        try:
            # Add emphasis on format adherence for retry attempts
            if attempt > 0:
                retry_msg = user_msg + "\n\nREMINDER: You MUST respond with exactly:\nConfidence: <number>%\nAnswer: <your answer>"
            else:
                retry_msg = user_msg

            # Try new parameter first (GPT-4+), fall back to old parameter for compatibility
            try:
                response = await oai.chat.completions.create(
                    model=get_model(),
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": retry_msg},
                    ],
                    temperature=genome.temperature,
                    max_completion_tokens=300,
                )
            except Exception as e:
                if "max_completion_tokens" in str(e):
                    # Fall back to old parameter for older models
                    response = await oai.chat.completions.create(
                        model=get_model(),
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": retry_msg},
                        ],
                        temperature=genome.temperature,
                        max_tokens=300,
                    )
                else:
                    raise
            text = response.choices[0].message.content or ""

            # Try parsing
            predicted_confidence, predicted_answer = _parse_prediction(text)

            # If we got a valid parse (confidence != 0.5 or answer found), accept it
            if predicted_confidence != 0.5 or predicted_answer:
                break

            # If this was the last attempt, keep what we got
            if attempt == max_retries:
                logger.warning(f"Parse failed after {max_retries + 1} attempts for task {task.task_id}")
                break

        except Exception as e:
            logger.error(f"API error on attempt {attempt + 1} for task {task.task_id}: {e}")
            if attempt == max_retries:
                # Final fallback
                text = f"Error: {e}\nConfidence: 50%\nAnswer: unknown"
                predicted_confidence, predicted_answer = _parse_prediction(text)
            else:
                # Retry with exponential backoff
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue

    is_correct = _check_correct(predicted_answer, task.ground_truth, task.task_type)
    raw_calibration, prediction_accuracy, fitness = _score_fitness(
        predicted_confidence, is_correct, genome.confidence_bias, task.difficulty
    )

    return EvalResult(
        genome_id=genome.genome_id,
        task_id=task.task_id,
        predicted_confidence=predicted_confidence,
        predicted_answer=predicted_answer,
        actual_answer=predicted_answer,
        ground_truth=task.ground_truth,
        is_correct=is_correct,
        raw_calibration=raw_calibration,
        prediction_accuracy=prediction_accuracy,
        fitness=fitness,
    )


async def run_generation_tasks(
    genomes: list[AgentGenome],
    tasks: list[Task],
    concurrency: int = 10,
) -> dict[str, list[EvalResult]]:
    """Run all agents on all tasks with bounded concurrency."""
    sem = asyncio.Semaphore(concurrency)
    results: dict[str, list[EvalResult]] = {g.genome_id: [] for g in genomes}

    async def _run(genome: AgentGenome, task: Task):
        async with sem:
            return await run_agent_on_task(genome, task)

    coros = []
    for genome in genomes:
        for task in tasks:
            coros.append(_run(genome, task))

    completed = await asyncio.gather(*coros, return_exceptions=True)

    for result in completed:
        if isinstance(result, EvalResult):
            results[result.genome_id].append(result)

    return results
