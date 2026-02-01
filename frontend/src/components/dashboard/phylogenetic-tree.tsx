"use client";

import React from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePhylogeny, useRunSummary } from "@/lib/api";
import { STRATEGY_COLORS, STRATEGY_LABELS, type ReasoningStyle } from "@/lib/types";
import { useMemo, useState, useCallback, useRef, useEffect } from "react";

interface NodePosition {
  id: string;
  x: number;
  y: number;
  generation: number;
  reasoning_style: ReasoningStyle;
  confidence_bias: number;
  temperature: number;
  system_prompt: string;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  node: NodePosition | null;
}

export function PhylogeneticTree() {
  const { data: phylogeny, isLoading: phyloLoading } = usePhylogeny();
  const { data: runSummary, isLoading: runLoading } = useRunSummary();
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    node: null,
  });
  const svgRef = useRef<SVGSVGElement>(null);

  const isLoading = phyloLoading || runLoading;

  const { nodePositions, edges, svgWidth, svgHeight } = useMemo(() => {
    if (!phylogeny || !runSummary) {
      return { nodePositions: [], edges: [], svgWidth: 800, svgHeight: 400 };
    }

    const totalGenerations = runSummary.total_generations;
    const padding = 60;
    const width = Math.max(800, (totalGenerations + 1) * 80);
    const height = 450;

    // Group nodes by generation
    const nodesByGen: Record<number, typeof phylogeny.nodes> = {};
    phylogeny.nodes.forEach((node) => {
      if (!nodesByGen[node.generation]) {
        nodesByGen[node.generation] = [];
      }
      nodesByGen[node.generation].push(node);
    });

    // Calculate positions
    const positions: NodePosition[] = [];
    const nodeIdToPosition: Record<string, NodePosition> = {};

    Object.entries(nodesByGen).forEach(([gen, nodes]) => {
      const genNum = parseInt(gen);
      const x = padding + (genNum / totalGenerations) * (width - 2 * padding);
      const nodeCount = nodes.length;

      nodes.forEach((node, i) => {
        // Distribute nodes vertically with some jitter
        const baseY = padding + ((i + 0.5) / nodeCount) * (height - 2 * padding);
        const jitter = (Math.sin(node.id.charCodeAt(0) * 12.5) * 15);
        const y = Math.max(padding, Math.min(height - padding, baseY + jitter));

        const pos: NodePosition = {
          id: node.id,
          x,
          y,
          generation: node.generation,
          reasoning_style: node.reasoning_style,
          confidence_bias: node.confidence_bias,
          temperature: node.temperature,
          system_prompt: node.system_prompt,
        };
        positions.push(pos);
        nodeIdToPosition[node.id] = pos;
      });
    });

    // Map edges to positions
    const mappedEdges = phylogeny.edges
      .filter((e) => nodeIdToPosition[e.source] && nodeIdToPosition[e.target])
      .map((e) => ({
        source: nodeIdToPosition[e.source],
        target: nodeIdToPosition[e.target],
      }));

    return {
      nodePositions: positions,
      edges: mappedEdges,
      svgWidth: width,
      svgHeight: height,
    };
  }, [phylogeny, runSummary]);

  const handleMouseEnter = useCallback(
    (node: NodePosition, event: React.MouseEvent) => {
      const svgRect = svgRef.current?.getBoundingClientRect();
      if (svgRect) {
        setTooltip({
          visible: true,
          x: event.clientX - svgRect.left,
          y: event.clientY - svgRect.top,
          node,
        });
      }
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  }, []);

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Phylogenetic Tree</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[450px]">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!phylogeny || nodePositions.length === 0) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Phylogenetic Tree</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[450px]">
          <div className="text-muted-foreground">No phylogeny data available</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-foreground text-base font-medium">
            Phylogenetic Tree
          </CardTitle>
          <div className="flex flex-wrap gap-3">
            {(Object.keys(STRATEGY_COLORS) as ReasoningStyle[]).map((strategy) => (
              <div key={strategy} className="flex items-center gap-1.5">
                <div
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: STRATEGY_COLORS[strategy] }}
                />
                <span className="text-xs text-muted-foreground">
                  {STRATEGY_LABELS[strategy]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <div className="relative min-w-[800px]">
          <svg
            ref={svgRef}
            width={svgWidth}
            height={svgHeight}
            className="w-full"
            style={{ minWidth: svgWidth }}
          >
            {/* Generation labels */}
            {runSummary &&
              Array.from({ length: runSummary.total_generations + 1 }, (_, i) => {
                const x =
                  60 + (i / runSummary.total_generations) * (svgWidth - 120);
                return (
                  <text
                    key={i}
                    x={x}
                    y={svgHeight - 15}
                    textAnchor="middle"
                    className="fill-muted-foreground text-[10px]"
                  >
                    Gen {i}
                  </text>
                );
              })}

            {/* Edges */}
            {edges.map((edge, i) => (
              <path
                key={i}
                d={`M ${edge.source.x} ${edge.source.y} 
                    C ${edge.source.x + 30} ${edge.source.y}, 
                      ${edge.target.x - 30} ${edge.target.y}, 
                      ${edge.target.x} ${edge.target.y}`}
                fill="none"
                stroke="rgba(255,255,255,0.15)"
                strokeWidth={1}
              />
            ))}

            {/* Nodes */}
            {nodePositions.map((node) => (
              <g key={node.id}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={6}
                  fill={STRATEGY_COLORS[node.reasoning_style] || "#888"}
                  stroke="rgba(0,0,0,0.3)"
                  strokeWidth={1}
                  className="cursor-pointer transition-all hover:r-8"
                  onMouseEnter={(e) => handleMouseEnter(node, e)}
                  onMouseLeave={handleMouseLeave}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={10}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={(e) => handleMouseEnter(node, e)}
                  onMouseLeave={handleMouseLeave}
                />
              </g>
            ))}
          </svg>

          {/* Tooltip */}
          {tooltip.visible && tooltip.node && (
            <div
              className="absolute pointer-events-none z-50 bg-popover border border-border rounded-lg shadow-xl p-3 max-w-[280px]"
              style={{
                left: Math.min(tooltip.x + 15, svgWidth - 300),
                top: Math.max(tooltip.y - 80, 10),
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor:
                      STRATEGY_COLORS[tooltip.node.reasoning_style] || "#888",
                  }}
                />
                <span className="font-medium text-foreground text-sm">
                  {STRATEGY_LABELS[tooltip.node.reasoning_style]}
                </span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ID:</span>
                  <span className="text-foreground font-mono">
                    {tooltip.node.id.slice(0, 8)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Generation:</span>
                  <span className="text-foreground">{tooltip.node.generation}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence Bias:</span>
                  <span className="text-foreground">
                    {tooltip.node.confidence_bias.toFixed(3)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Temperature:</span>
                  <span className="text-foreground">
                    {tooltip.node.temperature.toFixed(2)}
                  </span>
                </div>
                {tooltip.node.system_prompt && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <span className="text-muted-foreground">System Prompt:</span>
                    <p className="text-foreground mt-1 line-clamp-3">
                      {tooltip.node.system_prompt.slice(0, 100)}...
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
