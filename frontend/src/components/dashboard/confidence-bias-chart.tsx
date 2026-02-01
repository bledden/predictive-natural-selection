"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGenerations, useGenomes } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";
import { useMemo } from "react";

export function ConfidenceBiasChart() {
  const { data: generations, isLoading: genLoading } = useGenerations();
  const { data: genomes, isLoading: genomesLoading } = useGenomes();

  const isLoading = genLoading || genomesLoading;

  const chartData = useMemo(() => {
    if (!generations || !genomes) return [];

    return generations.map((gen) => {
      const genomesInGen = genomes.filter((g) => g.generation === gen.generation);

      if (genomesInGen.length === 0) {
        return {
          generation: gen.generation,
          avg: 0,
          upper: 0,
          lower: 0,
        };
      }

      const biases = genomesInGen.map((g) => g.confidence_bias);
      const avg = biases.reduce((a, b) => a + b, 0) / biases.length;
      const variance =
        biases.reduce((sum, b) => sum + Math.pow(b - avg, 2), 0) / biases.length;
      const stdDev = Math.sqrt(variance);

      return {
        generation: gen.generation,
        avg,
        upper: avg + stdDev,
        lower: avg - stdDev,
      };
    });
  }, [generations, genomes]);

  if (isLoading) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">Confidence Bias Evolution</CardTitle>
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
          <CardTitle className="text-foreground">Confidence Bias Evolution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  // Calculate domain
  const allValues = chartData.flatMap((d) => [d.upper, d.lower]);
  const minVal = Math.min(...allValues, -0.3);
  const maxVal = Math.max(...allValues, 0.3);

  return (
    <Card className="bg-card border-border h-[380px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-foreground text-base font-medium">
          Confidence Bias Evolution
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[310px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="biasGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
              </linearGradient>
            </defs>
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
              domain={[minVal - 0.1, maxVal + 0.1]}
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
              tickFormatter={(value) => value.toFixed(2)}
              label={{
                value: "Confidence Bias",
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
                value.toFixed(3),
                name === "avg"
                  ? "Average"
                  : name === "upper"
                  ? "Upper (1 SD)"
                  : "Lower (1 SD)",
              ]}
              labelFormatter={(label) => `Generation ${label}`}
            />
            <ReferenceLine
              y={0}
              stroke="#666"
              strokeDasharray="5 5"
              label={{
                value: "Neutral",
                position: "right",
                fill: "#666",
                fontSize: 10,
              }}
            />
            {/* Std dev band */}
            <Area
              type="monotone"
              dataKey="upper"
              fill="url(#biasGradient)"
              stroke="transparent"
            />
            <Area
              type="monotone"
              dataKey="lower"
              fill="rgba(15, 23, 42, 1)"
              stroke="transparent"
            />
            <Line
              type="monotone"
              dataKey="upper"
              stroke="#ef4444"
              strokeWidth={1}
              strokeOpacity={0.5}
              strokeDasharray="3 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="lower"
              stroke="#ef4444"
              strokeWidth={1}
              strokeOpacity={0.5}
              strokeDasharray="3 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="avg"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
