# StrategyConnect Diligence Agent: Self-Improving From Feedback

An institutional investor diligence AI agent built for StrategyConnect that extracts grounded financial answers from real SEC EDGAR Form 10-K filings, cites exact sentence quotes and table cells, and continuously improves from scarce, noisy human analyst feedback.

---

## 🚀 Quickstart: Reproduce in One Command

### 1. Full Production Reproduction Pipeline
Runs the complete 4-round learning loop on Microsoft and Apple Form 10-Ks, evaluates held-out questions, benchmarks the automated judge against 30 hand-scored answers, generates publication plots, and outputs `results/metrics.json`:

```bash
chmod +x run.sh
./run.sh
```

### 2. Auditor CLI Execution Signature
The auditor can test the pipeline against any SEC Form 10-K HTML filing and questions file:

```bash
./run.sh --filing data/sc-diligence/filings/msft-20260630.htm --questions data/sc-diligence/questions.json --out answers_msft.jsonl
./run.sh --filing data/sc-diligence/filings/aapl-20260926.htm --questions data/sc-diligence/questions.json --out answers_aapl.jsonl
```

The output file strictly conforms to StrategyConnect's specification (`examples/answer.example.json` and `examples/answer_cell.example.json`) in line-delimited JSON (`.jsonl`).

### 3. Automated Judge Validation Against 30 Hand-Scored Answers
To inspect statistical agreement between the automated scorer and candidate-authored manual labels across Factual Accuracy, Numerical Accuracy, and Citation Grounding (note: manual labels were authored by the candidate; independent reviewer validation has not yet been completed):

```bash
python3 -m src.eval.scorer
```

---

## 📊 Summary of Production Results

All experiments run on **StrategyConnect’s official production dataset** (`sc-diligence`):
- **Real SEC Form 10-K Filings**: Microsoft FY2026 (8.58 MB HTML, 2,805 sentences, 2,609 table cells) and Apple FY2026 (1.65 MB HTML, 1,926 sentences, 1,587 table cells).
- **Official Question Benchmark**: 24 official questions (16 learn, 8 held-out).
- **Real Analyst Feedback**: 48 human analyst corrections across 4 rounds (12 items/round) from three distinct analyst profiles.

| Stage | Feedback Ingested | Accepted / Rejected | Learn Accuracy | Held-Out Accuracy | Citation Grounding |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Round 0 (Baseline)** | 0 | 0 / 0 | 18.8% | 12.5% | **100.0%** |
| **Round 1** | 12 (FB-001..012) | 8 / 4 | **50.0%** | 0.0% | **100.0%** |
| **Round 2** | 12 (FB-013..024) | 7 / 5 | **75.0%** | 0.0% | **100.0%** |
| **Round 3** | 12 (FB-025..036) | 5 (2 rev) / 5 | **93.8%** | 0.0% | **100.0%** |
| **Round 4** | 12 (FB-037..048) | 7 (2 rev) / 3 | **93.8%** | 0.0% | **100.0%** |

### Multi-Seed Sensitivity Profile
Across 3 random seeds (`[42, 137, 2026]`) testing stochastic feedback order permutations:
- **Learn Accuracy Growth**: Measurably improves from **18.8% $\to$ 93.8%** as verified corrections and retrieval strategies are assimilated.
- **Held-Out Citation Grounding**: **100.0% $\pm$ 0.0%** (invariant across all seeds and rounds).
- **Held-Out Strict Factual Accuracy**: Round 0 = **12.5% $\pm$ 0.0%** $\to$ Rounds 1–4 = **0.0% $\pm$ 0.0%** (the evaluation design keeps held-out questions and reference answers isolated from feedback processing; observed results are consistent with that separation, while demonstrating that localized feedback rules do not yet achieve generalized retrieval transfer to unseen line items).
- **Local Open-Weights Execution**: `llama3.2:3b` via Ollama executes the 4-round pipeline at \$0.00 cost.

### Analyst Reliability & Forensic Audit
The epistemic verification gate rejected **17 out of 48 corrupt items (35.4% noise rejection rate)** while quarantining 4 low-trust submissions for partner review (27 cleared directly into active playbooks + 4 quarantined):

| Analyst ID | Total Items | Cleared (Active) | Quarantined (Review) | Rejected (Noise) | Empirical Reliability | Primary Failure Modes |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`AN-01`** | 16 | 0 | 4 | 12 | **25.0%** | Prompt injection (`FB-028`), temporal swaps, $1,000\times$ scale error (`FB-027`), low overlap |
| **`AN-02`** | 16 | 15 | 0 | 1 | **93.8%** | Institutional grade; precision table citations. Only 1 rejection (`FB-003`: "all payable" vs $\$82.7\text{B}$) |
| **`AN-03`** | 16 | 12 | 0 | 4 | **75.0%** | Subtle accounting errors (receivables vs revenue, non-GAAP conflation, citing Japan for China) |
| **Total** | **48** | **27** | **4** | **17** | **64.6%** | **35.4% Noise Rejected (17 rejected; 4 quarantined for partner review)** |

