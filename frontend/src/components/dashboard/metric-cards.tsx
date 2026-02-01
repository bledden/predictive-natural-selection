"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useRunSummary, useGenerations } from "@/lib/api";
import { STRATEGY_COLORS, type ReasoningStyle } from "@/lib/types";
import {
  LineChart,
  Line,
  ResponsiveContainer,
} from "recharts";

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const chartData = data.map((value, index) => ({ value, index }));
  return (
    <div className="h-8 w-24">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ImprovementBadge({ value, label }: { value: number; label?: string }) {
  const isPositive = value >= 0;
  return (
    <Badge
      variant="outline"
      className={`text-xs ${
        isPositive
          ? "border-primary/40 text-primary bg-primary/10"
          : "border-destructive/40 text-destructive bg-destructive/10"
      }`}
    >
      {isPositive ? "+" : ""}
      {(value * 100).toFixed(1)}%{label ? ` ${label}` : ""}
    </Badge>
  );
}

export function MetricCards() {
  const { data: runSummary, isLoading: runLoading } = useRunSummary();
  const { data: generations, isLoading: genLoading } = useGenerations();

  const isLoading = runLoading || genLoading;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-card border-border animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-muted rounded w-20" />
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-muted rounded w-16 mb-2" />
              <div className="h-4 bg-muted rounded w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!runSummary || !generations) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                No Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">--</div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const gap = runSummary.final_evolved_calibration - runSummary.final_raw_calibration;
  const gapData = generations.map(
    (g) => g.avg_prediction_accuracy - g.avg_raw_calibration
  );
  const rawChange = runSummary.final_raw_calibration - runSummary.initial_raw_calibration;
  const calibrationImprovement =
    runSummary.final_evolved_calibration - runSummary.initial_evolved_calibration;

  const totalPopulation = Object.values(runSummary.strategy_counts).reduce(
    (a, b) => a + b,
    0
  );
  const dominantCount =
    runSummary.strategy_counts[runSummary.dominant_strategy] || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* System Gap Card */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            System Gap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                +{(gap * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Free performance from config
              </div>
            </div>
            <Sparkline data={gapData} color="#34d399" />
          </div>
        </CardContent>
      </Card>

      {/* Model Baseline Card */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Model Baseline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-foreground">
            {(runSummary.final_raw_calibration * 100).toFixed(1)}%
          </div>
          <div className="flex items-center gap-2 mt-1">
            <ImprovementBadge value={rawChange} />
            <span className="text-xs text-muted-foreground">
              unchanged
            </span>
          </div>
        </CardContent>
      </Card>

      {/* System Optimized Card */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            System Optimized
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-foreground">
            {(runSummary.final_evolved_calibration * 100).toFixed(1)}%
          </div>
          <div className="mt-1">
            <ImprovementBadge value={calibrationImprovement} />
          </div>
        </CardContent>
      </Card>

      {/* Dominant Strategy Card */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Dominant Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor:
                  STRATEGY_COLORS[runSummary.dominant_strategy as ReasoningStyle] ||
                  "#888",
              }}
            />
            <span className="text-lg font-bold text-foreground capitalize">
              {runSummary.dominant_strategy.replace("-", " ")}
            </span>
          </div>
          <div className="text-sm text-muted-foreground mt-1">
            {dominantCount}/{totalPopulation} agents
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
