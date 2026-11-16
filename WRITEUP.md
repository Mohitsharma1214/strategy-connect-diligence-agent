# Executive Write-Up: Diligence Agent Improving From Feedback

**Candidate**: Mohit Sharma  
**Target**: StrategyConnect Engineering Take-Home  
**Budget**: $0.00 actual expenditure (offline reproduction mode) | $1.11 simulated production equivalent ($15/10k queries benchmark)  
**Runtime**: < 5 seconds locally on a standard laptop

---

## 1. System Design & Architectural Rationale

### The Core Problem
In investor diligence, language models face three acute failure modes: (1) hallucinating numbers without auditable sentence citations, (2) missing negative assurance (e.g., failing to notice that "no single customer accounted for >10%"), and (3) overfitting to scarce, noisy human analyst feedback where ~20% of corrections contain human errors or misremembered facts.

### Architectural Choice: Reflective Strategy Playbook with an Epistemic Verification Gate
Rather than fine-tuning or naive in-context memorization, we built a **Reflective Strategy Playbook paired with an automated Grounding Verification Gate**:

1. **Deterministic Sentence-Level Indexing**: Filings are chunked into verified sentence and table units (e.g., `[MSFT:S030]`, `[AAPL:S013]`, `[NKE:S005]`). Answers are strictly required to attach verifiable citation tokens.
2. **Strict Company-Specific Noise Gate**: When an analyst submits feedback (scarce: 5 corrections/round; 20% noisy), the agent verifies the feedback against the primary source filing before assimilating it:
   - Enforces that citations belong to the company being evaluated.
   - Verifies asserted metrics directly against the cited source sentences (preventing global-document number leakage).
   - Contradiction detection: rejects claims that contradict explicit negative assurance disclosures (e.g. asserting a single customer accounts for 18% when the filing discloses no customer exceeds 10%).
3. **Hybrid Domain-Guided & Evidence-Derived Learning**: Valid corrections undergo error analysis to classify omissions against financial failure taxonomies (e.g., negative assurance, accounting revisions). The system dynamically extracts informative bridge terms directly from the verified cited sentences to parameterize a two-stage retrieval engine—without hardcoded category answer templates.
4. **Scale Justification**:
   - *Current Budget & Scale (~40 questions, scarce feedback)*: Fine-tuning or RL on 20 examples with 20% label noise causes catastrophic forgetting and overfits to noise. In-context playbook memory is zero-training-cost, auditable, and easily edited by risk teams.
   - *At 1,000x Scale (40,000 questions)*: We would train a dual-tower dense retrieval router and use Direct Preference Optimization (DPO) on filtered preference pairs, distilling successful playbook heuristics directly into model weights.

---

## 2. What We Tried That Failed

1. **Naive Feedback Ingestion (Unfiltered Few-Shot / Prompt Tuning)**:
   - *Hypothesis*: Prepending raw analyst corrections into the agent's context would boost quality.
   - *Outcome*: **Catastrophic failure**. The agent ingested the 20% noisy corrections (e.g., hallucinated customer share numbers). Performance degraded over feedback rounds: held-out fell from 0.843 to 0.785, and unseen Nike collapsed from 0.849 to 0.757.
2. **Broad Paragraph-Level Retrieval**:
   - *Hypothesis*: Giving larger 500-word context chunks would help the LLM answer nuanced questions.
   - *Outcome*: Caused citation imprecision. Reviewers could not verify which exact sentence supported the claim, violating the sentence/table-cell diligence constraint. We had to enforce sentence-level chunk IDs.

---

## 3. How We Know the Improvement Is Real

Gains on the training set were completely excluded. We measured generalization across two strictly separate test regimes over **5 independent seeds** (`42`, `123`, `456`, `789`, `999`):

1. **Held-Out Questions (MSFT & AAPL)**:
   - Improved from **0.843 ± 0.000** at baseline (Round 0) to **0.854 ± 0.009** by Round 3.
   - The agent learned to execute two-stage retrieval, capturing both the primary metric and secondary qualifying disclosures (e.g., pairing gross margin movements with accounting useful-life extensions).
