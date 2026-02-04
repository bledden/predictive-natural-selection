import useSWR, { mutate } from "swr";
import type {
  RunSummary,
  GenerationStats,
  Genome,
  PhylogenyData,
  EvalResult,
  Prescription,
  ExperimentComparison,
  ExperimentInfo,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
};

export function useRunSummary() {
  return useSWR<RunSummary>(`${API_BASE}/api/run`, fetcher);
}

export function useGenerations() {
  return useSWR<GenerationStats[]>(`${API_BASE}/api/generations`, fetcher);
}

export function useGenomes() {
  return useSWR<Genome[]>(`${API_BASE}/api/genomes`, fetcher);
}

export function usePhylogeny() {
  return useSWR<PhylogenyData>(`${API_BASE}/api/phylogeny`, fetcher);
}

export function usePrescription() {
  return useSWR<Prescription>(`${API_BASE}/api/prescription`, fetcher);
}

export function useGenerationResults(generation: number | null) {
  return useSWR<EvalResult[]>(
    generation !== null ? `${API_BASE}/api/results/${generation}` : null,
    fetcher
  );
}

export function useExperiments() {
  return useSWR<ExperimentInfo[]>(`${API_BASE}/api/experiments`, fetcher);
}

export function useComparison() {
  return useSWR<ExperimentComparison[]>(`${API_BASE}/api/comparison`, fetcher);
}

export async function activateExperiment(experimentId: string) {
  const res = await fetch(`${API_BASE}/api/experiments/${experimentId}/activate`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to activate: ${res.status}`);
  // Revalidate all data after switching experiment
  mutate(`${API_BASE}/api/run`);
  mutate(`${API_BASE}/api/generations`);
  mutate(`${API_BASE}/api/genomes`);
  mutate(`${API_BASE}/api/phylogeny`);
  mutate(`${API_BASE}/api/prescription`);
  mutate(`${API_BASE}/api/experiments`);
  return res.json();
}
