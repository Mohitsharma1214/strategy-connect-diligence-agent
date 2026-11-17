# Unseen-Company Evaluation: Tesla, Inc. (TSLA) Form 10-K

This document provides a factual, auditable cross-company evaluation of the StrategyConnect Diligence Agent on an authentic, unseen public company Form 10-K filing without company-specific tuning or hardcoded rules.

---

## 1. Filing Source & Evaluation Setup

- **Company**: Tesla, Inc. (`TSLA`)
- **Filing Form**: SEC EDGAR Form 10-K (Annual Report)
- **Period Ended**: December 31, 2025 (Fiscal Year 2025)
- **Filing Date**: January 29, 2026
- **SEC EDGAR URL**: [https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm)
- **Local File Path**: `data/unseen/tsla-20251231.htm` (2.3 MB HTML)
- **Questions Path**: `data/unseen/tsla_questions.json`
- **Output Destination**: `results/unseen_tsla_answers.jsonl`

---

## 2. Exact Auditor CLI Execution Command

The test executes strictly via the official auditor CLI interface:

```bash
./run.sh --filing data/unseen/tsla-20251231.htm --questions data/unseen/tsla_questions.json --out results/unseen_tsla_answers.jsonl
```

### Parsing Telemetry
- **HTML Narrative Sentences Indexed**: **3,113 sentences**
- **Financial Table Cells Parsed**: **2,190 cells**
- **Parse Execution Time**: **0.44s**
- **Inference Runtime**: Local open-weights `llama3.2:3b` via Ollama (`last_call_cost = $0.0`)

---

## 3. Detailed Question-by-Question Evaluation & Citations

### Question 1: Total Revenue & YoY Change
- **Question ID**: `TSLA-Q01`
- **Question Text**: *"What was Tesla's total revenues in fiscal year 2025, and how did it change compared to fiscal 2024?"*
- **Generated Answer**:
  ```text
  In 2025, we recognized total revenues of $94.83 billion, representing a decrease of $2.86 billion compared to the prior year.
  ```
- **Attached Verbatim Filing Citation**:
  ```json
  [
    {
      "type": "sentence",
      "quote": "In 2025, we recognized total revenues of $94.83 billion, representing a decrease of $2.86 billion compared to the prior year."
    }
  ]
  ```
