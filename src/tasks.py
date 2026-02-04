"""Task generator: produces diverse prediction tasks with ground-truth answers."""

from __future__ import annotations

import json as _json
import logging
import random
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path as _Path

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    TRIVIA = "trivia"
    ESTIMATION = "estimation"
    REASONING = "reasoning"


@dataclass
class Task:
    task_id: str
    task_type: TaskType
    prompt: str
    ground_truth: str  # canonical correct answer
    difficulty: float  # 0.0-1.0 subjective difficulty


# ── Task banks ──────────────────────────────────────────────────

TRIVIA_TASKS = [
    # Easy (calibration anchors — agents should be confident here)
    Task("t01", TaskType.TRIVIA, "What is the chemical symbol for gold?", "Au", 0.1),
    Task("t02", TaskType.TRIVIA, "What planet is closest to the Sun?", "Mercury", 0.1),
    # Medium
    Task("t03", TaskType.TRIVIA, "What is the capital of Australia?", "Canberra", 0.4),
    Task("t04", TaskType.TRIVIA, "In what year was the Treaty of Westphalia signed?", "1648", 0.7),
    Task("t05", TaskType.TRIVIA, "What is the second most abundant element in Earth's crust by mass?", "Silicon", 0.6),
    # Hard — obscure facts that LLMs often get wrong
    Task("t06", TaskType.TRIVIA, "What is the smallest country in Africa by land area?", "Seychelles", 0.8),
    Task("t07", TaskType.TRIVIA, "Who was the first person to observe Saturn's rings (though he didn't know what they were)?", "Galileo", 0.7),
    Task("t08", TaskType.TRIVIA, "What is the only letter that doesn't appear in any U.S. state name?", "Q", 0.8),
    Task("t09", TaskType.TRIVIA, "In what year did the last confirmed smallpox case occur?", "1978", 0.9),
    Task("t10", TaskType.TRIVIA, "What is the longest river entirely within one country?", "Yangtze", 0.8),
    # Trick / commonly-wrong
    Task("t11", TaskType.TRIVIA, "How many time zones does China officially use?", "1", 0.8),
    Task("t12", TaskType.TRIVIA, "What fruit is the most produced in the world by weight?", "Tomato", 0.7),
    Task("t13", TaskType.TRIVIA, "Which has more neurons: a human brain or a dog's brain?", "Human", 0.3),
    Task("t14", TaskType.TRIVIA, "What color is a polar bear's skin (not fur)?", "Black", 0.7),
    Task("t15", TaskType.TRIVIA, "What country has the most islands?", "Sweden", 0.8),
]

ESTIMATION_TASKS = [
    # Easy anchors
    Task("e01", TaskType.ESTIMATION, "Estimate the number of bones in the adult human body.", "206", 0.3),
    Task("e02", TaskType.ESTIMATION, "Estimate the boiling point of water at sea level in Fahrenheit.", "212", 0.2),
    # Medium — requires actual knowledge
    Task("e03", TaskType.ESTIMATION, "Estimate the population of Nigeria in millions (nearest 10).", "220", 0.6),
    Task("e04", TaskType.ESTIMATION, "Estimate the depth of the Mariana Trench in meters (nearest 500).", "11000", 0.6),
    Task("e05", TaskType.ESTIMATION, "Estimate the number of airports in the United States (nearest 1000).", "19000", 0.8),
    # Hard — Fermi estimation, requires reasoning
    Task("e06", TaskType.ESTIMATION, "Estimate the number of piano tuners in Chicago (nearest 50).", "200", 0.9),
    Task("e07", TaskType.ESTIMATION, "Estimate the total length of all roads in the US in millions of miles (nearest integer).", "4", 0.9),
    Task("e08", TaskType.ESTIMATION, "Estimate the number of golf balls that fit in a school bus (nearest 10000).", "500000", 0.9),
    Task("e09", TaskType.ESTIMATION, "Estimate the weight of all ants on Earth compared to all humans. Is the total ant biomass heavier? Answer the ratio (ant mass / human mass) to nearest 0.1.", "0.1", 0.9),
    Task("e10", TaskType.ESTIMATION, "Estimate the number of satellites currently orbiting Earth (nearest 1000).", "10000", 0.8),
    # Counterintuitive
    Task("e11", TaskType.ESTIMATION, "Estimate the average distance between stars in the Milky Way in light-years (nearest integer).", "5", 0.8),
    Task("e12", TaskType.ESTIMATION, "Estimate the number of grains of sand on all of Earth's beaches, as a power of 10 (e.g., answer '18' for 10^18).", "18", 0.9),
]

