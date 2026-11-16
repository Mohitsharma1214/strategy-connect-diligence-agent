"""
End-to-end multi-seed experiment pipeline:
1. Loads filings and question suite.
2. Calibrates DiligenceScorer against human judgments (Nike strictly excluded).
3. Evaluates agents across multiple seeds and feedback rounds (0 to 3).
4. Strictly isolates Nike (unseen company) from the learning loop, training filings, and training verifier.
5. Tracks held-out performance, unseen company (NKE) performance, and noise rejection.
6. Runs the gaming/failure mode ablation (Naive Learner without verification gate).
7. Generates publication-ready plots and summary metrics.
"""

import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ["MPLCONFIGDIR"] = "/tmp"

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.signals.citation_verifier import CitationVerifier
from src.evaluation.scorer import DiligenceScorer
from src.evaluation.calibration_data import HUMAN_CALIBRATION_SAMPLES
from src.feedback.feedback_simulator import FeedbackSimulator
from src.memory.playbook import DiligencePlaybook
from src.agent.diligence_agent import DiligenceAgent

DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def load_all_filings():
    filings = {}
    filings_dir = os.path.join(DATA_DIR, "filings")
    for fname, comp in [("msft_10k_2023.txt", "MSFT"), ("aapl_10k_2023.txt", "AAPL"), ("nke_10k_2023.txt", "NKE")]:
        fpath = os.path.join(filings_dir, fname)
        with open(fpath, "r") as f:
            filings[comp] = f.read()
    return filings

def load_questions():
    with open(os.path.join(DATA_DIR, "questions.json"), "r") as f:
        return json.load(f)

def run_evaluation_split(agent: DiligenceAgent, scorer: DiligenceScorer, questions: list, filing_dict: dict):
    # Temporarily bind evaluation filings to agent to ensure clean out-of-distribution evaluation
    old_filings = agent.filings
    agent.filings = filing_dict
    scores = []
    for q in questions:
        res = agent.answer_question(q)
        eval_res = scorer.score_answer(res["answer"], q)
        scores.append(eval_res["composite_score"])
    agent.filings = old_filings
    return float(np.mean(scores))

