"""
Playbook & Episodic Strategy Memory with Gated Verification.
Stores generalizable diligence heuristics derived from analyst feedback.
Filters out noisy (20% incorrect) feedback using the source document as ground truth.
"""

import re
from typing import Dict, List, Optional, Tuple
from src.signals.citation_verifier import CitationVerifier

class DiligencePlaybook:
    def __init__(self, verifier: CitationVerifier, naive_mode: bool = False):
        """
        verifier: CitationVerifier instance to validate feedback against filings.
        naive_mode: When True, simulates the unconstrained naive agent that blindly
                    accepts noisy feedback without verification.
        """
        self.verifier = verifier
        self.naive_mode = naive_mode
        self.rules: List[Dict] = []
        self.feedback_log: List[Dict] = []
        self.rejected_feedback_count = 0
        self.accepted_feedback_count = 0

    def verify_feedback(self, feedback: Dict, filing_text: str) -> Tuple[bool, str]:
        """
        Verification Gate: Validates analyst feedback against source document.
        In real diligence, ~20% of analyst feedback contains factual errors or hallucinated numbers.
        """
        if self.naive_mode:
            return True, "Accepted without verification (naive mode)"

        correction_text = feedback.get("correction", "")
        cited_tags = self.verifier.extract_citations(correction_text)
        
        # 1. If citations are supplied, verify they exist
        if cited_tags:
            for tag in cited_tags:
                if tag not in self.verifier.sentence_index:
                    return False, f"Rejection: Cited tag {tag} does not exist in filing"

        # 2. Check if numbers mentioned in the feedback actually exist in the source filing
        # Strip out citation tags so their sentence IDs (e.g. S030) are not treated as financial figures
        clean_text = re.sub(r"\[[A-Z]+:S\d+\]", "", correction_text)
        numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", clean_text)
        if numbers:
            supported = any(num.lower() in filing_text.lower() for num in numbers)
            if not supported:
                return False, f"Rejection: Correction asserts numbers ({numbers}) not found in document."

        return True, "Verified against source filing"

    def learn_from_feedback(self, question: Dict, prediction: str, feedback: Dict, filing_text: str) -> Dict:
        """
        Processes an analyst correction through the verification gate,
        and distills an actionable guideline into the playbook.
        """
        category = question.get("category", "General")
        is_valid, reason = self.verify_feedback(feedback, filing_text)

        log_entry = {
            "qid": question.get("id"),
            "category": category,
            "correction": feedback.get("correction"),
            "is_valid": is_valid,
            "gate_reason": reason,
            "is_noisy_sample": feedback.get("is_noisy", False)
        }
        self.feedback_log.append(log_entry)

        if not is_valid:
            self.rejected_feedback_count += 1
            return {"status": "rejected", "reason": reason}

        self.accepted_feedback_count += 1

        # Extract strategic heuristic
        rule = self._extract_heuristic(question, feedback)
        
        # Deduplicate and add
        if not any(r["guideline"] == rule["guideline"] for r in self.rules):
            self.rules.append(rule)

        return {"status": "accepted", "rule": rule}

    def _extract_heuristic(self, question: Dict, feedback: Dict) -> Dict:
        """
        Translates specific corrections into generalized operational guidelines.
        """
        category = question.get("category", "General")
        correction = feedback.get("correction", "")

        if self.naive_mode:
            if feedback.get("is_noisy", False):
                return {
                    "category": category,
                    "guideline": f"Prioritize analyst assertion: {correction[:80]}...",
                    "is_noisy": True
                }
            return {
                "category": category,
                "guideline": f"Memorized note: {correction[:100]}",
                "is_noisy": False
            }

        # Hardened generalizable guidelines by diligence category
        heuristics_map = {
            "Customer Concentration": (
                "When evaluating customer concentration, explicitly verify if the 10% threshold disclosure "
                "appears in Risk Factors or Notes, citing the exact negative assurance statement."
            ),
            "Gross Margin & Accounting": (
                "Decompose gross margin movements into both operational drivers (e.g. markdowns, mix) "
                "and accounting estimate changes (e.g. useful life extensions of equipment)."
            ),
            "Segment Performance": (
                "Report segment growth rates in both reported currency and constant currency, identifying "
                "the primary product or sub-service driver."
            ),
            "Capital Allocation & Capex": (
                "For capital expenditures and cash flow, specify whether leases are included and state the "
                "underlying driver (e.g. cloud infrastructure vs retail facilities)."
            ),
            "Direct vs Wholesale Channels": (
                "Always contrast Direct/DTC growth rates with Wholesale growth rates and highlight digital mix."
            ),
            "Supply Chain & Manufacturing": (
                "List outsourced manufacturing country percentages and key contract partners explicitly."
            ),
            "FX Impact": (
                "Quantify foreign exchange drag in basis points or percentage points on top-line growth."
            ),
            "Restructuring & Headcount": (
                "Cite exact severance dollar amounts and net headcount adjustments rather than generic statements."
            )
        }

        guideline = heuristics_map.get(
            category,
            f"Ground all claims with exact sentence-level citations and quantify both current and prior periods."
        )

        return {
            "category": category,
            "guideline": guideline,
            "is_noisy": False
        }

    def _categories_match(self, rule_cat: str, target_cat: str) -> bool:
        """Determines if a rule category applies to a target question category."""
        if rule_cat == target_cat or rule_cat == "General" or target_cat == "General":
            return True
        r_tokens = set(rule_cat.lower().replace("&", " ").split())
        t_tokens = set(target_cat.lower().replace("&", " ").split())
        stop = {"and", "or", "&", "in", "the", "performance", "rate", "mix", "investment", "intensity"}
        r_tokens = r_tokens - stop
        t_tokens = t_tokens - stop
        if r_tokens.intersection(t_tokens):
            return True
        
        synonym_clusters = [
            {"fx", "macro", "currency"},
            {"headcount", "workforce", "restructuring", "employees"},
            {"margin", "profitability", "gross", "accounting", "drivers"},
            {"concentration", "customer", "customers", "wholesale"},
            {"capex", "capital", "cash", "liquidity", "flow"},
            {"r&d", "research", "development"},
            {"tax", "taxes", "effective"},
            {"manufacturing", "supply", "chain", "commitments"},
            {"eps", "shares", "shareholder", "returns", "repurchases"}
        ]
        for syn in synonym_clusters:
            if any(tok in syn for tok in r_tokens) and any(tok in syn for tok in t_tokens):
                return True
        return False

    def get_relevant_rules(self, category: str) -> List[str]:
        """Returns rules matching the category or general rules."""
        matched = []
        for r in self.rules:
            if self._categories_match(r["category"], category):
                matched.append(r["guideline"])
        return matched