REASONING_TASKS = [
    # Classic cognitive traps
    Task(
        "r01", TaskType.REASONING,
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost in cents?",
        "5", 0.5,
    ),
    Task(
        "r02", TaskType.REASONING,
        "If it takes 5 machines 5 minutes to make 5 widgets, how many minutes would it take 100 machines to make 100 widgets?",
        "5", 0.5,
    ),
    Task(
        "r03", TaskType.REASONING,
        "In a lake, there is a patch of lily pads. Every day, the patch doubles in size. If it takes 48 days for the patch to cover the entire lake, how many days would it take for the patch to cover half the lake?",
        "47", 0.4,
    ),
    # Formal logic — LLMs frequently fail these
    Task(
        "r04", TaskType.REASONING,
        "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly? Answer Yes or No.",
        "No", 0.7,
    ),
    Task(
        "r05", TaskType.REASONING,
        "All cats are animals. Some animals are dogs. Therefore, some cats are dogs. Is this argument valid? Answer Yes or No.",
        "No", 0.7,
    ),
    Task(
        "r06", TaskType.REASONING,
        "If no fish are birds, and some birds can swim, can we conclude that some things that swim are not fish? Answer Yes or No.",
        "Yes", 0.8,
    ),
    # Math traps
    Task(
        "r07", TaskType.REASONING,
        "Is 91 prime? Answer Yes or No.",
        "No", 0.7,
    ),
    Task(
        "r08", TaskType.REASONING,
        "What is 17 * 23? Answer with just the number.",
        "391", 0.6,
    ),
    Task(
        "r09", TaskType.REASONING,
        "A train leaves at 2:00 PM going 60 mph. Another leaves the same station at 3:00 PM going 90 mph in the same direction. At what time does the second train catch the first? Answer in HH:MM PM format.",
        "5:00 PM", 0.7,
    ),
    # Spatial/counterfactual — hard for LLMs
    Task(
        "r10", TaskType.REASONING,
        "I have a drawer with 10 black socks and 10 white socks. It's dark and I can't see. What is the minimum number of socks I must pull out to guarantee a matching pair?",
        "3", 0.5,
    ),
    Task(
        "r11", TaskType.REASONING,
        "You are in a race and you pass the person in second place. What place are you in now?",
        "2", 0.5,
    ),
    Task(
        "r12", TaskType.REASONING,
        "A man is looking at a photograph. Someone asks 'Who is in the picture?' He replies: 'Brothers and sisters I have none, but that man's father is my father's son.' Who is in the picture?",
        "His son", 0.8,
    ),
    # Multi-step / tricky
    Task(
        "r13", TaskType.REASONING,
        "You have 12 coins, one of which is counterfeit and either heavier or lighter than the rest. Using a balance scale exactly 3 times, can you always identify the counterfeit coin AND determine whether it is heavier or lighter? Answer Yes or No.",
        "Yes", 0.9,
    ),
    Task(
        "r14", TaskType.REASONING,
        "There are three boxes: one contains only apples, one contains only oranges, and one contains both. All labels are wrong. You can pick one fruit from one box. From which box should you pick to determine all labels? Answer: the box labeled 'Both', 'Apples', or 'Oranges'.",
        "Both", 0.8,
    ),
    Task(
        "r15", TaskType.REASONING,
        "If you have a 4-minute hourglass and a 7-minute hourglass, how do you measure exactly 9 minutes? Answer with the total time measured.",
        "9", 0.9,
    ),
]

ALL_TASKS = TRIVIA_TASKS + ESTIMATION_TASKS + REASONING_TASKS

# ── Active task pool (mutable — defaults to built-in, replaced by load_tasks_from_file) ──
_active_trivia: list[Task] = list(TRIVIA_TASKS)
_active_estimation: list[Task] = list(ESTIMATION_TASKS)
_active_reasoning: list[Task] = list(REASONING_TASKS)
_active_all: list[Task] = list(ALL_TASKS)


def set_task_pool(tasks: list[Task]) -> None:
    """Replace the active task pool with a custom set of tasks.

    Partitions tasks by type into the per-type pools.
    Clears any cached splits/batches so they rebuild from the new pool.
    """
    global _active_trivia, _active_estimation, _active_reasoning, _active_all

    _active_trivia = [t for t in tasks if t.task_type == TaskType.TRIVIA]
    _active_estimation = [t for t in tasks if t.task_type == TaskType.ESTIMATION]
    _active_reasoning = [t for t in tasks if t.task_type == TaskType.REASONING]
    _active_all = list(tasks)

    # Clear cached splits so they rebuild from new pool
    _FIXED_TASK_SETS.clear()
    _TRAIN_VAL_TEST_SPLITS.clear()


