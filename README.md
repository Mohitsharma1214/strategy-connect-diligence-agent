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
To interact with the agent directly, ask arbitrary custom diligence questions on Microsoft, Apple, or the unseen Nike, and test the Verification Gate in real time:

```bash
.venv/bin/python demo.py
```

---

## 📊 Summary of Verified Experimental Results

All experiments were evaluated across **5 random seeds** (`42`, `123`, `456`, `789`, `999`) over **3 rounds of feedback** (5 corrections per round, with **20% noisy/erroneous corrections** injected).

*Note: Gains on the training set are strictly disregarded. Only held-out questions and the unseen company are reported. Nike data is strictly isolated until evaluation.*

| Feedback Round | Hardened Held-Out (MSFT/AAPL) | Hardened Unseen (Nike NKE) | Naive Held-Out (No Gate) | Naive Unseen (No Gate) |
| :---: | :---: | :---: | :---: | :---: |
| **Round 0 (Baseline)** | 0.843 ± 0.000 | 0.849 ± 0.000 | 0.843 ± 0.000 | 0.849 ± 0.000 |
| **Round 1** | 0.847 ± 0.007 | 0.874 ± 0.026 | 0.803 ± 0.044 | 0.814 ± 0.046 |
| **Round 2** | 0.854 ± 0.009 | 0.879 ± 0.023 | 0.806 ± 0.047 | 0.791 ± 0.089 |
| **Round 3** | **0.854 ± 0.009** | **0.894 ± 0.026** | **0.785 ± 0.053** | **0.757 ± 0.122** |

- **Feedback Verification Performance**: **5.0** total feedback items rejected per run on average; **100.0% Noise Detection Recall** on injected corruptions (3.8 of 3.8 injected noisy corrections caught).
- **Preliminary Scorer Calibration**: Benchmarked against a pilot dataset of expert human diligence ratings ($N=12$, Nike strictly excluded) yielding **$r = 0.9272$ Pearson correlation** and **MAE = 0.1126**.
- **Model Call Expenditure**: **\$0.0000 USD** actual expenditure (offline deterministic execution mode); **\$1.1100 USD** simulated production equivalent (\$15.00 / 10,000 queries benchmark).
- **Runtime**: **< 5 seconds** on a standard laptop.

Generated plots are saved in `results/plots/`:
1. `results/plots/quality_vs_feedback_rounds.png`: Held-out and Unseen Company learning curves with error bars across 5 seeds.
2. `results/plots/gaming_failure_comparison.png`: Comparison between the Hardened Agent and Naive Agent under 20% feedback noise.
3. `results/plots/loophole_gaming_demonstration.png`: Demonstration of the citation stuffing exploit and how semantic claim-support penalties closed it.

---

## 🏛 Architecture & Design Choices

```
       [Analyst Feedback (80% True, 20% Noisy)]
                         │
                         ▼
        ┌──────────────────────────────────┐
        │   Source Verification Gate       │  <── Document 10-K (Company-Specific & Local Claim Checked)
        │ (Rejects Hallucinations / Errors)│
        └────────────────┬─────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │ Error Analysis & Lesson Extractor│  <── Dynamic Bridge Terms & Multi-Hop Query Expansions
        └────────────────┬─────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │     Playbook Strategy Memory     │  <── Reusable Intent & Retrieval Heuristics
        └────────────────┬─────────────────┘
                         │
                         ▼
┌──────────────┐   ┌────────────────────────┐
│ Investor Q&A │──>│ Diligence Agent Engine │──> [Two-Stage Retrieval + Direct Compositional Answer]
└──────────────┘   └────────────────────────┘
```

1. **Sentence & Cell Level Citation Indexing**:
   Every document is chunked with deterministic tokens (e.g. `[MSFT:S030]`, `[AAPL:S004]`, `[NKE:S005]`). Every answer is required to supply verifiable sentence-level citations.
2. **The 20% Noise Challenge**:
   Human analyst feedback in private equity / venture deals is scarce and often contains mistakes (~20% erroneous numbers or stale memories). Our **Source Verification Gate** enforces company-specific citation prefixes, validates asserted metrics directly against cited sentences (preventing global-document leakage), and checks for negative assurance contradictions.
3. **Hybrid Domain-Guided & Evidence-Derived Learning**:
   Instead of destructive full fine-tuning on scarce data, the agent performs automated failure analysis on verified corrections. It combines standard financial omission categories (e.g., negative assurance, accounting revisions) with dynamically extracted domain bridge terms (e.g., "depreciation", "useful life", "freight", "markdowns", "wholesale") from cited sentences. These terms parameterize a two-stage retrieval engine for future questions on both held-out and unseen companies.

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
│   │   └── feedback_simulator.py # Simulates scarce feedback + 20% noise injection (MSFT & AAPL only)
│   ├── memory/
│   │   └── playbook.py           # Verification gate, error analysis & dynamic strategy memory
│   ├── agent/
│   │   ├── diligence_agent.py    # Two-stage retrieval agent with dynamic playbook expansions
│   │   └── llm_client.py         # Live LLM proxy & offline fallback client
│   └── evaluation/
│       ├── calibration_data.py   # Human expert benchmark data (Nike strictly isolated)
│       ├── scorer.py             # Calibrated composite scorer with claim-to-citation check
│       ├── run_experiments.py    # 5-seed, multi-round experiment pipeline
│       └── run_gaming.py         # Gaming/loophole exploit demonstration
├── results/
│   ├── plots/                    # High-resolution publication plots
│   └── metrics.json              # Exact numerical output from multi-seed runs
├── demo.py                       # Interactive terminal demo for arbitrary questions
├── main.py                       # One-command Python runner
├── run.sh                        # One-command shell runner
├── WRITEUP.md                    # Two-page technical write-up
└── README.md                     # Documentation and reproduction guide
```

---

## 📋 Evaluation Integrity Checklist

- [x] **Zero Nike Leakage**: Nike 10-K text and calibration examples are completely excluded from the training environment, training verifier, and scorer calibration. Loaded exclusively during unseen out-of-distribution evaluation.
- [x] **Dynamic Strategy Extraction**: Zero hardcoded answer generation branches or category templates. Strategies extract informative bridge terms from verified cited evidence and parameterize the retrieval engine.
- [x] **Local Sentence Grounding**: Numbers in analyst feedback are validated strictly against the cited sentence, preventing spurious acceptance of numbers found elsewhere in the 100-page filing.
- [x] **Claim-to-Citation Support Scorer**: Scorer inspects each cited clause to verify that numbers and entities are entailed by the cited source sentence.
- [x] **Exact Cost Accounting**: Clear separation between offline reproduction ($0.00) and simulated enterprise deployment benchmarks ($1.11, or $15/10k queries).
