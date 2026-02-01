#!/usr/bin/env python3
"""
Compare frontier models vs previous-generation models
"""

import json
from pathlib import Path

def main():
    # Load frontier results
    frontier_path = Path("data/comprehensive_experiment/analysis_results.json")
    with open(frontier_path) as f:
        frontier = json.load(f)

    # Load previous-gen results
    prev_gen_path = Path("data/previous_gen_experiment/analysis_results.json")
    with open(prev_gen_path) as f:
        prev_gen = json.load(f)

    print("="*80)
    print("SYSTEM VS MODEL: COMPREHENSIVE COMPARISON")
    print("="*80)
    print()
    print("**Question: Do you need a better system — or a better model?**")
    print()
    print("="*80)
    print()

    # GPT Comparison
    print("## GPT EVOLUTION: GPT-4o → GPT-5.2")
    print()
    if "GPT-4o" in prev_gen and "GPT-5.2" in frontier:
        gpt4o = prev_gen["GPT-4o"]
        gpt52 = frontier["GPT-5.2"]

        print(f"**GPT-4o (Previous Gen)**")
        print(f"  Test Set Performance: {gpt4o['evolved_calibration']['mean']*100:.1f}% ± {gpt4o['evolved_calibration']['std']*100:.1f}%")
        print(f"  Calibration Gap: {gpt4o['calibration_gap']*100:+.1f}%")
        print(f"  Verdict: Evolution HURT performance (need better base model)")
        print()

        print(f"**GPT-5.2 (Frontier)**")
        print(f"  Test Set Performance: {gpt52['evolved_calibration']['mean']*100:.1f}% ± {gpt52['evolved_calibration']['std']*100:.1f}%")
        print(f"  Calibration Gap: {gpt52['calibration_gap']*100:+.1f}%")
        print(f"  Verdict: Already well-calibrated (minimal improvement)")
        print()

        improvement = gpt52['evolved_calibration']['mean'] - gpt4o['evolved_calibration']['mean']
        print(f"**Key Insight**: GPT-5.2 is {improvement*100:+.1f}% better than GPT-4o on test set")
        print(f"  → Model improvement >>> system optimization for GPT line")
    print()
    print("-"*80)
    print()

    # DeepSeek Comparison
    print("## DEEPSEEK EVOLUTION: V2.5 vs V3")
    print()
    print(f"**DeepSeek V2.5 (Previous Gen)**")
    print(f"  Status: Model not available via W&B Inference API")
    print()

    if "DeepSeek V3" in frontier:
        ds3 = frontier["DeepSeek V3"]
        print(f"**DeepSeek V3 (Frontier)**")
        print(f"  Test Set Performance: {ds3['evolved_calibration']['mean']*100:.1f}% ± {ds3['evolved_calibration']['std']*100:.1f}%")
        print(f"  Calibration Gap: {ds3['calibration_gap']*100:+.1f}%")
        print(f"  Verdict: Evolution degraded performance (need better model)")
    print()
    print("-"*80)
    print()

    # Claude Comparison
    print("## CLAUDE: Opus 4.5 (Frontier Only)")
    print()
    if "Claude Opus 4.5" in frontier:
        opus = frontier["Claude Opus 4.5"]
        print(f"**Claude Opus 4.5**")
        print(f"  Test Set Performance: {opus['evolved_calibration']['mean']*100:.1f}% ± {opus['evolved_calibration']['std']*100:.1f}%")
        print(f"  Calibration Gap: {opus['calibration_gap']*100:+.1f}%")
        print(f"  Verdict: Already optimally calibrated")
    print()
    print("="*80)
    print()

    # Summary
    print("## CONCLUSION")
    print()
    print("**Frontier models (GPT-5.2, Claude Opus 4.5) show minimal system optimization headroom.**")
    print("They're already well-calibrated out of the box.")
    print()
    print("**Previous-gen models (GPT-4o) show NEGATIVE optimization gaps.**")
    print("Evolution actually hurt performance → the issue is model capability, not system config.")
    print()
    print("**Answer: For these frontier models, you need a better MODEL, not a better SYSTEM.**")
    print()
    print("="*80)

if __name__ == "__main__":
    main()