def load_tasks_from_file(path: str) -> list[Task]:
    """Load tasks from a JSON file and set them as the active task pool.

    JSON format: list of objects with fields:
      - prompt (required): The question text
      - ground_truth (required): The correct answer
      - task_type (optional): "trivia", "estimation", or "reasoning" (default: "reasoning")
      - difficulty (optional): 0.0-1.0 (default: 0.5)
      - task_id (optional): unique identifier (default: auto-generated)

    Returns the loaded tasks.
    Raises ValueError/FileNotFoundError for invalid input.
    """
    file_path = _Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {path}")

    with open(file_path) as f:
        raw = _json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"Tasks file must contain a JSON array, got {type(raw).__name__}")

    if len(raw) < 1:
        raise ValueError("Tasks file must contain at least 1 task")

    TYPE_MAP = {
        "trivia": TaskType.TRIVIA,
        "estimation": TaskType.ESTIMATION,
        "reasoning": TaskType.REASONING,
    }

    tasks: list[Task] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"Task {i}: expected object, got {type(entry).__name__}")
        if "prompt" not in entry:
            raise ValueError(f"Task {i}: missing required field 'prompt'")
        if "ground_truth" not in entry:
            raise ValueError(f"Task {i}: missing required field 'ground_truth'")

        type_str = entry.get("task_type", "reasoning").lower()
        task_type = TYPE_MAP.get(type_str, TaskType.REASONING)

        difficulty = entry.get("difficulty", 0.5)
        if not (0.0 <= float(difficulty) <= 1.0):
            raise ValueError(f"Task {i}: difficulty must be 0.0-1.0, got {difficulty}")

        task_id = entry.get("task_id", f"custom_{i + 1:03d}")

        tasks.append(Task(
            task_id=str(task_id),
            task_type=task_type,
            prompt=str(entry["prompt"]),
            ground_truth=str(entry["ground_truth"]),
            difficulty=float(difficulty),
        ))

    if len(tasks) < 10:
        warnings.warn(
            f"Only {len(tasks)} tasks loaded. For meaningful evolution, "
            f"consider providing at least 15-20 tasks.",
            stacklevel=2,
        )

    set_task_pool(tasks)
    logger.info("Loaded %d custom tasks from %s", len(tasks), path)
    return tasks


def get_task_batch(n: int = 8, seed: int | None = None) -> list[Task]:
    """Get a diverse batch of tasks, mixing types.

    Uses a consistent task pool seeded once per run, so fitness is
    comparable across generations. Each generation gets a shuffled
    version of the same core task set.
    """
    rng = random.Random(seed)
    # ensure at least one of each type
    batch: list[Task] = []
    for pool in [_active_trivia, _active_estimation, _active_reasoning]:
        if pool:
            batch.append(rng.choice(pool))
    # fill the rest randomly
    remaining = [t for t in _active_all if t not in batch]
    fill_count = max(0, n - len(batch))
    batch.extend(rng.sample(remaining, min(fill_count, len(remaining))))
    rng.shuffle(batch)
    return batch[:n]


# Pre-built consistent task sets for reproducible runs
_FIXED_TASK_SETS: dict[int, list[Task]] = {}
_TRAIN_VAL_TEST_SPLITS: dict[int, tuple[list[Task], list[Task], list[Task]]] = {}


