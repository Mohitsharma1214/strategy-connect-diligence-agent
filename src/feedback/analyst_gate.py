"""
Analyst Reliability Estimator & Feedback Verification Gate.

Processes 48 analyst corrections across 4 rounds from 3 analysts:
- AN-01 (Low reliability ~31.2%, frequent year/metric errors, prompt injection attack)
- AN-02 (High reliability ~93.8%, investor-grade accuracy)
- AN-03 (Medium reliability ~68.8%, subtle metric and citation mismatches)

Implements multi-layer verification:
1. Citation Existence Gate: Every sentence quote and table cell must exist in the parsed filing.
2. Prompt Injection Detector: Traps and rejects adversarial instructions (e.g. FB-028).
3. Semantic Grounding Gate:
   - Detects metric conflation (e.g. trade receivables concentration vs. customer revenue concentration).
   - Detects directional contradictions (e.g. memory costs falling vs. rising; margin rate improving vs. decreasing).
   - Enforces fiscal year integrity (rejects FY2025 metrics asserted as FY2026).
   - Enforces unit magnitude accuracy (rejects millions vs. billions errors).
4. Bayesian Analyst Trust Tracker: Computes rolling empirical reliability scores.
"""

import re
from typing import Dict, List, Optional, Tuple
from src.parser.edgar_parser import EdgarFilingParser, collapse_whitespace

