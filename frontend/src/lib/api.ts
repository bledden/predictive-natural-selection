import useSWR from "swr";
import type {
  RunSummary,
  GenerationStats,
  Genome,
  PhylogenyData,
  EvalResult,
  Prescription,
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