def get_train_val_test_split(
    run_seed: int = 42,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
) -> tuple[list[Task], list[Task], list[Task]]:
    """Split ALL_TASKS into train/validation/test sets.

    Args:
        run_seed: Random seed for reproducible splits
        train_ratio: Fraction of tasks for training (default 0.6 = 27 tasks)
        val_ratio: Fraction for validation (default 0.2 = 9 tasks)
        test_ratio: Implicit (1 - train - val = 0.2 = 9 tasks)

    Returns:
        (train_tasks, val_tasks, test_tasks)

    Strategy:
        - Stratified split: maintain task type distribution in each set
        - Train: Used during evolution for fitness scoring
        - Val: Used for early stopping / convergence detection (future use)
        - Test: NEVER seen during evolution, used only for final evaluation
    """
    if run_seed in _TRAIN_VAL_TEST_SPLITS:
        return _TRAIN_VAL_TEST_SPLITS[run_seed]

    rng = random.Random(run_seed)
    test_ratio = 1.0 - train_ratio - val_ratio

    train_tasks: list[Task] = []
    val_tasks: list[Task] = []
    test_tasks: list[Task] = []

    # Stratified split: maintain type distribution in each set
    for pool in [_active_trivia, _active_estimation, _active_reasoning]:
        if not pool:
            continue
        shuffled = list(pool)
        rng.shuffle(shuffled)

        n_total = len(shuffled)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)

        train_tasks.extend(shuffled[:n_train])
        val_tasks.extend(shuffled[n_train:n_train + n_val])
        test_tasks.extend(shuffled[n_train + n_val:])

    # Shuffle within each set
    rng.shuffle(train_tasks)
    rng.shuffle(val_tasks)
    rng.shuffle(test_tasks)

    _TRAIN_VAL_TEST_SPLITS[run_seed] = (train_tasks, val_tasks, test_tasks)
    return train_tasks, val_tasks, test_tasks


def get_rotating_task_batch(n: int = 15, generation: int = 0, run_seed: int = 42) -> list[Task]:
    """Get a task batch that varies per generation, preventing task memorization.

    Args:
        n: Number of tasks to sample
        generation: Current generation number (changes the sample each gen)
        run_seed: Base random seed for reproducibility

    Each generation gets a different subset of training tasks, seeded
    deterministically by (run_seed, generation). This prevents evolution
    from overfitting to a fixed set of tasks.
    """
    combined_seed = run_seed * 1000 + generation
    train_tasks, _, _ = get_train_val_test_split(run_seed)
    rng = random.Random(combined_seed)

    # Type-diverse sampling from training pool
    batch: list[Task] = []
    for pool_type in [TaskType.TRIVIA, TaskType.ESTIMATION, TaskType.REASONING]:
        typed = [t for t in train_tasks if t.task_type == pool_type]
        k = max(1, n // 3)
        batch.extend(rng.sample(typed, min(k, len(typed))))

    # Fill remaining slots
    remaining = [t for t in train_tasks if t not in batch]
    if remaining and len(batch) < n:
        batch.extend(rng.sample(remaining, min(n - len(batch), len(remaining))))

    rng.shuffle(batch)
    return batch[:n]


def get_fixed_task_batch(n: int = 8, run_seed: int = 42, split: str = "train") -> list[Task]:
    """Get a fixed task batch that stays the same across generations.

    Args:
        n: Number of tasks to sample
        run_seed: Random seed for reproducibility
        split: Which data split to use ("train", "val", "test", or "all")

    Call once per run with a seed, then reuse for every generation.
    This makes fitness comparable across generations.

    IMPORTANT: Use split="train" during evolution, split="test" for final evaluation.
    """
    cache_key = (run_seed, split)

    if cache_key not in _FIXED_TASK_SETS:
        rng = random.Random(run_seed)

        # Get appropriate task pool based on split
        if split == "all":
            task_pool = _active_all
        elif split == "train":
            train_tasks, _, _ = get_train_val_test_split(run_seed)
            task_pool = train_tasks
        elif split == "val":
            _, val_tasks, _ = get_train_val_test_split(run_seed)
            task_pool = val_tasks
        elif split == "test":
            _, _, test_tasks = get_train_val_test_split(run_seed)
            task_pool = test_tasks
        else:
            raise ValueError(f"Invalid split: {split}. Must be 'train', 'val', 'test', or 'all'")

        # Sample from the pool, ensuring type diversity
        batch: list[Task] = []

        # Get one of each type from the pool if possible
        trivia_pool = [t for t in task_pool if t.task_type == TaskType.TRIVIA]
        estimation_pool = [t for t in task_pool if t.task_type == TaskType.ESTIMATION]
        reasoning_pool = [t for t in task_pool if t.task_type == TaskType.REASONING]

        if trivia_pool:
            batch.append(rng.choice(trivia_pool))
        if estimation_pool:
            batch.append(rng.choice(estimation_pool))
        if reasoning_pool:
            batch.append(rng.choice(reasoning_pool))

        # Fill remaining slots
        remaining = [t for t in task_pool if t not in batch]
        if remaining:
            batch.extend(rng.sample(remaining, min(n - len(batch), len(remaining))))

        rng.shuffle(batch)
        _FIXED_TASK_SETS[cache_key] = batch[:n]

    return _FIXED_TASK_SETS[cache_key]
