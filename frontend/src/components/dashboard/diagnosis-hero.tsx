"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useRunSummary, useGenerations } from "@/lib/api";

type Verdict = "system" | "mixed" | "model";

const VERDICT_CONFIG: Record<
  Verdict,
  { border: string; bg: string; text: string; label: string; description: string }
> = {
  system: {
    border: "border-l-emerald-500",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    label: "System optimization available",
    description:
      "Your system is leaving significant performance on the table. You don't need a better model — you need better configuration.",
  },
  mixed: {
    border: "border-l-amber-500",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    label: "Moderate gains available",
    description:
      "Some performance gains are available from system optimization. Consider both system tuning and model upgrades.",
  },
  model: {
    border: "border-l-red-500",
    bg: "bg-red-500/10",
    text: "text-red-400",
    label: "Model upgrade needed",
    description:
      "Your system configuration is near-optimal for this model. To go further, you need a better model.",
  },
};

function BarIndicator({
  label,
  value,
  color,
  maxValue = 1,
}: {
  label: string;
  value: number;
  color: string;
  maxValue?: number;
}) {
  const pct = (value / maxValue) * 100;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-mono">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function DiagnosisHero() {
  const { data: runSummary, isLoading: runLoading } = useRunSummary();
  const { data: generations, isLoading: genLoading } = useGenerations();

  if (runLoading || genLoading) {
    return (
      <Card className="bg-card border-border border-l-4 border-l-muted">
        <CardContent className="py-8">
          <div className="animate-pulse space-y-3">
            <div className="h-10 bg-muted rounded w-48" />
            <div className="h-4 bg-muted rounded w-96" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!runSummary || !generations || generations.length === 0) {
    return (
      <Card className="bg-card border-border border-l-4 border-l-muted">
        <CardContent className="py-8">
          <p className="text-muted-foreground">
            No evolution data available. Run an experiment to see the diagnosis.
          </p>
        </CardContent>
      </Card>
    );
  }

  const rawCalib = runSummary.final_raw_calibration;
  const evolvedCalib = runSummary.final_evolved_calibration;
  const gap = evolvedCalib - rawCalib;
  const gapPct = (gap * 100).toFixed(1);

  const verdict: Verdict = gap > 0.05 ? "system" : gap > 0.02 ? "mixed" : "model";
  const config = VERDICT_CONFIG[verdict];

  return (
    <Card className={`bg-card border-border border-l-4 ${config.border}`}>
      <CardContent className="py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Diagnosis */}
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-baseline gap-3">
              <span className={`text-4xl font-bold font-mono ${config.text}`}>
                +{gapPct}%
              </span>
              <span className="text-lg text-muted-foreground">
                from system optimization alone
              </span>
            </div>
            <div
              className={`inline-block px-3 py-1 rounded-md text-sm font-medium ${config.bg} ${config.text}`}
            >
              {config.label}
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
              {config.description}
            </p>
            <p className="text-xs text-muted-foreground/60">
              Based on {runSummary.total_generations} generations of evolution with{" "}
              {runSummary.population_size} agents. Dominant surviving strategy:{" "}
              <span className="text-foreground capitalize">
                {runSummary.dominant_strategy.replace("-", " ")}
              </span>
              .{" "}
              <a
                href="#prescription"
                className="text-primary hover:text-primary/80 transition-colors underline underline-offset-2"
              >
                See optimized configuration below
              </a>
            </p>
          </div>

          {/* Right: Before/After bars */}
          <div className="space-y-4 flex flex-col justify-center">
            <BarIndicator
              label="Model Baseline"
              value={rawCalib}
              color="#14b8a6"
              maxValue={1}
            />
            <BarIndicator
              label="System Optimized"
              value={evolvedCalib}
              color="#a855f7"
              maxValue={1}
            />
            <div className="pt-1 border-t border-border">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Free performance gap</span>
                <span className={`font-mono font-medium ${config.text}`}>
                  +{gapPct}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
