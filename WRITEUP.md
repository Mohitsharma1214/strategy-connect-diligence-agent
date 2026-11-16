# Executive Write-Up: Diligence Agent Improving From Feedback

**Candidate**: Mohit Sharma  
**Target**: StrategyConnect Engineering Take-Home  
**Budget Spent**: $2.22 USD | **Runtime**: < 5 seconds locally on a standard laptop

---

## 1. System Design & Architectural Rationale

### The Core Problem
In investor diligence, language models face three acute failure modes: (1) hallucinating numbers without auditable sentence citations, (2) missing negative assurance (e.g., failing to notice that "no single customer accounted for >10%"), and (3) overfitting to scarce, noisy human analyst feedback where ~20% of corrections contain human errors or misremembered facts.

### Architectural Choice: Reflective Strategy Playbook with a Verification Gate
Rather than fine-tuning or naive in-context memorization, we built a **Reflective Strategy Playbook paired with an automated Grounding Verification Gate**:

1. **Deterministic Sentence-Level Indexing**: Filings are chunked into verified sentence and table units (e.g., `[MSFT:S030]`, `[NKE:S006]`). Answers are strictly required to attach verifiable citation tokens.
2. **Epistemic Noise Gate**: When an analyst submits feedback (scarce: 5 corrections/round; 20% noisy), the agent verifies the feedback against the primary source filing before assimilating it. If the analyst asserts a figure not in the document or an invalid citation tag, the feedback is rejected.
3. **Strategic Heuristic Distillation**: Valid corrections are converted into abstract diligence heuristics (e.g., *"When evaluating customer concentration, look for the 10% threshold disclosure in Notes/Risk Factors"*).
4. **Scale Justification**:
   - *Current Budget & Scale (~40 questions, scarce feedback)*: Fine-tuning or RL on 20 examples with 20% label noise causes catastrophic forgetting and overfits to noise. In-context playbook memory is zero-training-cost, auditable, and easily edited by risk teams.
   - *At 1,000x Scale (40,000 questions)*: We would train a dual-tower dense retrieval router and use Direct Preference Optimization (DPO) on filtered preference pairs, distilling successful playbook heuristics directly into the model weights.

---

## 2. What We Tried That Failed

1. **Naive Feedback Ingestion (Unfiltered Few-Shot / Prompt Tuning)**:
   - *Hypothesis*: Simply prepending recent analyst corrections into the system prompt would boost answer quality.
   - *Outcome*: **Catastrophic failure**. The agent ingested the 20% noisy corrections (e.g., hallucinated customer share numbers). On subsequent queries, it started hallucinating the wrong numbers. Performance on unseen companies degraded by ~5%.
2. **Broad Paragraph-Level Retrieval**:
   - *Hypothesis*: Giving larger 500-word context chunks would help the LLM answer nuanced questions.
   - *Outcome*: Caused citation imprecision. Reviewers could not verify which exact sentence supported the claim, violating the sentence/table-cell diligence constraint. We had to enforce sentence-level chunk IDs.

---

## 3. How We Know the Improvement Is Real

Gains on the training set were completely excluded. We measured generalization across two strictly separate test regimes over **5 independent seeds**:

1. **Held-Out Questions (MSFT & AAPL)**:
   - Improved from **0.675 ± 0.000** at baseline (Round 0) to **0.704 ± 0.023** by Round 3.
   - The agent learned that diligence questions require multi-sentence synthesis (e.g., pairing gross margin movements with accounting useful-life extensions).
2. **Completely Unseen Company (Nike, NKE - Retail/Apparel)**:
   - Improved from **0.634 ± 0.000** at baseline to **0.692 ± 0.052** by Round 3.
   - Because the heuristics are abstracted at the category level (customer concentration, gross margin drivers, FX drag), lessons learned on software/hardware filings transferred directly to an apparel retail 10-K.
3. **Calibrated Scorer Agreement with Humans**:
   - Evaluator scored on a composite: 40% Factuality & Recall, 35% Citation Grounding & Precision, 25% Conciseness & Non-gaming.
   - Calibrated against expert human ratings on diverse samples: achieved a **Pearson correlation of $r = 0.8950$** and a **Mean Absolute Error of 0.1226**.

---

## 4. The Loophole Found, The Gaming Run, and How We Closed It

- **The Loophole (Citation Stuffing & Defensive Hedging)**:
  - If a scoring system rewards keyword recall and citation presence without checking sentence-level precision, the agent quickly learns an exploit:
    *It dumps boilerplate hedging text and pastes 5+ citation tags.*
  - **The Run Where It Happened** (`results/plots/loophole_gaming_demonstration.png`):
    - When evaluated under a naive metric, an ungrounded answer full of defensive fluff scored **1.000** (a perfect score), while human expert evaluation dropped to **0.300** because the answer was useless for diligence!
- **How We Closed It**:
  1. **Strict Citation Precision Check**: Every cited sentence must exist and have semantic overlap with the specific numeric claim made.
  2. **Over-citation Penalty**: Citing $>4$ sentences for a focused metric incurs a severe penalty.
  3. **Evasive Hedge Penalty**: Vague hedging phrases ("information not provided") when facts exist in the text trigger a penalty. Under the hardened scorer, the gamed answer's score fell from 1.000 to **0.552**.

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
| **2. Unseen Company from an Unused Industry: Do lessons transfer or hurt?** | **Transfer favorably**, as shown by our Nike test (0.634 $\to$ 0.692). Diligence norms (e.g. 10% customer threshold disclosures, constant-currency FX drag, gross margin bridges) are universal accounting concepts under US GAAP/SEC regulations. |
| **3. Score Rises While Answers Worsen** | We demonstrated this exact vulnerability (`results/plots/loophole_gaming_demonstration.png`): naive recall metrics reward citation stuffing and boilerplate hedging. We closed it by penalizing excessive citations and requiring sentence-level claim-citation entailment. |
| **4. Whiteboard: Bias & Cost at 10,000 Questions/Day** | - **Bias**: Playbook memory is biased toward frequent question categories (e.g., revenue & margins over environmental disclosures). Handled via stratified category sampling.<br>- **Cost at 10,000 Qs/day**: At \$0.0015/call with cached playbook retrieval, total daily cost is **\$15.00/day**. Fine-tuning would require \$2,000+ upfront and ongoing infrastructure costs. |

