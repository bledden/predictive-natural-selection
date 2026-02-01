"use client";

import { Badge } from "@/components/ui/badge";

export function DashboardHeader() {
  return (
    <header className="flex items-center justify-between px-6 py-5 border-b border-border">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Predictive Natural Selection
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Do you need a better system — or a better model?
        </p>
        <p className="text-xs text-muted-foreground/60 mt-0.5">
          Evolving LLM agent behaviors to find free performance hidden in system configuration
        </p>
      </div>
      <Badge
        variant="outline"
        className="border-primary/30 text-primary bg-primary/5 px-3 py-1"
      >
        Powered by W&B Weave
      </Badge>
    </header>
  );
}