def run_experiment_suite(seeds=[42, 123, 456, 789, 999], rounds=3, noise_rate=0.20):
    all_filings = load_all_filings()
    questions = load_questions()
    
    # 1. Strictly separate training filings from unseen company filing
    train_filings = {"MSFT": all_filings["MSFT"], "AAPL": all_filings["AAPL"]}
    unseen_filings = {"NKE": all_filings["NKE"]}

    train_qs = [q for q in questions if q["split"] == "train"]
    held_out_qs = [q for q in questions if q["split"] == "held_out"]
    unseen_qs = [q for q in questions if q["split"] == "unseen"]

    # Training verifier and scorer (Nike is 100% absent)
    train_verifier = CitationVerifier(train_filings)
    train_scorer = DiligenceScorer(train_verifier)

    # Out-of-distribution evaluation verifier and scorer (used only during unseen evaluation)
    unseen_verifier = CitationVerifier(unseen_filings)
    unseen_scorer = DiligenceScorer(unseen_verifier)

    print("==================================================")
    print("STEP 1: Calibrating Scorer with Human Judgments...")
    print("==================================================")
    calibration_res = train_scorer.calibrate_with_human_judgments(HUMAN_CALIBRATION_SAMPLES)
    print(f"Human-Scorer Pearson Correlation: {calibration_res['pearson_correlation']:.4f}")
    print(f"Mean Absolute Error (MAE):       {calibration_res['mean_absolute_error']:.4f}")
    print(f"Calibration Samples (Nike strictly excluded): {calibration_res['n_samples']}")
    print("Calibration successful!\n")

    hardened_held_out = {r: [] for r in range(rounds + 1)}
    hardened_unseen = {r: [] for r in range(rounds + 1)}
    hardened_rejected_noise = []

    naive_held_out = {r: [] for r in range(rounds + 1)}
    naive_unseen = {r: [] for r in range(rounds + 1)}

    total_actual_cost = 0.0
    total_simulated_cost = 0.0

    print("==================================================")
    print(f"STEP 2: Running Multi-Seed Experiments ({len(seeds)} seeds, {rounds} rounds, {noise_rate*100:.0f}% noise)...")
    print("==================================================")

    for i, seed in enumerate(seeds, 1):
        print(f"  [Progress {i}/{len(seeds)}] Evaluating Seed {seed} across Rounds 0 to {rounds}...")
        
        # A. Hardened Agent Run (With Verification Gate & Dynamic Strategy Extraction)
        # Note: Initialized solely with train_filings and train_verifier
        playbook_hardened = DiligencePlaybook(train_verifier, naive_mode=False)
        agent_hardened = DiligenceAgent(train_filings, train_verifier, playbook=playbook_hardened, naive_mode=False)
        sim_hardened = FeedbackSimulator(noise_rate=noise_rate, seed=seed)

        # Baseline evaluation (Round 0)
        r0_ho = run_evaluation_split(agent_hardened, train_scorer, held_out_qs, train_filings)
        r0_un = run_evaluation_split(agent_hardened, unseen_scorer, unseen_qs, unseen_filings)
        hardened_held_out[0].append(r0_ho)
        hardened_unseen[0].append(r0_un)

        # Feedback Rounds 1 to 3
        for r in range(1, rounds + 1):
            preds = {q["id"]: agent_hardened.answer_question(q)["answer"] for q in train_qs}
            feedback_batch = sim_hardened.generate_feedback_batch(train_qs, preds, batch_size=5)
            
            for fb in feedback_batch:
                q_obj = fb["question"]
                playbook_hardened.learn_from_feedback(q_obj, fb["prediction"], fb)

            score_ho = run_evaluation_split(agent_hardened, train_scorer, held_out_qs, train_filings)
            score_un = run_evaluation_split(agent_hardened, unseen_scorer, unseen_qs, unseen_filings)
            hardened_held_out[r].append(score_ho)
            hardened_unseen[r].append(score_un)

        hardened_rejected_noise.append(playbook_hardened.rejected_feedback_count)
        total_actual_cost += agent_hardened.actual_api_cost_usd
        total_simulated_cost += agent_hardened.simulated_production_cost_usd

        # B. Naive Agent Run (No Gate / Absorbs Contaminated Feedback)
        playbook_naive = DiligencePlaybook(train_verifier, naive_mode=True)
        agent_naive = DiligenceAgent(train_filings, train_verifier, playbook=playbook_naive, naive_mode=True)
        sim_naive = FeedbackSimulator(noise_rate=noise_rate, seed=seed)

        r0_ho_n = run_evaluation_split(agent_naive, train_scorer, held_out_qs, train_filings)
        r0_un_n = run_evaluation_split(agent_naive, unseen_scorer, unseen_qs, unseen_filings)
        naive_held_out[0].append(r0_ho_n)
        naive_unseen[0].append(r0_un_n)

        for r in range(1, rounds + 1):
            preds = {q["id"]: agent_naive.answer_question(q)["answer"] for q in train_qs}
            feedback_batch = sim_naive.generate_feedback_batch(train_qs, preds, batch_size=5)
            for fb in feedback_batch:
                q_obj = fb["question"]
                playbook_naive.learn_from_feedback(q_obj, fb["prediction"], fb)

            score_ho_n = run_evaluation_split(agent_naive, train_scorer, held_out_qs, train_filings)
            score_un_n = run_evaluation_split(agent_naive, unseen_scorer, unseen_qs, unseen_filings)
            naive_held_out[r].append(score_ho_n)
            naive_unseen[r].append(score_un_n)

    print("\nExperiment runs complete!")
    print(f"Actual model call expenditure: ${total_actual_cost:.4f} USD (Offline deterministic reproduction: $0.00)")
    print(f"Simulated production API cost benchmark: ${total_simulated_cost:.4f} USD ($15.00/10k queries)")
    print(f"Average noisy feedback items rejected per run by Hardened Agent: {np.mean(hardened_rejected_noise):.1f}")

    rounds_axis = list(range(rounds + 1))
    h_ho_mean = [np.mean(hardened_held_out[r]) for r in rounds_axis]
    h_ho_std = [np.std(hardened_held_out[r]) for r in rounds_axis]

    h_un_mean = [np.mean(hardened_unseen[r]) for r in rounds_axis]
    h_un_std = [np.std(hardened_unseen[r]) for r in rounds_axis]

    n_ho_mean = [np.mean(naive_held_out[r]) for r in rounds_axis]
    n_ho_std = [np.std(naive_held_out[r]) for r in rounds_axis]

    n_un_mean = [np.mean(naive_unseen[r]) for r in rounds_axis]
    n_un_std = [np.std(naive_unseen[r]) for r in rounds_axis]

    print("\n--- RESULTS SUMMARY (Mean ± Std) ---")
    print("Round | Hardened Held-out | Hardened Unseen (NKE) | Naive Held-out | Naive Unseen")
    for r in rounds_axis:
        print(f"  {r}   |   {h_ho_mean[r]:.3f} ± {h_ho_std[r]:.3f}   |     {h_un_mean[r]:.3f} ± {h_un_std[r]:.3f}    |  {n_ho_mean[r]:.3f} ± {n_ho_std[r]:.3f} | {n_un_mean[r]:.3f} ± {n_un_std[r]:.3f}")

    print("\nGenerating publication plots...")
    
    # Plot 1: Held-out & Unseen quality vs rounds (Hardened Agent)
    plt.figure(figsize=(8, 5))
    plt.errorbar(rounds_axis, h_ho_mean, yerr=h_ho_std, fmt='-o', capsize=5, label='Held-Out Questions (MSFT/AAPL)', color='#1f77b4', linewidth=2)
    plt.errorbar(rounds_axis, h_un_mean, yerr=h_un_std, fmt='-s', capsize=5, label='Unseen Company (Nike NKE)', color='#2ca02c', linewidth=2)
    plt.title("Diligence Agent Quality vs Rounds of Feedback (20% Noise)", fontsize=13, fontweight='bold')
    plt.xlabel("Rounds of Feedback", fontsize=11)
    plt.ylabel("Composite Quality Score (0 - 1.0)", fontsize=11)
    plt.xticks(rounds_axis)
    plt.ylim(0.40, 1.00)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=10, loc='lower right')
    plt.tight_layout()
    plot1_path = os.path.join(PLOTS_DIR, "quality_vs_feedback_rounds.png")
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f"Saved: {plot1_path}")

    # Plot 2: Gaming / Failure Comparison (Hardened vs Naive)
    plt.figure(figsize=(8, 5))
    plt.plot(rounds_axis, h_ho_mean, '-o', label='Hardened Agent (With Gate): Held-Out', color='#1f77b4', linewidth=2.5)
    plt.plot(rounds_axis, h_un_mean, '-s', label='Hardened Agent (With Gate): Unseen', color='#2ca02c', linewidth=2.5)
    plt.plot(rounds_axis, n_ho_mean, '--o', label='Naive Agent (No Gate / Poisoned): Held-Out', color='#d62728', linewidth=2)
    plt.plot(rounds_axis, n_un_mean, '--s', label='Naive Agent (No Gate / Poisoned): Unseen', color='#ff7f0e', linewidth=2)
    plt.title("Noise Vulnerability: Hardened vs Naive Agent", fontsize=13, fontweight='bold')
    plt.xlabel("Rounds of Feedback", fontsize=11)
    plt.ylabel("Composite Quality Score", fontsize=11)
    plt.xticks(rounds_axis)
    plt.ylim(0.35, 1.00)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=9, loc='lower left')
    plt.tight_layout()
    plot2_path = os.path.join(PLOTS_DIR, "gaming_failure_comparison.png")
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f"Saved: {plot2_path}")

    # Save metrics JSON
    metrics = {
        "calibration": calibration_res,
        "actual_api_expenditure_usd": round(total_actual_cost, 4),
        "simulated_production_cost_usd": round(total_simulated_cost, 4),
        "hardened": {
            "held_out_mean": [round(x, 4) for x in h_ho_mean],
            "held_out_std": [round(x, 4) for x in h_ho_std],
            "unseen_mean": [round(x, 4) for x in h_un_mean],
            "unseen_std": [round(x, 4) for x in h_un_std]
        },
        "naive": {
            "held_out_mean": [round(x, 4) for x in n_ho_mean],
            "held_out_std": [round(x, 4) for x in n_ho_std],
            "unseen_mean": [round(x, 4) for x in n_un_mean],
            "unseen_std": [round(x, 4) for x in n_un_std]
        }
    }
    metrics_path = os.path.join(RESULTS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics: {metrics_path}")

    return metrics

if __name__ == "__main__":
    run_experiment_suite()