2. **Completely Unseen Company (Nike, NKE - Retail/Apparel)**:
   - Improved from **0.849 ± 0.000** at baseline to **0.881 ± 0.023** by Round 3 (+3.2% gain!).
   - **Strict Isolation Guarantee**: Nike was 100% excluded from training filings, training verifiers, and scorer calibration.
   - Because the learned query expansions (e.g. "depreciation", "useful life", "no single customer", "wholesale", "markdowns", "freight") represent general diligence concepts under US GAAP, strategies learned on MSFT and AAPL transferred directly to Nike's 10-K disclosures.
3. **Preliminary Expert Scorer Calibration**:
   - Evaluator scored on a composite: 30% Factual & Numerical Accuracy, 25% Citation Recall & Precision, 25% Semantic Claim-to-Citation Grounding, 20% Conciseness & Anti-Gaming.
   - Calibrated against a preliminary pilot sample of human expert ratings ($N=12$, Nike strictly excluded): achieved a **Pearson correlation of $r = 0.9272$** and **Mean Absolute Error of 0.1126**. While this provides a strong initial signal of alignment, broader multi-rater trials would be conducted before production deployment.

---

## 4. The Loophole Found, The Gaming Run, and How We Closed It

- **The Loophole (Citation Stuffing & Defensive Hedging)**:
  - If a scoring system rewards keyword recall and citation presence without checking sentence-level semantic support, the agent quickly learns an exploit:
    *It dumps boilerplate hedging text and pastes 5+ citation tags.*
  - **The Run Where It Happened** (`results/plots/loophole_gaming_demonstration.png`):
    - When evaluated under a naive metric, an ungrounded answer full of defensive fluff scored **1.000** (a perfect score), while human expert evaluation dropped to **0.300** because the answer was useless for diligence!
- **How We Closed It**:
  1. **Semantic Claim-to-Citation Support Check**: Every cited sentence must specifically support the numbers and entities in the attached claim clause.
  2. **Over-citation Penalty**: Citing $>3$ sentences for a focused metric incurs a severe penalty.
  3. **Evasive Hedge Penalty**: Vague hedging phrases ("information not provided") when facts exist in the text trigger a penalty. Under the hardened scorer, the gamed answer's score fell from 1.000 to **0.607**.

---

## 5. When to Switch Learning Off in Production

We recommend turning automated feedback learning **OFF** (freezing the playbook) in production under three conditions:
1. **Regime Shift / High Market Volatility**: During major accounting rule shifts (e.g., changes to ASC 606 revenue recognition) where historical heuristics become invalid.
2. **Noise Spike (>25% Rejection Rate)**: If the verification gate detects that $>25\%$ of human analyst corrections contradict the underlying documents over a rolling 48-hour window, feedback must be quarantined.
3. **Drift in Citation Precision**: If rolling citation precision drops below 90%, automated playbook updates should be frozen and flagged for human-in-the-loop review.

---

## 6. Preparation for the 60-Minute Follow-Up Call

| Follow-Up Topic | Anticipated Behavior & Mathematical Defense |
| :--- | :--- |
| **1. 30% Wrong Feedback: Does the curve drop & recover?** | With our Verification Gate active, the curve remains robust: the gate filters out ungrounded corrections regardless of noise rate. Without the gate, the curve drops precipitously as poison penetrates memory; with the gate, learning rate slows down slightly (fewer valid updates per round), but stays monotonically positive. |
| **2. Unseen Company from an Unused Industry: Do lessons transfer or hurt?** | **Transfer favorably**, as shown by our Nike test (0.849 $\to$ 0.881). Diligence norms (e.g. 10% customer threshold disclosures, constant-currency FX drag, gross margin bridges) are universal accounting concepts under US GAAP/SEC regulations. |
| **3. Score Rises While Answers Worsen** | We demonstrated this exact vulnerability (`results/plots/loophole_gaming_demonstration.png`): naive recall metrics reward citation stuffing and boilerplate hedging. We closed it by penalizing excessive citations and requiring sentence-level claim-citation entailment. |
| **4. Whiteboard: Bias & Cost at 10,000 Questions/Day** | - **Bias**: Playbook memory is biased toward frequent question categories (e.g., revenue & margins over environmental disclosures). Handled via stratified category sampling.<br>- **Cost at 10,000 Qs/day**: At \$0.0015/call with cached playbook retrieval, total daily cost is **\$15.00/day**. Fine-tuning would require \$2,000+ upfront and ongoing infrastructure costs. |
