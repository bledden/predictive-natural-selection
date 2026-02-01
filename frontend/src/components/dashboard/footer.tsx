"use client";

export function DashboardFooter() {
  return (
    <footer className="flex items-center justify-between px-6 py-4 border-t border-border text-sm">
      <span className="text-muted-foreground">
        Predictive Natural Selection — Finding Free Performance in System Configuration
      </span>
      <a
        href="https://wandb.ai/site/weave"
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary hover:text-primary/80 transition-colors"
      >
        View W&B Weave Traces
      </a>
    </footer>
  );
}
