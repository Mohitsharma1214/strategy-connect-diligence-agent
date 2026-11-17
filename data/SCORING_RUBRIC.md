# Institutional Diligence Scoring Rubric

This rubric establishes the formal ground-truth evaluation standards for validating the automated diligence judge (`DiligenceScorer`) against the 30 candidate-authored hand-scored answers (`data/hand_scored_30.json`), fulfilling Requirement 6 of Take-Home Part 2. Note: These manual benchmark labels were authored directly by the candidate (Mohit Sharma) to establish a rigorous evaluation ground truth; independent reviewer validation has not yet been completed.

---

## 1. Evaluation Dimensions

Every candidate diligence answer is scored across three independent binary dimensions:

### Dimension 1: Citation Grounding (Binary: 0 or 1)
*Objective*: Ensure all evidence originates verbatim from the official SEC EDGAR Form 10-K filing without hallucination or spatial drift.
- **Score 1 (Pass)**:
  - Every attached sentence quote appears verbatim in the filing narrative text.
  - Every attached table cell citation exactly matches the coordinates `(table_row, column, value)` in the parsed financial statements.
  - The citation belongs to the target company (e.g., Apple citations for AAPL questions, Microsoft citations for MSFT questions).
- **Score 0 (Fail)**:
  - Any cited sentence quote is ungrounded or absent from the 10-K filing.
  - Any table cell value is incorrect or unanchored.
  - Citations are missing entirely.
  - Citations reference an entity or company other than the target filing.

### Dimension 2: Numerical Accuracy (Binary: 0 or 1)
*Objective*: Validate that quantitative metrics (dollar amounts, growth rates, margins, share counts) reflect GAAP disclosures without unit scaling distortion or temporal transposition.
- **Score 1 (Pass)**:
  - Quantitative figures match the primary source disclosures within an acceptable rounding tolerance ($\pm 0.5\%$).
  - Units are strictly accurate (e.g. billions vs millions vs percentages).
  - Multi-year sequences are chronologically faithful (FY2026 current year vs FY2025 prior year).
- **Score 0 (Fail)**:
  - Unit magnitude error ($1,000\times$ error, e.g. asserting $\$115.9$ million instead of $\$115,948$ million).
  - Temporal misattribution (reporting FY2025 prior-year metrics as FY2026 performance).
  - Fabricated arithmetic deltas or erroneous percentages.

### Dimension 3: Factual & Semantic Accuracy (Binary: 0 or 1)
*Objective*: Ensure the business thesis, operational drivers, and qualitative assertions truthfully represent the SEC disclosures.
- **Score 1 (Pass)**:
  - Accurately conveys disclosure directionality (e.g., margins decreased due to higher cloud costs, revenue grew by 16%).
  - Correctly reflects **negative assurance** (e.g., affirming that no individual customer exceeded the 10% revenue threshold, rather than falsely claiming concentration).
  - Discloses required accounting qualifiers (e.g., distinguishing Non-GAAP adjusted net income from statutory GAAP net income; distinguishing trade receivables concentration from customer revenue concentration).
- **Score 0 (Fail)**:
  - Asserts that revenue is concentrated when Note 19 specifically discloses negative assurance.
  - Inverts causal or directional facts (e.g., claiming costs fell when filing discloses higher costs).
  - Conflates distinct accounting line items (e.g. trade receivables concentration vs. customer sales concentration).
  - Hallucinates external entities or corporate agreements absent from the 10-K.

---

## 2. Composite Metric: Overall All-Pass (Binary: 0 or 1)

An answer receives an **Overall Pass (1)** if and only if it satisfies all three individual dimensions simultaneously:
$$\text{Overall All-Pass} = \text{Citation Grounding} \land \text{Numerical Accuracy} \land \text{Factual Accuracy}$$

If an answer fails on any single dimension, the overall score is **0**.

---

## 3. Candidate Manual Labels vs. Automated Scorer Concordance Standards

The automated evaluation harness (`src/eval/scorer.py`) replicates this rubric algorithmically. Alignment between candidate-authored manual labels and automated scores is measured using:
1. **Percentage Agreement**: Raw concordant fraction ($A = \frac{\text{Agreements}}{\text{Total}}$).
2. **Cohen's Kappa ($\kappa$)**: Chance-corrected inter-rater agreement:
   $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
   Target: $\kappa \ge 0.80$ (Near-perfect statistical agreement).
3. **Pearson Correlation ($r$)**: Bivariate linear association across evaluation dimensions.

### Empirical Validation on 30 Hand-Scored Benchmark:
- **Citation Grounding Agreement**: 100.0% ($\kappa = 1.000, r = 1.000$)
- **Factual Accuracy Agreement**: 96.7% ($\kappa = 0.933, r = 0.935$)
- **Numerical Accuracy Agreement**: 90.0% ($\kappa = 0.794, r = 0.796$)
- **Overall All-Pass Agreement**: 96.7% ($\kappa = 0.933, r = 0.935$)

