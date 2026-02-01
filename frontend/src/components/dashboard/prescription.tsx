"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePrescription } from "@/lib/api";
import { STRATEGY_COLORS, STRATEGY_LABELS, type ReasoningStyle } from "@/lib/types";
import { useState } from "react";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="text-xs text-muted-foreground hover:text-foreground transition-colors"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function TraitRow({
  label,
  value,
  std,
  description,
}: {
  label: string;
  value: string;
  std?: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-border last:border-0">
      <div className="w-36 shrink-0">
        <div className="text-sm font-medium text-foreground">{label}</div>
        {std && (
          <div className="text-xs text-muted-foreground/60 font-mono mt-0.5">
            {std}
          </div>
        )}
      </div>
      <div className="flex-1">
        <div className="text-sm font-mono text-foreground">{value}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{description}</div>
      </div>
    </div>
  );
}

export function Prescription() {
  const { data: rx, isLoading } = usePrescription();

  if (isLoading) {
    return (
      <Card id="prescription" className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Optimized Configuration</CardTitle>
        </CardHeader>
        <CardContent className="h-[200px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!rx || !rx.best_genome) {
    return (
      <Card id="prescription" className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Optimized Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            No prescription available. Run an evolution experiment first.
          </p>
        </CardContent>
      </Card>
    );
  }

  const bg = rx.best_genome;
  const ct = rx.converged_traits;

  // Build the copyable config JSON
  const configJson = JSON.stringify(
    {
      reasoning_strategy: rx.dominant_strategy,
      system_prompt: bg.system_prompt,
      confidence_bias: ct.confidence_bias.mean,
      temperature: ct.temperature.mean,
      risk_tolerance: ct.risk_tolerance.mean,
    },
    null,
    2
  );

  // Interpret the confidence bias direction
  const biasDirection =
    ct.confidence_bias.mean > 0.02
      ? "underconfident"
      : ct.confidence_bias.mean < -0.02
      ? "overconfident"
      : "well-calibrated";

  const biasAdvice =
    ct.confidence_bias.mean > 0.02
      ? `The model is systematically ${biasDirection} by ~${(ct.confidence_bias.mean * 100).toFixed(1)}%. Apply a +${(ct.confidence_bias.mean * 100).toFixed(1)}% correction to confidence outputs.`
      : ct.confidence_bias.mean < -0.02
      ? `The model is systematically ${biasDirection} by ~${(Math.abs(ct.confidence_bias.mean) * 100).toFixed(1)}%. Apply a ${(ct.confidence_bias.mean * 100).toFixed(1)}% correction to confidence outputs.`
      : "The model's confidence is already well-calibrated. No correction needed.";

  return (
    <Card id="prescription" className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-foreground text-base font-medium">
              Optimized Configuration
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Derived from {rx.total_generations} generations of evolution across {rx.population_size} agents
            </p>
          </div>
          <Badge
            variant="outline"
            className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
          >
            Best fitness: {bg.fitness}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Recommended settings */}
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-1">
            Recommended Settings
          </h3>
          <p className="text-xs text-muted-foreground mb-3">
            Population-converged values from the final generation. Low standard deviation = high confidence in this recommendation.
          </p>
          <div className="bg-muted/20 rounded-lg px-4">
            <TraitRow
              label="Reasoning Strategy"
              value={
                STRATEGY_LABELS[rx.dominant_strategy as ReasoningStyle] ||
                rx.dominant_strategy
              }
              std={`${rx.dominant_strategy_pct}% of survivors`}
              description={`Dominated the population. ${
                rx.extinct_strategies.length > 0
                  ? `Outcompeted: ${rx.extinct_strategies.join(", ")}.`
                  : rx.weak_strategies.length > 0
                  ? `Near-extinct: ${rx.weak_strategies.map(s => STRATEGY_LABELS[s as ReasoningStyle] || s).join(", ")}.`
                  : "All strategies survived but this one dominated."
              }`}
            />
            <TraitRow
              label="Confidence Bias"
              value={`${ct.confidence_bias.mean > 0 ? "+" : ""}${(ct.confidence_bias.mean * 100).toFixed(1)}%`}
              std={`\u00B1${(ct.confidence_bias.std * 100).toFixed(1)}%`}
              description={biasAdvice}
            />
            <TraitRow
              label="Temperature"
              value={ct.temperature.mean.toFixed(2)}
              std={`\u00B1${ct.temperature.std.toFixed(2)}`}
              description={
                ct.temperature.mean < 0.5
                  ? "Low temperature converged. The model benefits from more deterministic outputs for these tasks."
                  : ct.temperature.mean > 0.8
                  ? "Higher temperature survived. The model benefits from more exploration/diversity for these tasks."
                  : "Moderate temperature. Balanced exploration and determinism."
              }
            />
            <TraitRow
              label="Risk Tolerance"
              value={ct.risk_tolerance.mean.toFixed(2)}
              std={`\u00B1${ct.risk_tolerance.std.toFixed(2)}`}
              description={
                ct.risk_tolerance.mean > 0.6
                  ? "Higher risk tolerance survived. Agents that commit to uncertain predictions outperformed cautious ones."
                  : ct.risk_tolerance.mean < 0.4
                  ? "Low risk tolerance converged. Cautious prediction strategies were more calibrated."
                  : "Moderate risk tolerance. Balanced approach to uncertainty."
              }
            />
          </div>
        </div>

        {/* Best agent's system prompt */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-foreground">
              Highest-Fitness System Prompt
            </h3>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground font-mono">
                {bg.genome_id.slice(0, 8)}
              </span>
              <Badge
                variant="outline"
                className="border-transparent text-xs"
                style={{
                  backgroundColor: `${STRATEGY_COLORS[bg.reasoning_style as ReasoningStyle] || "#888"}22`,
                  color: STRATEGY_COLORS[bg.reasoning_style as ReasoningStyle] || "#888",
                }}
              >
                {STRATEGY_LABELS[bg.reasoning_style as ReasoningStyle] || bg.reasoning_style}
              </Badge>
            </div>
          </div>
          <div className="bg-muted/20 border border-border rounded-lg p-3">
            <p className="text-sm text-foreground font-mono whitespace-pre-wrap leading-relaxed">
              {bg.system_prompt}
            </p>
          </div>
        </div>

        {/* Copyable config */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-foreground">
              Export Configuration
            </h3>
            <CopyButton text={configJson} />
          </div>
          <pre className="bg-muted/20 border border-border rounded-lg p-3 text-xs text-foreground font-mono overflow-x-auto">
            {configJson}
          </pre>
        </div>

        {/* What to avoid */}
        {(rx.extinct_strategies.length > 0 || rx.weak_strategies.length > 0) && (
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2">
              What to Avoid
            </h3>
            <div className="space-y-2">
              {rx.extinct_strategies.map((s) => (
                <div key={s} className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 rounded-full bg-destructive" />
                  <span className="text-muted-foreground">
                    <span className="text-foreground font-medium capitalize">
                      {STRATEGY_LABELS[s as ReasoningStyle] || s}
                    </span>{" "}
                    — went extinct during evolution
                  </span>
                </div>
              ))}
              {rx.weak_strategies.map((s) => (
                <div key={s} className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 rounded-full bg-amber-500" />
                  <span className="text-muted-foreground">
                    <span className="text-foreground font-medium capitalize">
                      {STRATEGY_LABELS[s as ReasoningStyle] || s}
                    </span>{" "}
                    — near-extinct ({rx.strategy_distribution[s] || 0}/{rx.population_size} agents)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
