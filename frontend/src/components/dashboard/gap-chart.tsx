"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGenerations } from "@/lib/api";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Line,
  Legend,
} from "recharts";

export function GapChart() {
  const { data: generations, isLoading } = useGenerations();

  if (isLoading) {
    return (
      <Card className="bg-card border-border h-[420px]">
        <CardHeader>
          <CardTitle className="text-foreground">The System Optimization Gap</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[320px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!generations || generations.length === 0) {
    return (
      <Card className="bg-card border-border h-[420px]">
        <CardHeader>
          <CardTitle className="text-foreground">The System Optimization Gap</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[320px]">
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  // Build chart data with the gap as a stacked area on top of rawCalibration
  const chartData = generations.map((g) => {
    const raw = g.avg_raw_calibration;
    const evolved = g.avg_prediction_accuracy;
    return {
      generation: g.generation,
      rawCalibration: raw,
      evolvedCalibration: evolved,
      // gap stacked on top of raw gives us the filled area between the lines
      gap: Math.max(0, evolved - raw),
    };
  });

  const finalGap = chartData[chartData.length - 1]?.gap ?? 0;

  return (
    <Card className="bg-card border-border h-[420px]">
      <CardHeader className="pb-1">
        <CardTitle className="text-foreground text-base font-medium">
          The System Optimization Gap
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Shaded area = calibration improvement from behavioral evolution alone, with the same underlying model
        </p>
      </CardHeader>
      <CardContent className="h-[340px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="gapGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0.08} />
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
              domain={[0.6, 1]}
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
              tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              label={{
                value: "Calibration",
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
              formatter={(value: number, name: string) => {
                if (name === "gap") {
                  return [`+${(value * 100).toFixed(1)}%`, "System Gain"];
                }
                return [
                  `${(value * 100).toFixed(1)}%`,
                  name === "rawCalibration"
                    ? "Model Baseline"
                    : "System Optimized",
                ];
              }}
              labelFormatter={(label) => `Generation ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }}
              formatter={(value) =>
                value === "rawCalibration"
                  ? "Model Baseline"
                  : value === "evolvedCalibration"
                  ? "System Optimized"
                  : `Free Performance (+${(finalGap * 100).toFixed(1)}%)`
              }
            />
            {/* Base: raw calibration area (transparent, just defines the floor) */}
            <Area
              type="monotone"
              dataKey="rawCalibration"
              stackId="calibration"
              fill="transparent"
              stroke="transparent"
            />
            {/* Gap area stacked on top of raw = fills between raw and evolved */}
            <Area
              type="monotone"
              dataKey="gap"
              stackId="calibration"
              fill="url(#gapGradient)"
              stroke="transparent"
            />
            {/* Raw calibration line (flat, teal, dashed) */}
            <Line
              type="monotone"
              dataKey="rawCalibration"
              stroke="#14b8a6"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 4 }}
            />
            {/* Evolved calibration line (climbing, purple, solid) */}
            <Line
              type="monotone"
              dataKey="evolvedCalibration"
              stroke="#a855f7"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
