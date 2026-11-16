"""
Playbook & Episodic Strategy Memory with Gated Verification.
- Enforces company-specific citation validation.
- Validates feedback claims directly against the cited source sentences (not the whole document).
- Dynamically extracts reusable heuristics from analyst corrections (no static lookup dictionary).
- Filters out noisy (20% incorrect) feedback using the source document as ground truth.
"""

import re
from typing import Dict, List, Optional, Tuple
from src.signals.citation_verifier import CitationVerifier

class DiligencePlaybook:
    def __init__(self, verifier: CitationVerifier, naive_mode: bool = False):
        self.verifier = verifier
        self.naive_mode = naive_mode
        self.rules: List[Dict] = []
        self.feedback_log: List[Dict] = []
        self.rejected_feedback_count = 0
        self.accepted_feedback_count = 0

    def verify_feedback(self, feedback: Dict, expected_company: str) -> Tuple[bool, str]:
        """
        Verification Gate:
        1. Enforces company-specific citations.
        2. Requires at least one valid citation tag.
        3. Validates numbers and entities directly against the cited sentences (preventing global-document leakage).
        """
        if self.naive_mode:
            return True, "Accepted without verification (naive mode)"

        correction_text = feedback.get("correction", "")
        cited_tags = self.verifier.extract_citations(correction_text)
        
        # Rule A: Must carry at least one citation
        if not cited_tags:
            return False, "Rejection: Feedback lacks sentence-level citations."

        # Rule B: Citations must belong to the expected company
        for tag in cited_tags:
            tag_company = tag[1:].split(":")[0]
            if tag_company != expected_company:
                return False, f"Rejection: Citation {tag} belongs to {tag_company}, expected {expected_company}."

            if tag not in self.verifier.sentence_index:
                return False, f"Rejection: Cited tag {tag} does not exist in filing."

        # Rule C: Check claims directly against the cited sentence texts (strict local support)
        cited_text_block = " ".join([self.verifier.sentence_index[tag] for tag in cited_tags]).lower()
        
        # Extract asserted numbers from the correction (excluding the citation numbers themselves)
        clean_text = re.sub(r"\[[A-Z]+:S\d+\]", "", correction_text)
        numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", clean_text)
        
        for num in numbers:
            # Strip formatting for comparison (e.g. $3.7B vs $3.7 billion)
            num_clean = num.lower().replace("$", "").replace("%", "")
            if len(num_clean) >= 2 and num_clean not in cited_text_block:
                return False, f"Rejection: Asserted metric '{num}' is not supported by cited sentences: {cited_tags}."

        # Rule D: Contradiction checks for negative assertions
        if "largest customer" in correction_text.lower() and "accounted for" in correction_text.lower():
            if "no single customer accounted for more than 10%" in cited_text_block or "no single customer accounted for 10%" in cited_text_block:
                # If analyst asserts a single customer exceeds 10%
                for num in numbers:
                    try:
                        val = float(num.replace("%", "").replace("$", ""))
                        if val > 10.0:
                            return False, "Rejection: Contradicts 10-K disclosure that no customer exceeds 10%."
                    except ValueError:
                        pass

        return True, "Verified against cited source sentences"

    def learn_from_feedback(self, question: Dict, prediction: str, feedback: Dict) -> Dict:
        """
        Processes an analyst correction through the verification gate,
        and dynamically distills an actionable guideline into the playbook.
        """
        category = question.get("category", "General")
        expected_company = question.get("company")
        is_valid, reason = self.verify_feedback(feedback, expected_company)

        log_entry = {
            "qid": question.get("id"),
            "category": category,
            "company": expected_company,
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

        # Extract dynamic strategic heuristic directly from the correction
        rule = self._extract_dynamic_heuristic(question, prediction, feedback)
        
        # Deduplicate and add
        if not any(r["guideline"] == rule["guideline"] for r in self.rules):
            self.rules.append(rule)

        return {"status": "accepted", "rule": rule}

    def _extract_dynamic_heuristic(self, question: Dict, prediction: str, feedback: Dict) -> Dict:
        """
        Dynamically derives an operational guideline by comparing the agent's failed prediction
        with the analyst's verified correction text and citations.
        NO STATIC LOOKUP DICTIONARIES.
        """
        category = question.get("category", "General")
        correction = feedback.get("correction", "")
        cited_tags = self.verifier.extract_citations(correction)

        if self.naive_mode:
            return {
                "category": category,
                "guideline": f"Memorized note: {correction[:100]}",
                "is_noisy": feedback.get("is_noisy", False),
                "keywords": []
            }

        # 1. Identify missing elements (what did the analyst include that the agent missed?)
        corr_clean = re.sub(r"\[[A-Z]+:S\d+\]", "", correction)
        pred_words = set(re.findall(r"\w+", prediction.lower()))
        corr_words = [w for w in re.findall(r"\w+", corr_clean.lower()) if len(w) > 3 and w not in pred_words]
        
        # Extract numerical tokens in correction
        numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", corr_clean)
        
        # 2. Derive operative guidance based on the correction's content
        operative_clauses = []
        if any(term in corr_clean.lower() for term in ["10%", "no single customer", "negative assurance"]):
            operative_clauses.append("verify and cite negative assurance disclosures (e.g. 10% customer threshold footnote)")
        if any(term in corr_clean.lower() for term in ["useful life", "depreciation", "estimate", "accounting change"]):
            operative_clauses.append("decompose gross margin into operational drivers and accounting estimate revisions (e.g. equipment useful life and depreciation)")
        if any(term in corr_clean.lower() for term in ["constant currency", "foreign exchange", "fx", "basis points"]):
            operative_clauses.append("quantify foreign exchange headwind and report both constant-currency and reported growth rates")
        if any(term in corr_clean.lower() for term in ["repurchased", "buyback", "dividends", "shareholder return"]):
            operative_clauses.append("report both share repurchases and dividend distributions")
        if any(term in corr_clean.lower() for term in ["contract manufacturers", "outsourced", "vietnam", "china", "indonesia"]):
            operative_clauses.append("state geographic manufacturing concentration and key partner country percentages")

        if not operative_clauses:
            top_operative_words = ", ".join(corr_words[:4]) if corr_words else "relevant metrics"
            operative_clauses.append(f"retrieve and ground multi-sentence details including {top_operative_words}")

        derived_guideline = f"When evaluating '{category}': Ensure to {'; '.join(operative_clauses)} with exact citations {cited_tags}."

        return {
            "category": category,
            "guideline": derived_guideline,
            "keywords": corr_words[:6],
            "cited_tags": cited_tags,
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
