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

export function CalibrationChart() {
  const { data: generations, isLoading } = useGenerations();

  if (isLoading) {
    return (
      <Card className="bg-card border-border h-[380px]">
        <CardHeader>
          <CardTitle className="text-foreground">System vs Model Performance</CardTitle>
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
          <CardTitle className="text-foreground">System vs Model Performance</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[280px]">
          <div className="text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  const chartData = generations.map((g) => ({
    generation: g.generation,
    rawCalibration: g.avg_raw_calibration,
    evolvedCalibration: g.avg_prediction_accuracy,
    taskAccuracy: g.avg_task_accuracy,
  }));

  return (
    <Card className="bg-card border-border h-[380px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-foreground text-base font-medium">
          System vs Model Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[310px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="evolutionGainGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0.05} />
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
                value: "Accuracy",
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
                name === "rawCalibration"
                  ? "Model Baseline"
                  : name === "evolvedCalibration"
                  ? "System Optimized"
                  : "Task Accuracy",
              ]}
              labelFormatter={(label) => `Generation ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }}
              formatter={(value) =>
                value === "rawCalibration"
                  ? "Model Baseline"
                  : value === "evolvedCalibration"
                  ? "System Optimized"
                  : "Task Accuracy"
              }
            />
            {/* Shaded area between raw and evolved */}
            <Area
              type="monotone"
              dataKey="evolvedCalibration"
              fill="url(#evolutionGainGradient)"
              stroke="transparent"
            />
            <Line
              type="monotone"
              dataKey="rawCalibration"
              stroke="#14b8a6"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="evolvedCalibration"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="taskAccuracy"
              stroke="#f97316"
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