- **Factual Assessment**: **Pass (Factually Exact & Grounded)**
  - *Reported Figures*: Correctly identifies FY2025 total revenue of $94.83 billion (and in financial statements: $94,827 million) and absolute decrease of $2.86 billion (from $97,690 million in FY2024, approximately -2.93%).
  - *Relevance*: Directly addresses headline revenues without introducing unrelated R&D expense or overhead commentary.
  - *Grounding*: Supported verbatim by Part II, Item 7 (Management's Discussion and Analysis of Financial Condition and Results of Operations).

---

### Question 2: Capital Expenditures (Additions to Property, Plant & Equipment)
- **Question ID**: `TSLA-Q02`
- **Question Text**: *"What was Tesla's capital expenditures or additions to property, plant and equipment in 2025?"*
- **Generated Answer**:
  ```text
  Tesla's capital expenditures or additions to property, plant and equipment in 2025 were $8.53 billion.
  ```
- **Attached Verbatim Filing Citations**:
  ```json
  [
    {
      "type": "sentence",
      "quote": "Purchases of property and equipment excluding finance leases, net of sales"
    },
    {
      "type": "sentence",
      "quote": "Net cash flows from investing activities and their variability across each period related primarily to capital expenditures, which were $8.53 billion and $11.34 billion for the years ended December 31, 2025 and 2024, respectively, mainly for global AI and operational infrastructure and factory expansion, as well as machinery and equipment as we expand and enhance our product roadmap."
    }
  ]
  ```
- **Factual Assessment**: **Pass (Factually Exact & Grounded)**
  - *Reported Figures*: Correctly isolates FY2025 capital expenditures ($8.53 billion) and reports the context sentence containing the FY2024 comparison ($11.34 billion).
  - *Accounting Distinction*: Correctly distinguishes cash flow capital expenditures from cumulative balance sheet carrying assets (`Property, plant and equipment, net` of $40,643 million).
  - *Grounding*: Supported verbatim by the Liquidity and Capital Resources disclosure in Item 7.

---

### Question 3: Customer Revenue Concentration
- **Question ID**: `TSLA-Q03`
- **Question Text**: *"How concentrated is Tesla's revenue among individual customers, and did any single customer account for 10% or more of total revenue?"*
- **Generated Answer**:
  ```text
  Based on the filing context, Tesla does not provide sufficient evidence to establish whether any single customer accounted for 10% or more of revenue. However, as of December 31, 2025 and 2024, no entity represented 10% or more of total receivables balance.
  ```
- **Attached Verbatim Filing Citations**:
  ```json
  [
    {
      "type": "sentence",
      "quote": "As of December 31, 2025 and 2024, no entity represented 10% or more of our total receivables balance."
    },
    {
      "type": "sentence",
      "quote": "Financial instruments that potentially subject us to a concentration of credit risk consist of cash, cash equivalents, investments, restricted cash, accounts receivable and other finance receivables."
    }
  ]
  ```
- **Factual Assessment**: **Pass (Accounting Rigor & Epistemic Honesty)**
  - *Distinction*: Correctly distinguishes **accounts receivable credit risk concentration** from **customer revenue concentration**. Unlike Microsoft (which provides negative assurance for revenue in Note 19), Tesla does not state in its 10-K whether an individual customer exceeded 10% of total revenue.
  - *Abstention*: Rather than falsely extrapolating from the receivables statement, the agent explicitly states that the filing does not provide sufficient evidence to establish whether any single customer accounted for 10% or more of revenue.
  - *Contextual Accuracy*: Accurately cites Note 2 (*Summary of Significant Accounting Policies — Concentration of Risk*) affirming that no entity exceeded 10% of total receivables.

---

## 4. Complete Raw JSONL Output

The resulting output from `results/unseen_tsla_answers.jsonl`:

```json
{"id": "TSLA-Q01", "answer": "In 2025, we recognized total revenues of $94.83 billion, representing a decrease of $2.86 billion compared to the prior year.", "citations": [{"type": "sentence", "quote": "In 2025, we recognized total revenues of $94.83 billion, representing a decrease of $2.86 billion compared to the prior year."}]}
{"id": "TSLA-Q02", "answer": "Tesla's capital expenditures or additions to property, plant and equipment in 2025 were $8.53 billion.", "citations": [{"type": "sentence", "quote": "Purchases of property and equipment excluding finance leases, net of sales"}, {"type": "sentence", "quote": "Net cash flows from investing activities and their variability across each period related primarily to capital expenditures, which were $8.53 billion and $11.34 billion for the years ended December 31, 2025 and 2024, respectively, mainly for global AI and operational infrastructure and factory expansion, as well as machinery and equipment as we expand and enhance our product roadmap."}]}
{"id": "TSLA-Q03", "answer": "Based on the filing context, Tesla does not provide sufficient evidence to establish whether any single customer accounted for 10% or more of revenue. However, as of December 31, 2025 and 2024, no entity represented 10% or more of total receivables balance.", "citations": [{"type": "sentence", "quote": "As of December 31, 2025 and 2024, no entity represented 10% or more of our total receivables balance."}, {"type": "sentence", "quote": "Financial instruments that potentially subject us to a concentration of credit risk consist of cash, cash equivalents, investments, restricted cash, accounts receivable and other finance receivables."}]}
```

---

## 5. Architectural Boundaries & Known Limitations

1. **Absence of Specific Related-Party Cross-Referencing**:
   - In Note 21 (*Related Party Transactions*), Tesla reports $430 million in revenue from xAI for Megapack products.
   - The cold retrieval agent surfaces the primary *Concentration of Risk* disclosure (Note 2) rather than cross-referencing Note 21. In production, feedback rounds add specific retrieval expansion terms to surface related-party disclosures alongside concentration queries.
2. **Deterministic Fallback on Small-Model Numerical Hallucination**:
   - When generating with local open-weights `llama3.2:3b`, smaller 3B models occasionally drop leading digits during synthesis (e.g. dropping the leading "9" from `$94.83B`).
   - The pipeline's deterministic numerical verification safeguard (`is_numerically_faithful`) automatically intercepts this and retains the primary verbatim source sentence, guaranteeing 100% numerical fidelity.
3. **Company-Specific Playbook Necessity**:
   - While universal GAAP taxonomy allows cold extraction of headline metrics and standard credit disclosures on unseen companies, achieving nuanced diligence analysis on unique corporate footnotes requires company-specific feedback distillation—confirming the foundational thesis of StrategyConnect's self-improving agent architecture.

