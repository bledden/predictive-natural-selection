"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useGenomes, useRunSummary, useGenerationResults } from "@/lib/api";
import { STRATEGY_COLORS, STRATEGY_LABELS, type ReasoningStyle } from "@/lib/types";
import { useState, useMemo } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export function GenerationExplorer() {
  const { data: runSummary, isLoading: runLoading } = useRunSummary();
  const { data: genomes, isLoading: genomesLoading } = useGenomes();
  const [selectedGeneration, setSelectedGeneration] = useState(0);
  const [expandedGenome, setExpandedGenome] = useState<string | null>(null);

  const { data: results, isLoading: resultsLoading } = useGenerationResults(
    expandedGenome ? selectedGeneration : null
  );

  const isLoading = runLoading || genomesLoading;

  const genomesInGeneration = useMemo(() => {
    if (!genomes) return [];
    return genomes.filter((g) => g.generation === selectedGeneration);
  }, [genomes, selectedGeneration]);

  const genomeResults = useMemo(() => {
    if (!results || !expandedGenome) return [];
    return results.filter((r) => r.genome_id === expandedGenome);
  }, [results, expandedGenome]);

  const totalGenerations = runSummary?.total_generations ?? 20;

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Generation Explorer</CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-foreground text-base font-medium">
            Generation Explorer
          </CardTitle>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Generation:</span>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedGeneration(Math.max(0, selectedGeneration - 1))}
                disabled={selectedGeneration === 0}
                className="h-7 w-7 p-0"
              >
                -
              </Button>
              <span className="text-foreground font-mono w-8 text-center">
                {selectedGeneration}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setSelectedGeneration(Math.min(totalGenerations, selectedGeneration + 1))
                }
                disabled={selectedGeneration === totalGenerations}
                className="h-7 w-7 p-0"
              >
                +
              </Button>
            </div>
          </div>
        </div>
        <div className="mt-3">
          <Slider
            value={[selectedGeneration]}
            onValueChange={([val]) => setSelectedGeneration(val)}
            max={totalGenerations}
            min={0}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>0</span>
            <span>{totalGenerations}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="border border-border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent border-border">
                <TableHead className="w-8"></TableHead>
                <TableHead className="text-muted-foreground">Genome ID</TableHead>
                <TableHead className="text-muted-foreground">Reasoning Style</TableHead>
                <TableHead className="text-muted-foreground text-right">Conf. Bias</TableHead>
                <TableHead className="text-muted-foreground text-right">Temperature</TableHead>
                <TableHead className="text-muted-foreground text-right">Memory Window</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {genomesInGeneration.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="text-center text-muted-foreground py-8"
                  >
                    No genomes found for generation {selectedGeneration}
                  </TableCell>
                </TableRow>
              ) : (
                genomesInGeneration.map((genome) => (
                  <Collapsible
                    key={genome.genome_id}
                    open={expandedGenome === genome.genome_id}
                    onOpenChange={(open) =>
                      setExpandedGenome(open ? genome.genome_id : null)
                    }
                    asChild
                  >
                    <>
                      <CollapsibleTrigger asChild>
                        <TableRow className="cursor-pointer hover:bg-muted/50 border-border">
                          <TableCell className="w-8">
                            {expandedGenome === genome.genome_id ? (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-sm text-foreground">
                            {genome.genome_id.slice(0, 8)}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className="border-transparent"
                              style={{
                                backgroundColor: `${
                                  STRATEGY_COLORS[genome.reasoning_style] || "#888"
                                }22`,
                                color: STRATEGY_COLORS[genome.reasoning_style] || "#888",
                              }}
                            >
                              {STRATEGY_LABELS[genome.reasoning_style] ||
                                genome.reasoning_style}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm text-foreground">
                            {genome.confidence_bias.toFixed(3)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm text-foreground">
                            {genome.temperature.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm text-foreground">
                            {genome.memory_window}
                          </TableCell>
                        </TableRow>
                      </CollapsibleTrigger>
                      <CollapsibleContent asChild>
                        <TableRow className="hover:bg-transparent border-border bg-muted/30">
                          <TableCell colSpan={6} className="p-0">
                            <div className="p-4 space-y-4">
                              {/* Genome Details */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <span className="text-muted-foreground">Risk Tolerance:</span>
                                  <span className="text-foreground ml-2 font-mono">
                                    {genome.risk_tolerance.toFixed(2)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Memory Weighting:</span>
                                  <span className="text-foreground ml-2 capitalize">
                                    {genome.memory_weighting}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Parents:</span>
                                  <span className="text-foreground ml-2 font-mono">
                                    {genome.parent_ids.length > 0
                                      ? genome.parent_ids.map((p) => p.slice(0, 6)).join(", ")
                                      : "None"}
                                  </span>
                                </div>
                              </div>

                              {/* System Prompt */}
                              {genome.system_prompt && (
                                <div className="text-sm">
                                  <span className="text-muted-foreground">System Prompt:</span>
                                  <p className="text-foreground mt-1 bg-background p-2 rounded border border-border text-xs font-mono whitespace-pre-wrap">
                                    {genome.system_prompt}
                                  </p>
                                </div>
                              )}

                              {/* Task Results */}
                              {resultsLoading ? (
                                <div className="text-muted-foreground text-sm animate-pulse">
                                  Loading task results...
                                </div>
                              ) : genomeResults.length > 0 ? (
                                <div>
                                  <span className="text-muted-foreground text-sm">
                                    Task Results ({genomeResults.length})
                                  </span>
                                  <div className="mt-2 max-h-[200px] overflow-auto">
                                    <Table>
                                      <TableHeader>
                                        <TableRow className="hover:bg-transparent border-border">
                                          <TableHead className="text-muted-foreground text-xs">
                                            Task ID
                                          </TableHead>
                                          <TableHead className="text-muted-foreground text-xs">
                                            Predicted
                                          </TableHead>
                                          <TableHead className="text-muted-foreground text-xs">
                                            Truth
                                          </TableHead>
                                          <TableHead className="text-muted-foreground text-xs text-center">
                                            Correct
                                          </TableHead>
                                          <TableHead className="text-muted-foreground text-xs text-right">
                                            Confidence
                                          </TableHead>
                                          <TableHead className="text-muted-foreground text-xs text-right">
                                            Fitness
                                          </TableHead>
                                        </TableRow>
                                      </TableHeader>
                                      <TableBody>
                                        {genomeResults.map((result) => (
                                          <TableRow
                                            key={result.task_id}
                                            className="hover:bg-muted/30 border-border"
                                          >
                                            <TableCell className="font-mono text-xs text-foreground">
                                              {result.task_id}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs text-foreground">
                                              {result.predicted_answer}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs text-foreground">
                                              {result.ground_truth}
                                            </TableCell>
                                            <TableCell className="text-center">
                                              <Badge
                                                variant="outline"
                                                className={
                                                  result.is_correct
                                                    ? "border-primary/40 text-primary bg-primary/10"
                                                    : "border-destructive/40 text-destructive bg-destructive/10"
                                                }
                                              >
                                                {result.is_correct ? "Yes" : "No"}
                                              </Badge>
                                            </TableCell>
                                            <TableCell className="text-right font-mono text-xs text-foreground">
                                              {(result.predicted_confidence * 100).toFixed(0)}%
                                            </TableCell>
                                            <TableCell className="text-right font-mono text-xs text-foreground">
                                              {result.fitness.toFixed(3)}
                                            </TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </div>
                                </div>
                              ) : (
                                <div className="text-muted-foreground text-sm">
                                  No task results available
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      </CollapsibleContent>
                    </>
                  </Collapsible>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
