"""Visualization: phylogenetic trees, fitness curves, trait distribution charts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

from .orchestrator import EvolutionRun


COLORS = {
    "chain-of-thought": "#e74c3c",
    "step-by-step": "#3498db",
    "analogical": "#2ecc71",
    "debate-self": "#f39c12",
    "first-principles": "#9b59b6",
    "elimination": "#1abc9c",
}


def plot_fitness_curves(run: EvolutionRun, output_path: str = "data/fitness_curves.png") -> str:
    """Plot average, best, and worst fitness over generations."""
    gens = [s.generation for s in run.generation_stats]
    avg = [s.avg_fitness for s in run.generation_stats]
    best = [s.best_fitness for s in run.generation_stats]
    worst = [s.worst_fitness for s in run.generation_stats]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(gens, avg, "o-", color="#3498db", linewidth=2, label="Average Fitness")
    ax.plot(gens, best, "^-", color="#2ecc71", linewidth=2, label="Best Fitness")
    ax.plot(gens, worst, "v-", color="#e74c3c", linewidth=1, alpha=0.6, label="Worst Fitness")
    ax.fill_between(gens, worst, best, alpha=0.1, color="#3498db")
    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Fitness", fontsize=12)
    ax.set_title("Fitness Over Generations", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_prediction_accuracy(run: EvolutionRun, output_path: str = "data/prediction_accuracy.png") -> str:
    """Plot raw calibration, adjusted calibration, and task accuracy over generations."""
    gens = [s.generation for s in run.generation_stats]
    raw_cal = [s.avg_raw_calibration for s in run.generation_stats]
    adj_cal = [s.avg_prediction_accuracy for s in run.generation_stats]
    task_acc = [s.avg_task_accuracy for s in run.generation_stats]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(gens, raw_cal, "D--", color="#1abc9c", linewidth=2, label="Raw LLM Calibration")
    ax.plot(gens, adj_cal, "o-", color="#9b59b6", linewidth=2, label="Evolved Calibration (with bias)")
    ax.plot(gens, task_acc, "s-", color="#f39c12", linewidth=2, label="Task Accuracy")
    # shade the gap between raw and evolved calibration
    ax.fill_between(gens, raw_cal, adj_cal, alpha=0.15, color="#9b59b6", label="Evolution gain")
    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Calibration & Accuracy Over Generations", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_trait_distribution(run: EvolutionRun, output_path: str = "data/trait_distribution.png") -> str:
    """Plot stacked area chart of reasoning style distribution over generations."""
    # group genomes by generation
    gen_genomes: dict[int, list[dict]] = {}
    for g in run.all_genomes:
        gen = g["generation"]
        gen_genomes.setdefault(gen, []).append(g)

    max_gen = max(gen_genomes.keys()) if gen_genomes else 0
    styles = list(COLORS.keys())
    gens = list(range(max_gen + 1))

    # count proportion of each style per generation
    proportions = {s: [] for s in styles}
    for gen in gens:
        genomes = gen_genomes.get(gen, [])
        total = len(genomes) if genomes else 1
        counts = Counter(g["reasoning_style"] for g in genomes)
        for s in styles:
            proportions[s].append(counts.get(s, 0) / total)

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(gens))
    for style in styles:
        values = np.array(proportions[style])
        ax.bar(gens, values, bottom=bottom, color=COLORS.get(style, "#999"),
               label=style, width=0.8)
        bottom += values

    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Proportion", fontsize=12)
    ax.set_title("Reasoning Style Distribution Over Generations", fontsize=14, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis="y")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_phylogenetic_tree(run: EvolutionRun, output_path: str = "data/phylogenetic_tree.png") -> str:
    """Build and plot a phylogenetic tree of agent lineage."""
    G = nx.DiGraph()

    # build genome lookup
    genome_lookup: dict[str, dict] = {}
    for g in run.all_genomes:
        genome_lookup[g["genome_id"]] = g
        G.add_node(g["genome_id"], generation=g["generation"], style=g["reasoning_style"])

    # add edges from parent to child
    for g in run.all_genomes:
        for pid in g.get("parent_ids", []):
            if pid in genome_lookup:
                G.add_edge(pid, g["genome_id"])

    if not G.nodes:
        # empty graph, create placeholder
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.text(0.5, 0.5, "No lineage data", ha="center", va="center", fontsize=16)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # position nodes by generation (x) and spread within generation (y)
    pos = {}
    gen_nodes: dict[int, list[str]] = {}
    for node, data in G.nodes(data=True):
        gen = data.get("generation", 0)
        gen_nodes.setdefault(gen, []).append(node)

    for gen, nodes in gen_nodes.items():
        for i, node in enumerate(sorted(nodes)):
            spread = len(nodes)
            pos[node] = (gen, (i - spread / 2) * 1.5)

    fig, ax = plt.subplots(figsize=(16, 10))

    # draw edges
    for u, v in G.edges():
        if u in pos and v in pos:
            ax.annotate(
                "",
                xy=pos[v], xytext=pos[u],
                arrowprops=dict(arrowstyle="-|>", color="#ccc", lw=0.8),
            )

    # draw nodes colored by reasoning style
    for node, data in G.nodes(data=True):
        if node in pos:
            style = data.get("style", "unknown")
            color = COLORS.get(style, "#999")
            ax.scatter(*pos[node], c=color, s=80, zorder=5, edgecolors="white", linewidth=0.5)

    # legend
    patches = [mpatches.Patch(color=c, label=s) for s, c in COLORS.items()]
    ax.legend(handles=patches, loc="upper left", fontsize=9)

    ax.set_xlabel("Generation", fontsize=12)
    ax.set_title("Agent Phylogenetic Tree", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.2)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_confidence_evolution(run: EvolutionRun, output_path: str = "data/confidence_evolution.png") -> str:
    """Plot how average confidence bias evolves over generations."""
    gen_biases: dict[int, list[float]] = {}
    for g in run.all_genomes:
        gen = g["generation"]
        gen_biases.setdefault(gen, []).append(g["confidence_bias"])

    gens = sorted(gen_biases.keys())
    avg_bias = [np.mean(gen_biases[g]) for g in gens]
    std_bias = [np.std(gen_biases[g]) for g in gens]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(gens, avg_bias, "o-", color="#e74c3c", linewidth=2, label="Avg Confidence Bias")
    ax.fill_between(
        gens,
        [a - s for a, s in zip(avg_bias, std_bias)],
        [a + s for a, s in zip(avg_bias, std_bias)],
        alpha=0.2, color="#e74c3c",
    )
    ax.axhline(0, color="#333", linestyle="--", alpha=0.5)
    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Confidence Bias", fontsize=12)
    ax.set_title("Confidence Bias Evolution (negative = underconfident, positive = overconfident)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_all_plots(run: EvolutionRun, output_dir: str = "data") -> list[str]:
    """Generate all visualization plots and return file paths."""
    paths = [
        plot_fitness_curves(run, f"{output_dir}/fitness_curves.png"),
        plot_prediction_accuracy(run, f"{output_dir}/prediction_accuracy.png"),
        plot_trait_distribution(run, f"{output_dir}/trait_distribution.png"),
        plot_phylogenetic_tree(run, f"{output_dir}/phylogenetic_tree.png"),
        plot_confidence_evolution(run, f"{output_dir}/confidence_evolution.png"),
    ]
    return paths


def generate_summary(run: EvolutionRun) -> str:
    """Generate a text summary of the evolutionary run."""
    if not run.generation_stats:
        return "No data."

    first = run.generation_stats[0]
    last = run.generation_stats[-1]

    # find dominant traits in final generation
    final_genomes = [g for g in run.all_genomes if g["generation"] == last.generation]
    style_counts = Counter(g["reasoning_style"] for g in final_genomes)
    memory_counts = Counter(g["memory_weighting"] for g in final_genomes)

    # extinct styles
    initial_styles = set(g["reasoning_style"] for g in run.all_genomes if g["generation"] == 0)
    final_styles = set(g["reasoning_style"] for g in final_genomes)
    extinct = initial_styles - final_styles

    lines = [
        "# Evolution Summary",
        "",
        f"**Generations:** {last.generation + 1}",
        f"**Population size:** {last.population_size}",
        "",
        "## Fitness Progression",
        f"- Generation 0 avg fitness: {first.avg_fitness:.3f}",
        f"- Final avg fitness: {last.avg_fitness:.3f}",
        f"- Improvement: {last.avg_fitness - first.avg_fitness:+.3f}",
        f"- Best individual fitness: {last.best_fitness:.3f}",
        "",
        "## Prediction Calibration",
        f"- Raw LLM calibration: {first.avg_raw_calibration:.1%} -> {last.avg_raw_calibration:.1%}",
        f"- Evolved calibration (with bias): {first.avg_prediction_accuracy:.1%} -> {last.avg_prediction_accuracy:.1%}",
        "",
        "## Task Accuracy",
        f"- Generation 0: {first.avg_task_accuracy:.1%}",
        f"- Final: {last.avg_task_accuracy:.1%}",
        "",
        "## Dominant Strategies (Final Generation)",
        f"- Reasoning: {style_counts.most_common(1)[0][0] if style_counts else 'N/A'} ({style_counts.most_common(1)[0][1]}/{len(final_genomes)} agents)" if style_counts else "- N/A",
        f"- Memory: {memory_counts.most_common(1)[0][0] if memory_counts else 'N/A'}",
        "",
        "## Extinct Strategies",
    ]
    if extinct:
        lines.extend(f"- {s}" for s in extinct)
    else:
        lines.append("- None (all strategies survived)")
    return "\n".join(lines)
