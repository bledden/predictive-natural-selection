"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGenerations } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Legend,
} from "recharts";

export function FitnessChart() {
  const { data: generations, isLoading } = useGenerations();

  if (isLoading) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">Fitness Curves</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!generations || generations.length === 0) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">Fitness Curves</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  const chartData = generations.map((g) => ({
    generation: g.generation,
    avg: g.avg_fitness,
    best: g.best_fitness,
    worst: g.worst_fitness,
  }));

  return (
    <Card className="bg-card border-border h-[380px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-foreground text-base font-medium">
          Fitness Curves
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-0.5">Composite fitness score driving natural selection pressure</p>
      </CardHeader>
      <CardContent className="h-[310px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="fitnessGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
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
              domain={[0.4, 1]}
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              tickLine={false}
              label={{
                value: "Fitness",
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
              itemStyle={{ color: "#888" }}
              formatter={(value: number, name: string) => [
                value.toFixed(3),
                name === "avg" ? "Average" : name === "best" ? "Best" : "Worst",
              ]}
              labelFormatter={(label) => `Generation ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }}
              formatter={(value) =>
                value === "avg" ? "Average" : value === "best" ? "Best" : "Worst"
              }
            />
            <Area
              type="monotone"
              dataKey="worst"
              fill="rgba(239, 68, 68, 0.1)"
              stroke="transparent"
            />
            <Area
              type="monotone"
              dataKey="best"
              fill="rgba(34, 197, 94, 0.1)"
              stroke="transparent"
            />
            <Line
              type="monotone"
              dataKey="worst"
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeOpacity={0.5}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="avg"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="best"
              stroke="#22c55e"
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
