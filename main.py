#!/usr/bin/env python3
"""
Main entry point for StrategyConnect Take-Home: Diligence Agent That Improves From Feedback.
Executes the full pipeline in one command:
1. Scorer calibration against human expert judgments
2. Multi-seed experiments across feedback rounds (with 20% noise)
3. Unconstrained naive agent gaming experiment & mitigation
4. Generation of all publication-quality plots and metrics
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ["MPLCONFIGDIR"] = "/tmp"

from src.evaluation.run_experiments import run_experiment_suite
from src.evaluation.run_gaming import simulate_gaming_loophole

def main():
    print("=" * 65)
    print("STRATEGYCONNECT DILIGENCE AGENT - END-TO-END REPRODUCTION RUN")
    print("=" * 65)

    print("\n[Phase 1] Running Multi-Seed Evaluations & Scorer Calibration...")
    run_experiment_suite(seeds=[42, 123, 456, 789, 999], rounds=3, noise_rate=0.20)

    print("\n[Phase 2] Running Gaming Loophole & Exploitation Analysis...")
    simulate_gaming_loophole()

    print("\n" + "=" * 65)
    print("ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print("Artifacts generated:")
    print(" - Plots: results/plots/quality_vs_feedback_rounds.png")
    print(" - Plots: results/plots/gaming_failure_comparison.png")
    print(" - Plots: results/plots/loophole_gaming_demonstration.png")
    print(" - Metrics: results/metrics.json")
    print(" - Two-Page Write-Up: WRITEUP.md")
    print(" - Interactive Demo: python demo.py")
    print("=" * 65)

if __name__ == "__main__":
    main()

