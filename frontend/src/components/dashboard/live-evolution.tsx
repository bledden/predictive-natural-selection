"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { STRATEGY_COLORS, STRATEGY_LABELS, type ReasoningStyle } from "@/lib/types";
import { useState, useCallback, useRef } from "react";
import { useSWRConfig } from "swr";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface GenerationEvent {
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
}

type RunPhase = "idle" | "running" | "complete" | "error";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";

export function LiveEvolution() {
  const { mutate } = useSWRConfig();
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [population, setPopulation] = useState(10);
  const [generations, setGenerations] = useState(8);
  const [tasks, setTasks] = useState(8);
  const [generationData, setGenerationData] = useState<GenerationEvent[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const startRun = useCallback(async () => {
    setPhase("running");
    setGenerationData([]);
    setErrorMsg("");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(
        `${API_BASE}/api/live/run?population=${population}&generations=${generations}&tasks=${tasks}`,
        { signal: controller.signal }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const json = line.slice(6);
          try {
            const event = JSON.parse(json);
            if (event.type === "generation") {
              setGenerationData((prev) => [...prev, event]);
            } else if (event.type === "complete") {
              setPhase("complete");
              // Revalidate all SWR caches so dashboard charts update
              mutate(() => true, undefined, { revalidate: true });
            } else if (event.type === "error") {
              setErrorMsg(event.message);
              setPhase("error");
            }
          } catch {
            // skip malformed JSON
          }
        }
      }

      // If stream ended without complete event
      if (phase === "running") {
        setPhase("complete");
        mutate(() => true, undefined, { revalidate: true });
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setErrorMsg(e instanceof Error ? e.message : "Unknown error");
      setPhase("error");
    }
  }, [population, generations, tasks, mutate, phase]);

  const stopRun = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
  }, []);

  const currentGen = generationData.length > 0 ? generationData[generationData.length - 1] : null;
  const progress = generationData.length / generations;

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-foreground text-base font-medium">
            Run New Experiment
          </CardTitle>
          <div className="flex items-center gap-2">
            {phase === "running" && (
              <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10 animate-pulse">
                Gen {generationData.length}/{generations}
              </Badge>
            )}
            {phase === "complete" && (
              <Badge variant="outline" className="border-primary/40 text-primary bg-primary/10">
                Complete
              </Badge>
            )}
            {phase === "error" && (
              <Badge variant="outline" className="border-destructive/40 text-destructive bg-destructive/10">
                Error
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        {phase === "idle" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground flex justify-between">
                  <span>Population</span>
                  <span className="text-foreground font-mono">{population}</span>
                </label>
                <Slider
                  value={[population]}
                  onValueChange={([v]) => setPopulation(v)}
                  min={4}
                  max={30}
                  step={2}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground flex justify-between">
                  <span>Generations</span>
                  <span className="text-foreground font-mono">{generations}</span>
                </label>
                <Slider
                  value={[generations]}
                  onValueChange={([v]) => setGenerations(v)}
                  min={3}
                  max={30}
                  step={1}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground flex justify-between">
                  <span>Tasks per Gen</span>
                  <span className="text-foreground font-mono">{tasks}</span>
                </label>
                <Slider
                  value={[tasks]}
                  onValueChange={([v]) => setTasks(v)}
                  min={4}
                  max={20}
                  step={2}
                />
              </div>
            </div>
            <Button onClick={startRun} className="w-full">
              Start Evolution Run
            </Button>
          </div>
        )}

        {/* Progress bar */}
        {phase === "running" && (
          <div className="space-y-2">
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Evaluating {population} agents on {tasks} tasks...</span>
              <span>{Math.round(progress * 100)}%</span>
            </div>
          </div>
        )}

        {/* Live fitness chart */}
        {generationData.length > 0 && (
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={generationData.map((g) => ({
                  gen: g.generation,
                  avg: g.avg_fitness,
                  best: g.best_fitness,
                  calibration: g.avg_prediction_accuracy,
                }))}
                margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.1)"
                  vertical={false}
                />
                <XAxis
                  dataKey="gen"
                  tick={{ fill: "#888", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0.3, 1]}
                  tick={{ fill: "#888", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "#fff" }}
                  formatter={(value: number, name: string) => [
                    value.toFixed(3),
                    name === "avg"
                      ? "Avg Fitness"
                      : name === "best"
                      ? "Best Fitness"
                      : "Calibration",
                  ]}
                  labelFormatter={(label) => `Generation ${label}`}
                />
                <Legend
                  wrapperStyle={{ fontSize: "11px" }}
                  formatter={(value) =>
                    value === "avg"
                      ? "Avg Fitness"
                      : value === "best"
                      ? "Best Fitness"
                      : "Calibration"
                  }
                />
                <Line
                  type="monotone"
                  dataKey="avg"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="best"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="calibration"
                  stroke="#a855f7"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Current generation stats */}
        {currentGen && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-muted/30 rounded-lg p-3">
              <div className="text-xs text-muted-foreground">Avg Fitness</div>
              <div className="text-lg font-bold text-foreground font-mono">
                {currentGen.avg_fitness.toFixed(3)}
              </div>
            </div>
            <div className="bg-muted/30 rounded-lg p-3">
              <div className="text-xs text-muted-foreground">Best Fitness</div>
              <div className="text-lg font-bold text-foreground font-mono">
                {currentGen.best_fitness.toFixed(3)}
              </div>
            </div>
            <div className="bg-muted/30 rounded-lg p-3">
              <div className="text-xs text-muted-foreground">Calibration</div>
              <div className="text-lg font-bold text-foreground font-mono">
                {(currentGen.avg_prediction_accuracy * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-muted/30 rounded-lg p-3">
              <div className="text-xs text-muted-foreground">Dominant</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div
                  className="w-2.5 h-2.5 rounded-full"
                  style={{
                    backgroundColor:
                      STRATEGY_COLORS[currentGen.dominant_reasoning as ReasoningStyle] || "#888",
                  }}
                />
                <span className="text-sm font-medium text-foreground capitalize">
                  {STRATEGY_LABELS[currentGen.dominant_reasoning as ReasoningStyle] ||
                    currentGen.dominant_reasoning}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {phase === "error" && errorMsg && (
          <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3">
            <p className="text-destructive text-sm font-mono">{errorMsg}</p>
          </div>
        )}

        {/* Action buttons */}
        {phase === "running" && (
          <Button variant="destructive" onClick={stopRun} className="w-full">
            Stop Run
          </Button>
        )}
        {(phase === "complete" || phase === "error") && (
          <Button variant="outline" onClick={() => setPhase("idle")} className="w-full">
            New Run
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