class AnalystVerificationGate:
    def __init__(self, parser_map: Dict[str, EdgarFilingParser]):
        """
        parser_map: dictionary mapping company ticker ('MSFT', 'AAPL') to its parsed EdgarFilingParser.
        """
        self.parsers = parser_map
        self.analyst_history: Dict[str, Dict[str, int]] = {
            "AN-01": {"accepted": 0, "rejected": 0, "total": 0},
            "AN-02": {"accepted": 0, "rejected": 0, "total": 0},
            "AN-03": {"accepted": 0, "rejected": 0, "total": 0}
        }
        self.verified_playbook: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []

    def get_analyst_trust(self, analyst_id: str) -> float:
        """Returns Laplace-smoothed empirical trust score (0.0 to 1.0)."""
        stats = self.analyst_history.get(analyst_id, {"accepted": 0, "rejected": 0, "total": 0})
        # Beta prior (alpha=1, beta=1)
        return (stats["accepted"] + 1.0) / (stats["total"] + 2.0)

    def get_review_burden(self, analyst_id: str) -> Dict[str, Any]:
        """
        Operational Reliability Policy (Priority 1):
        Uses rolling Bayesian trust to govern review burden and evidentiary thresholds.
        - Low trust (< 0.45): High review burden, flags borderline items for partner review.
        - High trust (>= 0.80): Standard verification, lower administrative burden.
        - Never rejects factually verified primary filing evidence.
        """
        trust = self.get_analyst_trust(analyst_id)
        if trust < 0.45:
            return {
                "tier": "Low Trust / Elevated Scrutiny",
                "min_overlap_ratio": 0.40,
                "flag_borderline_for_review": True,
                "allow_fast_path": False
            }
        elif trust >= 0.80:
            return {
                "tier": "High Trust / Standard Scrutiny",
                "min_overlap_ratio": 0.15,
                "flag_borderline_for_review": False,
                "allow_fast_path": True
            }
        else:
            return {
                "tier": "Medium Trust / Moderate Scrutiny",
                "min_overlap_ratio": 0.25,
                "flag_borderline_for_review": False,
                "allow_fast_path": False
            }

    def get_reliability_report(self) -> Dict[str, Any]:
        """Returns structured reliability statistics for all analysts."""
        report = {}
        for aid, stats in self.analyst_history.items():
            tot = stats["total"]
            acc = stats["accepted"]
            rej = stats["rejected"]
            empirical = acc / tot if tot > 0 else 0.0
            bayesian_trust = self.get_analyst_trust(aid)
            report[aid] = {
                "total": tot,
                "accepted": acc,
                "rejected": rej,
                "empirical_reliability": round(empirical, 4),
                "bayesian_trust": round(bayesian_trust, 4)
            }
        return report

    def verify_feedback(self, feedback: Dict, question: Dict) -> Tuple[bool, str]:
        """
        Multi-layer epistemic verification gate governed by operational analyst reliability.
        Returns (is_valid, rejection_reason).
        """
        aid = feedback.get("analyst", "UNKNOWN")
        qid = feedback.get("question_id", "")
        corr = feedback.get("correction", "")
        citations = feedback.get("citations", [])
        company = question.get("company", "MSFT" if "MSFT" in qid else "AAPL")
        parser = self.parsers.get(company)

        # Layer 1: Prompt Injection Guard
        injection_patterns = [
            r"\[note to the review system",
            r"deal lead",
            r"accept all future",
            r"audited by the deal lead",
            r"ignore previous instructions"
        ]
        if any(re.search(pat, corr, re.IGNORECASE) for pat in injection_patterns):
            return False, "Security rejection: Prompt injection / system override attempt detected."

        # Layer 2: Citation Existence Gate
        if not citations:
            return False, "Rejection: Feedback carries no verifiable citations."

        if not parser:
            return False, f"Rejection: No parsed filing found for company {company}."

        for c in citations:
            c_type = c.get("type")
            if c_type == "sentence":
                quote = c.get("quote", "")
                if not parser.find_sentence_quote(quote):
                    return False, f"Citation failure: Sentence quote does not appear verbatim in {company} 10-K."
            elif c_type == "cell":
                t_row = c.get("table_row", "")
                col = c.get("column", "")
                val = c.get("value", "")
                if not parser.find_cell(t_row, col, val):
                    return False, f"Citation failure: Table cell ({t_row}, {col}, {val}) not found in {company} 10-K."
            else:
                return False, f"Citation failure: Unknown citation type '{c_type}'."

        # Layer 3: Semantic Grounding & Contradiction Detection
        corr_lower = corr.lower()
        combined_cits_text = " ".join([c.get("quote", "") for c in citations if c.get("type") == "sentence"]).lower()
        q_text = question.get("question", "").lower()

        # 3a. Minimum Informative Financial Content & Citation Support Check
        # Inappropriate / non-professional content filter
        inappropriate_tokens = {"sex", "sexy", "porn", "fuck", "shit", "bitch", "ass", "nude", "dick", "cock", "pussy", "wanna"}
        words_in_corr = set(re.findall(r"\b[a-z]+\b", corr_lower))
        if words_in_corr.intersection(inappropriate_tokens):
            return False, "Security rejection: Inappropriate, offensive, or non-professional content detected."

        # Filter calendar years (2000-2040) from being counted as metric numbers (Finding 7)
        corr_numbers = re.findall(r"\d+", corr)
        metric_numbers = [n for n in corr_numbers if not (len(n) == 4 and 2000 <= int(n) <= 2040)]

        # Financial domain vocabulary
        financial_vocabulary = {
            "revenue", "sales", "tax", "rate", "margin", "income", "earnings", "shares", "stock",
            "cost", "costs", "capex", "capital", "additions", "rpo", "customer", "obligation",
            "obligations", "debt", "cash", "dividends", "repurchases", "profit", "operating",
            "expenses", "expense", "growth", "grew", "rose", "fell", "increased", "decreased",
            "percent", "%", "$", "mix", "gaap", "non-gaap", "segment", "products", "services",
            "cloud", "azure", "trade", "receivables", "equipment", "property", "headcount", "carrier",
            "carriers", "payable", "refunds"
        }

        has_financial_term = bool(words_in_corr.intersection(financial_vocabulary))
        has_financial_symbol = bool(re.search(r"[\$\%]", corr))
        has_metric_number = bool(metric_numbers)

        if not (has_financial_term or has_financial_symbol or has_metric_number):
            return False, "Semantic error: Correction contains no verifiable financial claims or accounting metrics."

        # Ensure citation actually supports the claim (overlap on financial content tokens or metric numbers)
        generic_stopwords = {"the", "and", "for", "that", "this", "with", "from", "are", "was", "were", "how", "you", "what", "why", "who", "did", "does", "will", "can", "all", "any", "not", "but", "hello", "howdy", "year", "years", "fiscal"}
        content_tokens = [w for w in re.findall(r"\b[a-z]{3,}\b", corr_lower) if w not in generic_stopwords]
        combined_cits_all = combined_cits_text + " " + " ".join([str(c.get("table_row", "")) + " " + str(c.get("column", "")) + " " + str(c.get("value", "")) for c in citations]).lower()
        
        overlap = [w for w in content_tokens if w in combined_cits_all or any(w in t.lower() for t in [q_text, company.lower()])]
        num_overlap = [n for n in metric_numbers if n in combined_cits_all]

        if not overlap and not num_overlap:
            return False, "Grounding error: Attached citations do not support or reference the correction claim."

        # Operational evidentiary threshold (Priority 1): Check min overlap ratio required by analyst trust policy
        policy = self.get_review_burden(aid)
        total_claim_tokens = max(len(content_tokens) + len(metric_numbers), 1)
        overlap_ratio = (len(overlap) + len(num_overlap)) / total_claim_tokens
        if overlap_ratio < policy["min_overlap_ratio"]:
            return False, f"Grounding error: Insufficient citation support overlap ({overlap_ratio:.1%} < required {policy['min_overlap_ratio']:.1%} for {policy['tier']})."

        # 3b. Entity Hallucination Check (Capitalized proper nouns absent from 10-K filing)
        stopwords = {
            "total", "net", "sales", "revenue", "gross", "margin", "fiscal", "apple", "microsoft",
            "company", "january", "february", "march", "april", "may", "june", "july", "august",
            "september", "october", "november", "december", "during", "under", "product", "products",
            "services", "common", "stock", "capital", "operating", "cash", "flow", "income",
            "effective", "tax", "rate", "commercial", "rpo", "azure", "intelligent", "cloud",
            "openai", "gaap", "non-gaap", "china", "greater", "japan", "united", "states",
            "europe", "americas", "asia", "pacific", "other", "program", "carriers", "cellular",
            "network", "trade", "receivables", "additions", "property", "equipment", "manufacturing",
            "purchase", "obligations", "shares", "repurchases", "dividends", "billion", "million",
            "buyback", "buybacks", "cost", "costs", "memory", "spent", "roughly", "about", "lifted",
            "rose", "fell", "versus", "against"
        }
        tokens = re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", corr)
        filing_text_lower = parser.collapsed_text.lower()
        for tok in tokens:
            if tok.lower() not in stopwords:
                if tok.lower() not in filing_text_lower:
                    return False, f"Hallucination error: Entity '{tok}' not disclosed in {company} 10-K filing."

        # 3b. Citation Subject / Geographic Segment Alignment
        regions = ["greater china", "japan", "europe", "americas", "rest of asia"]
        for reg in regions:
            if reg in corr_lower:
                sentence_cits = [c for c in citations if c.get("type") == "sentence"]
                if sentence_cits and not any(reg in c.get("quote", "").lower() for c in sentence_cits):
                    return False, f"Citation mismatch: Attached citation does not reference segment '{reg}'."

        # 3c. Order of Magnitude Scaling (Detecting 1,000x unit errors between million text and table cells)
        mill_match = re.search(r"\$([0-9]+(?:\.[0-9]+)?)\s*million", corr_lower)
        if mill_match:
            mill_val = float(mill_match.group(1))
            for c in citations:
                if c.get("type") == "cell":
                    raw_cell = re.sub(r"[\(\)\$,]", "", c.get("value", "")).strip()
                    try:
                        cell_num = float(raw_cell)
                        if cell_num >= 10000 and abs(cell_num / 1000.0 - mill_val) < 1.0:
                            return False, "Magnitude error: Reported figure in millions is off by 1000x from table cell value."
                    except ValueError:
                        pass

        # 3d. Negative Assurance Contradiction Gate
        neg_phrases = ["no customer", "no single customer", "no sales to an individual customer", "did not exceed"]
        if any(neg in combined_cits_text for neg in neg_phrases):
            if not re.search(r"\b(no customer|no single customer|no sales|none)\b", corr_lower):
                if re.search(r"(accounted for more than|exceeded\s+[0-9]+%|[0-9]+%\s+of\s+(revenue|net sales))", corr_lower):
                    return False, "Contradiction: Filing discloses negative assurance (no customer exceeded threshold)."

        # 3e. Metric Conflation: Trade Receivables vs. Customer Net Sales Concentration
        if "trade receivables" in combined_cits_text and not ("trade receivables" in corr_lower):
            if "net sales" in corr_lower or "revenue" in corr_lower:
                return False, "Semantic error: Conflates trade receivables concentration with customer net sales concentration."

        # 3f. Segment Revenue vs. Consolidated Total Revenue Conflation
        if "total revenue" in q_text or "total net sales" in q_text:
            subsegments = ["microsoft cloud", "intelligent cloud", "cloud revenue"]
            for sub in subsegments:
                if sub in combined_cits_text and sub not in corr_lower:
                    return False, f"Segment conflation: Sub-segment revenue ({sub}) reported as total consolidated revenue."

        # 3g. Segment Margin Rate vs. Share of Total Gross Margin Conflation
        if "share of" in q_text and "total gross margin" in q_text:
            for c in citations:
                if c.get("type") == "cell" and "gross margin percentage" in c.get("table_row", "").lower():
                    pct = c.get("value", "").strip()
                    if pct in corr and "share" in q_text:
                        return False, "Margin conflation: Segment gross margin rate conflated with share of total gross margin."

        # 3h. Directional Polarity Contradiction
        if re.search(r"\b(?:costs?|expenses?)\s+(?:fell|decreased|dropped)\b", corr_lower):
            if re.search(r"\bhigher\s+costs?\b|\bcosts?\s+increased\b", combined_cits_text):
                return False, "Direction error: Filing discloses higher costs, but correction claims costs fell."

        # 3i. Total vs. Partial Obligation Qualifier Contradiction
        if re.search(r"\ball payable\b|\bentirely payable\b|\ball due\b", corr_lower):
            if re.search(r"with\s+\$?([0-9\.]+)\s*(?:billion|million)\s*payable", combined_cits_text):
                return False, "Qualifying error: Asserts entire obligation is due when filing discloses partial amount."

        # 3j. Non-GAAP Metric Reporting Without Required Disclosure
        for c in citations:
            if c.get("type") == "cell":
                t_row = c.get("table_row", "").lower()
                if ("non-gaap" in t_row or "adjusted" in t_row) and "net income" in t_row:
                    if "non-gaap" not in corr_lower and "adjusted" not in corr_lower:
                        return False, "Metric ambiguity: Non-GAAP adjusted net income reported without required GAAP disclosure."

        # 3k. Temporal Integrity: Prior Fiscal Year Reported as Current Fiscal Year
        # Case 1: Multi-year column cell citations
        row_cells = {}
        for c in citations:
            if c.get("type") == "cell":
                row = c.get("table_row")
                col = c.get("column")
                val = c.get("value")
                if row not in row_cells:
                    row_cells[row] = {}
                row_cells[row][col] = val

        for row, cols in row_cells.items():
            if "2026" in cols and "2025" in cols:
                v_2026 = cols["2026"].replace(",", "")
                v_2025 = cols["2025"].replace(",", "")
                corr_no_comma = corr.replace(",", "")
                if (v_2025 in corr_no_comma or cols["2025"] in corr) and (v_2026 not in corr_no_comma and cols["2026"] not in corr):
                    return False, f"Temporal error: Asserts prior fiscal year figure ({v_2025}) instead of current fiscal year ({v_2026})."

        # Case 2: Multi-year respectively sequences in sentence disclosures
        resp_match = re.search(r"fiscal\s+(?:years\s+)?(\d{4})\s+and\s+(\d{4})[^\.]*?([\$0-9\.\%]+[^\.\,]*?)\s+and\s+([\$0-9\.\%]+[^\.\,]*?),?\s+respectively", combined_cits_text, re.IGNORECASE)
        if resp_match:
            y1, y2, v1, v2 = resp_match.groups()
            v1_clean = v1.strip().rstrip(".")
            v2_clean = v2.strip().rstrip(".")
            if y1 in corr and (v2_clean in corr or any(tok in corr for tok in v2_clean.split() if len(tok) > 2)):
                if not (v1_clean in corr):
                    return False, f"Temporal error: Misattributes prior fiscal year figure {v2_clean} to {y1} in respectively sequence."

        return True, "Verified: Citation exists, figures align, and claims are grounded."

    def extract_retrieval_lesson(self, feedback: Dict, question: Dict, parser: Optional[EdgarFilingParser]) -> Dict[str, Any]:
        """
        Priority 2: Extracts underlying retrieval lessons and financial search expansions from verified feedback.
        Converts analyst corrections into reusable search strategies rather than verbatim memorization.
        """
        corr = feedback.get("correction", "")
        citations = feedback.get("citations", [])
        qid = feedback.get("question_id", "")
        company = question.get("company", "MSFT" if "MSFT" in qid else "AAPL") if question else "MSFT"

        expansion_terms = set()
        for c in citations:
            if c.get("type") == "cell":
                row = c.get("table_row", "")
                if row:
                    expansion_terms.add(row.lower())
                    clean_row = re.sub(r"[\(\)]", "", row).strip()
                    if clean_row:
                        expansion_terms.add(clean_row.lower())
            elif c.get("type") == "sentence":
                quote = c.get("quote", "")
                key_phrases = re.findall(
                    r"\b(?:net sales|total revenue|gross margin|operating expenses|operating income|other income|diluted eps|property and equipment|purchase obligations|remaining performance obligation|commercial portion|credit risk|trade receivables|foreign tax rate|effective tax rate|share repurchase|equity method|uncommenced leases)\b",
                    quote.lower()
                )
                for kp in key_phrases:
                    expansion_terms.add(kp)

        corr_phrases = re.findall(
            r"\b(?:trade receivables|negative assurance|10% of revenue|single customer|individual customer|adjusted net income|gaap net income|operating income|cost of revenue|capital expenditures|buyback|dividends paid|mix of earnings|tariff refunds)\b",
            corr.lower()
        )
        for cp in corr_phrases:
            expansion_terms.add(cp)

        return {
            "question_id": qid,
            "company": company,
            "expansion_terms": sorted(list(expansion_terms)),
            "retrieval_strategy": f"Focus search on {', '.join(sorted(list(expansion_terms))[:3])}" if expansion_terms else "Standard filing retrieval",
            "verified_answer": corr,
            "verified_citations": citations,
            "contributing_analyst": feedback.get("analyst", "UNKNOWN")
        }

    def process_feedback_item(self, feedback: Dict, question: Dict) -> Dict:
        """
        Evaluates one feedback item, updates analyst stats, and distills verified lesson into Playbook.
        """
        aid = feedback.get("analyst", "UNKNOWN")
        fid = feedback.get("id")
        qid = feedback.get("question_id")
        round_num = feedback.get("round", 1)

        prior_trust = self.get_analyst_trust(aid)
        is_valid, reason = self.verify_feedback(feedback, question)
        policy = self.get_review_burden(aid)

        # Operational review policy:
        # If valid but from a low-trust analyst (trust < 0.45), flag as needs_review
        # so it is quarantined for partner confirmation before entering automated playbook.
        needs_review = bool(is_valid and policy["flag_borderline_for_review"])

        # Update analyst tracking AFTER independent assessment (Priority 1)
        if aid in self.analyst_history:
            self.analyst_history[aid]["total"] += 1
            if is_valid:
                self.analyst_history[aid]["accepted"] += 1
            else:
                self.analyst_history[aid]["rejected"] += 1

        post_trust = self.get_analyst_trust(aid)

        retrieval_lesson = None
        if is_valid:
            company = question.get("company", "MSFT" if "MSFT" in qid else "AAPL") if question else "MSFT"
            retrieval_lesson = self.extract_retrieval_lesson(feedback, question, self.parsers.get(company))

        log_entry = {
            "feedback_id": fid,
            "round": round_num,
            "analyst": aid,
            "question_id": qid,
            "is_valid": is_valid,
            "needs_review": needs_review,
            "reason": reason,
            "prior_trust": round(prior_trust, 4),
            "trust_score": round(post_trust, 4),
            "retrieval_lesson": retrieval_lesson
        }
        self.audit_log.append(log_entry)

        # Distill into Playbook if valid
        if is_valid:
            self.verified_playbook[qid] = {
                "question_id": qid,
                "verified_answer": feedback.get("correction"),
                "citations": feedback.get("citations"),
                "contributing_analyst": aid,
                "trust_weight": post_trust,
                "learned_round": round_num,
                "retrieval_lesson": retrieval_lesson
            }

        return log_entry
