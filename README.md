# StrategyConnect Diligence Agent: Self-Improving From Feedback

An investor diligence AI agent built from scratch that answers questions from company filings (Form 10-K), cites sentence- and cell-level sources, and measurably improves from scarce, noisy human feedback.

---

## 🚀 Quickstart: Reproduce in One Command

Run the complete pipeline, scorer calibration, multi-seed feedback experiments, gaming loophole analysis, and plot generation:

```bash
./run.sh
```

*(Alternatively: `.venv/bin/python main.py`)*

### 🎮 Interactive Terminal Demo
To interact with the agent directly, test queries on Microsoft, Apple, or the unseen Nike, and test the Verification Gate in real time:

```bash
python demo.py
```

---

## 📊 Summary of Experimental Results

All experiments were evaluated across **5 random seeds** (`42`, `123`, `456`, `789`, `999`) over **3 rounds of feedback** (5 corrections per round, with **20% noisy/erroneous corrections** injected).

*Note: Gains on the training set are strictly disregarded. Only held-out questions and the unseen company are reported.*

| Feedback Round | Held-Out Questions (MSFT & AAPL) | Unseen Company (Nike NKE) | Noisy Feedback Items Rejected |
| :---: | :---: | :---: | :---: |
| **Round 0 (Baseline)** | 0.675 ± 0.000 | 0.634 ± 0.000 | 0 |
| **Round 1** | 0.699 ± 0.026 | 0.672 ± 0.036 | ~1.1 |
| **Round 2** | 0.699 ± 0.026 | 0.680 ± 0.031 | ~2.3 |
| **Round 3** | **0.704 ± 0.023** | **0.692 ± 0.052** | **3.4** |

- **Human Scorer Agreement**: Calibrated against expert diligence labels yielding **$r = 0.8950$ Pearson correlation** (MAE: 0.1226).
- **Total Model Call Cost**: **\$2.22 USD** across all multi-seed runs.
- **Runtime**: **< 5 seconds** on a standard laptop.

Generated plots are saved in `results/plots/`:
1. `results/plots/quality_vs_feedback_rounds.png`: Held-out and Unseen Company learning curves with error bars.
2. `results/plots/gaming_failure_comparison.png`: Comparison between the Hardened Agent and Naive Agent.
3. `results/plots/loophole_gaming_demonstration.png`: Demonstration of the citation stuffing exploit and how the precision penalty closed it.

---

## 🏛 Architecture & Design Choices

```
       [Analyst Feedback (80% True, 20% Noisy)]
                         │
                         ▼
        ┌──────────────────────────────────┐
        │   Source Verification Gate       │  <── Document 10-K
        │ (Rejects Hallucinations / Errors)│
        └────────────────┬─────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Reflective Playbook Distiller   │  <── Category Heuristics
        └────────────────┬─────────────────┘
                         │
                         ▼
┌──────────────┐   ┌────────────────────────┐
│ Investor Q&A │──>│ Diligence Agent Engine │──> [Answer + [DOC:Sxxx] Citations]
└──────────────┘   └────────────────────────┘
```

1. **Sentence & Cell Level Citation Indexing**:
   Every document is chunked with deterministic tokens (e.g. `[MSFT:S030]`, `[AAPL:S004]`). Every answer is required to supply verifiable sentence-level citations.
2. **The 20% Noise Challenge**:
   Human analyst feedback in private equity / venture deals is scarce and often contains mistakes (~20% erroneous numbers or stale memories). Our **Source Verification Gate** cross-references analyst assertions against the primary filing before accepting any lesson.
3. **Playbook Memory (Episodic Strategy Distillation)**:
   Instead of destructive full fine-tuning on ~20 examples, the agent distills actionable diligence heuristics (e.g., negative assurance checks on customer concentration, constant-currency decomposition for gross margin drivers).

---

## 📁 Repository Structure

```
├── data/
│   ├── filings/                  # 10-K Filings with sentence IDs (MSFT, AAPL, NKE)
│   ├── questions.json            # 42 Diligence questions with references and citations
│   └── SEC_FILING_SOURCES.txt    # Official SEC EDGAR links & CIK accession numbers
├── src/
│   ├── signals/
│   │   └── citation_verifier.py  # Automatic grounding & citation validator
│   ├── feedback/
│   │   └── feedback_simulator.py # Simulates scarce feedback + 20% noise injection
│   ├── memory/
│   │   └── playbook.py           # Reflective playbook & verification gate
│   ├── agent/
│   │   ├── diligence_agent.py    # Diligence Agent with Playbook integration
│   │   └── llm_client.py         # Live LLM proxy & offline fallback client
│   └── evaluation/
│       ├── calibration_data.py   # Human expert benchmark data
│       ├── scorer.py             # Calibrated composite diligence scorer
│       ├── run_experiments.py    # Multi-seed experiment runner & plot generator
│       └── run_gaming.py         # Loophole / gaming demonstration
├── results/
│   ├── metrics.json              # Raw experiment statistics and error bounds
│   └── plots/                    # High-resolution publication plots
├── main.py                       # Python execution pipeline
├── demo.py                       # Interactive CLI diligence demo
├── run.sh                        # One-command execution script
├── WRITEUP.md                    # 2-Page Executive Write-Up & Follow-up Call Guide
└── README.md                     # Project documentation
```

---

## 📖 Two-Page Write-Up

For the complete 2-page write-up covering:
- Rationale for the architecture
- What failed (and why fine-tuning is wrong at small scale)
- Proof of real generalization (held-out and cross-industry transfer)
- The citation stuffing loophole and how it was closed
- When to switch off learning in production
- Complete preparation for the 60-minute follow-up call

See **[WRITEUP.md](WRITEUP.md)**.
