"use client";

import { useComparison, useExperiments, activateExperiment } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const VERDICT_CONFIG: Record<
  string,
  { color: string; bg: string; border: string; icon: string }
> = {
  already_optimized: {
    color: "text-amber-400",
    bg: "bg-amber-900/20",
    border: "border-amber-500/30",
    icon: "~",
  },
  system_helps: {
    color: "text-emerald-400",
    bg: "bg-emerald-900/20",
    border: "border-emerald-500/30",
    icon: "+",
  },
  need_better_model: {
    color: "text-red-400",
    bg: "bg-red-900/20",
    border: "border-red-500/30",
    icon: "-",
  },
};

export function ModelComparison() {
  const { data: comparison, error, isLoading } = useComparison();
  const { data: experiments } = useExperiments();
  const [switching, setSwitching] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Multi-Model Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-muted rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !comparison) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Multi-Model Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No comparison data available.</p>
        </CardContent>
      </Card>
    );
  }

  const activeExperiment = experiments?.find((e) => e.active)?.id;

  async function handleSwitch(experimentId: string) {
    setSwitching(experimentId);
    try {
      await activateExperiment(experimentId);
    } catch (e) {
      console.error("Failed to switch experiment:", e);
    } finally {
      setSwitching(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">
          Multi-Model Comparison: System vs Model
        </CardTitle>
        <CardDescription>
          12 experiments across 4 models reveal when system optimization helps vs
          when you need a better model. Click any model to explore its evolution
          data.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Category headers */}
        <div className="space-y-6">
          {/* Frontier Models */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Frontier Models
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {comparison
                .filter((m) => m.category === "frontier")
                .map((model) => (
                  <ModelCard
                    key={model.id}
                    model={model}
                    isActive={model.id === activeExperiment}
                    isSwitching={switching === model.id}
                    onSwitch={() => handleSwitch(model.id)}
                  />
                ))}
            </div>
          </div>

          {/* Previous-Gen Models */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Previous-Generation Models
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {comparison
                .filter((m) => m.category === "previous_gen")
                .map((model) => (
                  <ModelCard
                    key={model.id}
                    model={model}
                    isActive={model.id === activeExperiment}
                    isSwitching={switching === model.id}
                    onSwitch={() => handleSwitch(model.id)}
                  />
                ))}
            </div>
          </div>
        </div>

        {/* Summary insight */}
        <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border">
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">Key Insight:</span>{" "}
            Frontier models (Claude Opus 4.5, GPT-5.2) are already well-calibrated
            with near-zero optimization gaps. Previous-gen and mid-tier models
            (GPT-4o, DeepSeek V3) show negative gaps, indicating system optimization
            cannot compensate for fundamental capability limitations.{" "}
            <span className="font-semibold text-foreground">
              The answer: upgrade the model, not the system.
            </span>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function ModelCard({
  model,
  isActive,
  isSwitching,
  onSwitch,
}: {
  model: {
    id: string;
    name: string;
    category: string;
    test_set: {
      raw_calibration: number;
      evolved_calibration: number;
      gap_pct: number;
      task_accuracy: number;
    };
    fitness: { initial: number; final: number; improvement: number };
    dominant_strategy: string;
    verdict: string;
    verdict_label: string;
  };
  isActive: boolean;
  isSwitching: boolean;
  onSwitch: () => void;
}) {
  const config = VERDICT_CONFIG[model.verdict] || VERDICT_CONFIG.already_optimized;

  return (
    <button
      onClick={onSwitch}
      disabled={isSwitching}
      className={`text-left p-4 rounded-lg border transition-all hover:scale-[1.02] ${
        isActive
          ? `${config.bg} ${config.border} border-2 ring-1 ring-offset-1 ring-offset-background ring-current`
          : "bg-card border-border hover:border-foreground/20"
      } ${isSwitching ? "opacity-50" : ""}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-foreground">{model.name}</span>
        {isActive && (
          <Badge variant="outline" className="text-xs">
            Active
          </Badge>
        )}
      </div>

      {/* Gap indicator */}
      <div className={`text-2xl font-mono font-bold ${config.color} mb-1`}>
        {model.test_set.gap_pct > 0 ? "+" : ""}
        {model.test_set.gap_pct.toFixed(1)}%
        <span className="text-xs font-normal ml-1">gap</span>
      </div>

      {/* Verdict */}
      <Badge
        className={`${config.bg} ${config.color} border ${config.border} text-xs mb-2`}
      >
        {model.verdict_label}
      </Badge>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-muted-foreground mt-2">
        <div>
          Raw:{" "}
          <span className="text-foreground">
            {model.test_set.raw_calibration.toFixed(1)}%
          </span>
        </div>
        <div>
          Evolved:{" "}
          <span className="text-foreground">
            {model.test_set.evolved_calibration.toFixed(1)}%
          </span>
        </div>
        <div>
          Accuracy:{" "}
          <span className="text-foreground">
            {model.test_set.task_accuracy.toFixed(1)}%
          </span>
        </div>
        <div>
          Strategy:{" "}
          <span className="text-foreground capitalize">
            {model.dominant_strategy.replace(/-/g, " ")}
          </span>
        </div>
      </div>

      {isSwitching && (
        <p className="text-xs text-muted-foreground mt-2 animate-pulse">
          Loading...
        </p>
      )}
    </button>
  );
}
