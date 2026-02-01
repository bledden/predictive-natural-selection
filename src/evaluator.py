"""Agent evaluator: predict-then-act loop with fitness scoring.

Supports any OpenAI-compatible API (OpenAI, Anthropic via proxy, Gemini, local models via ollama/vllm).
Configure via environment variables:
  - OPENAI_API_KEY / OPENAI_BASE_URL / MODEL_NAME  (default)
  - Or pass base_url/api_key/model to configure_client()
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from .genome import AgentGenome
from .tasks import Task, TaskType

# Module-level config — set via configure_client() or env vars
_client: AsyncOpenAI | None = None
_model_name: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")


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
    """Extract confidence (0-1) and predicted answer from agent prediction response."""
    confidence = 0.5
    answer = ""

    # look for confidence
    conf_match = re.search(r"confidence[:\s]*(\d+(?:\.\d+)?)\s*%?", text, re.IGNORECASE)
    if conf_match:
        val = float(conf_match.group(1))
        confidence = val / 100.0 if val > 1.0 else val

    # look for answer in structured format
    ans_match = re.search(r"(?:answer|prediction)[:\s]*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if ans_match:
        answer = ans_match.group(1).strip().strip('"').strip("'")
    else:
        # fallback: last non-empty line
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        answer = lines[-1] if lines else ""

    return max(0.0, min(1.0, confidence)), answer


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

    Fitness rewards:
    - Correct answers (weighted by difficulty)
    - Calibrated confidence (predicted confidence close to actual outcome)
    - Penalizes overconfidence on wrong answers
    """
    outcome = 1.0 if is_correct else 0.0

    # Raw calibration: how well the LLM's own confidence matches reality
    raw_calibration = 1.0 - abs(predicted_confidence - outcome)

    # Apply confidence bias from genome
    adjusted_confidence = max(0.0, min(1.0, predicted_confidence + confidence_bias))

    # Adjusted prediction accuracy: used for fitness
    prediction_accuracy = 1.0 - abs(adjusted_confidence - outcome)

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


async def run_agent_on_task(genome: AgentGenome, task: Task) -> EvalResult:
    """Run one agent on one task: predict confidence, answer, score fitness."""
    oai = get_client()

    system_msg = genome.build_system_message()
    user_msg = PREDICTION_PROMPT.format(question=task.prompt)

    try:
        response = await oai.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=genome.temperature,
            max_tokens=300,
        )
        text = response.choices[0].message.content or ""
    except Exception as e:
        text = f"Error: {e}\nConfidence: 50%\nAnswer: unknown"

    predicted_confidence, predicted_answer = _parse_prediction(text)
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
