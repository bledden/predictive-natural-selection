"use client";

import React from "react";
import { DashboardHeader } from "@/components/dashboard/header";
import { DiagnosisHero } from "@/components/dashboard/diagnosis-hero";
import { MetricCards } from "@/components/dashboard/metric-cards";
import { GapChart } from "@/components/dashboard/gap-chart";
import { FitnessChart } from "@/components/dashboard/fitness-chart";
import { CalibrationChart } from "@/components/dashboard/calibration-chart";
import { TraitDistributionChart } from "@/components/dashboard/trait-distribution-chart";
import { ConfidenceBiasChart } from "@/components/dashboard/confidence-bias-chart";
import { PhylogeneticTree } from "@/components/dashboard/phylogenetic-tree";
import { GenerationExplorer } from "@/components/dashboard/generation-explorer";
import { LiveEvolution } from "@/components/dashboard/live-evolution";
import { Prescription } from "@/components/dashboard/prescription";
import { ModelComparison } from "@/components/dashboard/model-comparison";
import { DashboardFooter } from "@/components/dashboard/footer";

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; name: string },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 m-2">
          <p className="text-red-400 font-mono text-sm">
            [{this.props.name}] {this.state.error.message}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function Dashboard() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <ErrorBoundary name="Header">
        <DashboardHeader />
      </ErrorBoundary>

      <main className="flex-1 p-6 space-y-6">
        {/* THE DIAGNOSIS */}
        <section>
          <ErrorBoundary name="DiagnosisHero">
            <DiagnosisHero />
          </ErrorBoundary>
        </section>

        {/* MULTI-MODEL COMPARISON */}
        <section>
          <ErrorBoundary name="ModelComparison">
            <ModelComparison />
          </ErrorBoundary>
        </section>

        {/* KEY METRICS */}
        <section>
          <ErrorBoundary name="MetricCards">
            <MetricCards />
          </ErrorBoundary>
        </section>

        {/* THE PRESCRIPTION */}
        <section>
          <ErrorBoundary name="Prescription">
            <Prescription />
          </ErrorBoundary>
        </section>

        {/* THE GAP VISUALIZATION */}
        <section>
          <ErrorBoundary name="GapChart">
            <GapChart />
          </ErrorBoundary>
        </section>

        {/* SYSTEM VS MODEL PERFORMANCE */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ErrorBoundary name="CalibrationChart">
            <CalibrationChart />
          </ErrorBoundary>
          <ErrorBoundary name="FitnessChart">
            <FitnessChart />
          </ErrorBoundary>
        </section>

        {/* HOW EVOLUTION OPTIMIZED THE SYSTEM */}
        <section>
          <h2 className="text-lg font-semibold text-foreground mb-4">
            How Evolution Optimized the System
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ErrorBoundary name="TraitDistribution">
              <TraitDistributionChart />
            </ErrorBoundary>
            <ErrorBoundary name="ConfidenceBias">
              <ConfidenceBiasChart />
            </ErrorBoundary>
          </div>
        </section>

        {/* RUN NEW EXPERIMENT */}
        <section>
          <ErrorBoundary name="LiveEvolution">
            <LiveEvolution />
          </ErrorBoundary>
        </section>

        {/* EVOLUTIONARY LINEAGE */}
        <section>
          <ErrorBoundary name="PhylogeneticTree">
            <PhylogeneticTree />
          </ErrorBoundary>
        </section>

        {/* DETAILED DATA */}
        <section>
          <ErrorBoundary name="GenerationExplorer">
            <GenerationExplorer />
          </ErrorBoundary>
        </section>
      </main>

      <ErrorBoundary name="Footer">
        <DashboardFooter />
      </ErrorBoundary>
    </div>
  );
}