### Automated Judge Alignment (30 Hand-Scored Benchmark)
Validated against 30 candidate-authored hand-scored answers in [`data/hand_scored_30.json`](data/hand_scored_30.json) (independent reviewer validation has not yet been completed):
- **Citation Grounding Agreement**: **100.0%** ($\kappa = 1.000$, Pearson $r = 1.000$)
- **Factual Accuracy Agreement**: **96.7%** ($\kappa = 0.933$, Pearson $r = 0.935$)
- **Numerical Accuracy Agreement**: **90.0%** ($\kappa = 0.794$, Pearson $r = 0.796$)
- **Overall All-Pass Agreement**: **96.7%** ($\kappa = 0.933$, Pearson $r = 0.935$)

---

## 🏛 Architecture & Codebase Map

```
strategy-connect-diligence-agent/
├── AUDIT_RESPONSE.md          # Point-by-point response addressing all 8 audit findings
├── WRITEUP.md                 # Revised two-page executive write-up (< 1,000 words)
├── README.md                  # Quickstart, reproduction instructions, and metrics summary
├── run.sh                     # Unified executable for reproduction and auditor CLI testing
├── main.py                    # Production pipeline, CLI driver, and experiment orchestrator
├── data/
│   ├── SCORING_RUBRIC.md      # Formal 3-dimensional diligence scoring rubric
│   ├── hand_scored_30.json    # 30 hand-scored answers with candidate-authored manual labels & rationale notes
│   └── sc-diligence/          # Official StrategyConnect dataset
│       ├── filings/           # Real 10-K HTML filings (msft-20260630.htm, aapl-20260926.htm)
│       ├── questions.json     # 24 official diligence questions (16 learn, 8 held-out)
│       └── feedback.jsonl     # 48 human analyst corrections across 4 rounds
├── src/
│   ├── parser/
│   │   └── edgar_parser.py    # SEC Form 10-K HTML and financial table parser
│   ├── agent/
│   │   ├── diligence_agent.py # Grounded diligence QA agent and reflective playbook memory
│   │   └── local_llm.py       # Open-weights local inference client (llama3.2:3b via Ollama)
│   ├── feedback/
│   │   └── analyst_gate.py    # 4-layer epistemic verification gate & Bayesian trust tracker
│   └── eval/
│       └── scorer.py          # Automated judge & statistical correlation benchmark evaluator
└── results/
    ├── metrics.json           # Machine-readable output metrics matching the write-up
    └── plots/                 # Generated empirical publication plots
```

---

## 🔐 Constraints & Compliance
- **Zero Paid APIs / Self-Contained Execution**: Runs 100% locally with open-weights LLM (`llama3.2:3b` via Ollama) and automatic deterministic grounded fallback, with zero external network or paid API dependencies (`last_call_cost = $0.0`).
- **Zero Hallucination Tolerance**: Every claim is strictly grounded in exact sentence quotes or parsed table coordinates.
- **Security Hardened**: Automatically detects and rejects prompt injection payloads in feedback.

---

## 🔬 System Limitations & Future Production Roadmap

While the verification gate rejects **17 of 48 submissions (35.4% noise rate)** and quarantines **4 low-trust submissions for human review**, production deployment requires recognizing edge-case boundaries:
- **Current Solved Capabilities**: Catches verbatim citation hallucinations, 1,000x magnitude unit errors ($115.9M vs $115,948M), multi-year temporal misattributions, negative assurance contradictions, and prompt injection attacks.
- **Theoretical Edge-Case Boundaries**: Pure deterministic lexical gates cannot fully catch subtle causal narrative fabrications (e.g., claiming a tax hike was due to "executive compensation" when the citation cites "earnings mix") or synthetic unquoted percentage deltas.
- **Production Scaling Roadmap**:
  1. *Deterministic Fast Sieve (Implemented)*: Filters corrupt feedback (ungrounded citations, magnitude errors, temporal misattributions, prompt injections) at zero API cost and low latency.
  2. *Local NLI Entailment Judge (Roadmap)*: Pipes surviving feedback through a local cross-encoder (`DeBERTa-v3` or structured local LLM) classifying Premise (10-K quote) vs Hypothesis (Analyst claim) as `Entailment`, `Neutral/Unsupported`, or `Contradiction`.
  3. *Symbolic Delta Verifier (Roadmap)*: Validates unquoted growth metrics using an AST arithmetic checker.
  4. *Multivariate Bayesian Trust (Roadmap)*: Expands Beta priors into topic-conditional trust matrices across distinct GAAP categories.
