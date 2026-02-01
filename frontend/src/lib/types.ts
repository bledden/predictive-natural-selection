export interface RunSummary {
  total_generations: number;
  population_size: number;
  initial_avg_fitness: number;
  final_avg_fitness: number;
  fitness_improvement: number;
  best_fitness: number;
  initial_raw_calibration: number;
  final_raw_calibration: number;
  initial_evolved_calibration: number;
  final_evolved_calibration: number;
  initial_task_accuracy: number;
  final_task_accuracy: number;
  dominant_strategy: string;
  strategy_counts: Record<string, number>;
  extinct_strategies: string[];
}

export interface GenerationStats {
  generation: number;
  population_size: number;
  avg_fitness: number;
  best_fitness: number;
  worst_fitness: number;
  avg_raw_calibration: number;
  avg_prediction_accuracy: number;
  avg_task_accuracy: number;
  dominant_reasoning: string;
  dominant_memory: string;
  elapsed_seconds: number;
}

export interface Genome {
  genome_id: string;
  system_prompt: string;
  reasoning_style: ReasoningStyle;
  memory_window: number;
  memory_weighting: string;
  confidence_bias: number;
  risk_tolerance: number;
  temperature: number;
  generation: number;
  parent_ids: string[];
  fitness_history: number[];
}

export interface PhylogenyNode {
  id: string;
  generation: number;
  reasoning_style: ReasoningStyle;
  confidence_bias: number;
  temperature: number;
  system_prompt: string;
}

export interface PhylogenyEdge {
  source: string;
  target: string;
}

export interface PhylogenyData {
  nodes: PhylogenyNode[];
  edges: PhylogenyEdge[];
}

export interface EvalResult {
  generation: number;
  genome_id: string;
  task_id: string;
  predicted_confidence: number;
  predicted_answer: string;
  ground_truth: string;
  is_correct: boolean;
  raw_calibration: number;
  prediction_accuracy: number;
  fitness: number;
}

export interface Prescription {
  gap: number;
  gap_pct: number;
  raw_calibration: number;
  evolved_calibration: number;
  best_genome: {
    genome_id: string;
    fitness: number;
    reasoning_style: string;
    system_prompt: string;
    confidence_bias: number;
    temperature: number;
    risk_tolerance: number;
  } | null;
  converged_traits: {
    confidence_bias: { mean: number; std: number };
    temperature: { mean: number; std: number };
    risk_tolerance: { mean: number; std: number };
  };
  dominant_strategy: string;
  dominant_strategy_pct: number;
  strategy_distribution: Record<string, number>;
  extinct_strategies: string[];
  weak_strategies: string[];
  total_generations: number;
  population_size: number;
}

export type ReasoningStyle =
  | "chain-of-thought"
  | "step-by-step"
  | "analogical"
  | "debate-self"
  | "first-principles"
  | "elimination";

export const STRATEGY_COLORS: Record<ReasoningStyle, string> = {
  "chain-of-thought": "#e74c3c",
  "step-by-step": "#3498db",
  "analogical": "#2ecc71",
  "debate-self": "#f39c12",
  "first-principles": "#9b59b6",
  "elimination": "#1abc9c",
};

export const STRATEGY_LABELS: Record<ReasoningStyle, string> = {
  "chain-of-thought": "Chain of Thought",
  "step-by-step": "Step by Step",
  "analogical": "Analogical",
  "debate-self": "Debate Self",
  "first-principles": "First Principles",
  "elimination": "Elimination",
};
