"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGenerations, useGenomes } from "@/lib/api";
import { STRATEGY_COLORS, STRATEGY_LABELS, type ReasoningStyle } from "@/lib/types";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useMemo } from "react";

export function TraitDistributionChart() {
  const { data: generations, isLoading: genLoading } = useGenerations();
  const { data: genomes, isLoading: genomesLoading } = useGenomes();

  const isLoading = genLoading || genomesLoading;

  const chartData = useMemo(() => {
    if (!generations || !genomes) return [];

    const strategies = Object.keys(STRATEGY_COLORS) as ReasoningStyle[];

    return generations.map((gen) => {
      const genomesInGen = genomes.filter((g) => g.generation === gen.generation);
      const total = genomesInGen.length || 1;

      const counts: Record<string, number> = {};
      strategies.forEach((strategy) => {
        const count = genomesInGen.filter(
          (g) => g.reasoning_style === strategy
        ).length;
        counts[strategy] = count / total;
      });

      return {
        generation: gen.generation,
        ...counts,
      };
    });
  }, [generations, genomes]);

  if (isLoading) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">Trait Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">Trait Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  const strategies = Object.keys(STRATEGY_COLORS) as ReasoningStyle[];

  return (
    <Card className="bg-card border-border h-[380px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-foreground text-base font-medium">
          Trait Distribution
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[310px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.1)"
              vertical={false}
            />
            <XAxis
              dataKey="generation"
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
              label={{
                value: "Generation",
                position: "insideBottom",
                offset: -5,
                fill: "#666",
                fontSize: 11,
              }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
              tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              label={{
                value: "Proportion",
                angle: -90,
                position: "insideLeft",
                fill: "#666",
                fontSize: 11,
              }}
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
                `${(value * 100).toFixed(1)}%`,
                STRATEGY_LABELS[name as ReasoningStyle] || name,
              ]}
              labelFormatter={(label) => `Generation ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: "10px", paddingTop: "10px" }}
              formatter={(value) =>
                STRATEGY_LABELS[value as ReasoningStyle] || value
              }
            />
            {strategies.map((strategy) => (
              <Area
                key={strategy}
                type="monotone"
                dataKey={strategy}
                stackId="1"
                fill={STRATEGY_COLORS[strategy]}
                stroke={STRATEGY_COLORS[strategy]}
                fillOpacity={0.8}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
