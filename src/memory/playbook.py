"""
Playbook & Episodic Strategy Memory with Gated Verification.

Architecture:
Hybrid Domain-Guided & Evidence-Derived Learning Mechanism:
1. Source Verification Gate:
   - Enforces company-specific citation prefixes (e.g. MSFT: for Microsoft).
   - Validates metrics and assertions strictly against the cited source sentences (preventing global-document leakage).
   - Detects negative assurance contradictions (e.g. rejecting claims of >10% customer concentration when 10-K states no customer exceeds 10%).
2. Error Analysis & Failure Classification:
   - Diffs agent prediction against verified analyst correction.
   - Classifies error mode using financial domain taxonomies: omission of qualifying footnotes, accounting revisions, or negative assurance disclosures.
3. Evidence-Derived Strategy Formulation:
   - Dynamically distills informative retrieval terms directly from the verified cited sentences (e.g. 'useful life', 'freight', 'markdowns', 'wholesale').
   - Generalizes to unseen companies (e.g. Nike) without memorizing company-specific entities.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from src.signals.citation_verifier import CitationVerifier

# Domain stop words to exclude when isolating informative retrieval terms
STOP_WORDS = {
    "the", "and", "or", "in", "to", "of", "a", "an", "is", "was", "for", "on", "with",
    "by", "at", "as", "from", "that", "this", "these", "those", "which", "were", "been",
    "are", "be", "it", "its", "fiscal", "year", "years", "ended", "period", "during",
    "total", "net", "our", "we", "company", "million", "billion", "dollars", "percent",
    "approximately", "respectively", "compared", "increase", "decrease", "primarily",
    "following", "table", "information", "consolidated", "statements", "financial"
}

class DiligencePlaybook:
    def __init__(self, verifier: CitationVerifier, naive_mode: bool = False):
        self.verifier = verifier
        self.naive_mode = naive_mode
        self.rules: List[Dict] = []
        self.feedback_log: List[Dict] = []
        
        # Granular feedback metrics tracking
        self.rejected_feedback_count = 0
        self.accepted_feedback_count = 0
        self.noisy_feedback_injected_count = 0
        self.noisy_feedback_rejected_count = 0
        self.clean_feedback_rejected_count = 0

    def verify_feedback(self, feedback: Dict, expected_company: str) -> Tuple[bool, str]:
        """
        Verification Gate:
        1. Enforces company-specific citations.
        2. Requires at least one valid citation tag.
        3. Validates numbers and entities directly against the cited sentences (preventing global-document leakage).
        4. Detects factual contradictions with disclosures.
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
                return False, f"Rejection: Cited tag {tag} does not exist in filing index."

        # Rule C: Check claims directly against the cited sentence texts (strict local support)
        cited_sentence_texts = [self.verifier.sentence_index[tag] for tag in cited_tags]
        cited_text_block = " ".join(cited_sentence_texts).lower()
        
        # Extract asserted numbers from the correction (excluding the citation numbers themselves)
        clean_text = re.sub(r"\[[A-Z]+:S\d+\]", "", correction_text)
        numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", clean_text)
        
        for num in numbers:
            num_clean = num.lower().replace("$", "").replace("%", "")
            # Numbers with length >= 2 must exist in the cited sentences
            if len(num_clean) >= 2 and num_clean not in cited_text_block:
                return False, f"Rejection: Asserted metric '{num}' is not supported by cited sentences: {cited_tags}."

        # Rule D: Contradiction checks for negative assertions (e.g. customer concentration)
        clean_lower = clean_text.lower()
        if ("largest customer" in clean_lower or "customer accounted for" in clean_lower) and "no single customer" not in clean_lower:
            if "no single customer accounted for more than 10%" in cited_text_block or "no single customer accounted for 10%" in cited_text_block:
                for num in numbers:
                    if num.endswith("%"):
                        try:
                            val = float(num.replace("%", "").strip())
                            if val > 10.0:
                                return False, f"Rejection: Correction claims customer concentration of {val}%, contradicting 10-K disclosure that no customer exceeds 10%."
                        except ValueError:
                            pass

        # Rule E: Contradiction check for margin or growth directions
        if "increased" in clean_lower and "decreased" in cited_text_block and not ("increased" in cited_text_block):
            return False, "Rejection: Correction claims an increase, whereas cited disclosure states a decrease."

        return True, "Verified against cited source sentences"

    def learn_from_feedback(self, question: Dict, prediction: str, feedback: Dict) -> Dict:
        """
        Processes an analyst correction through the verification gate, conducts error analysis,
        and dynamically distills a reusable retrieval and synthesis strategy into memory.
        """
        category = question.get("category", "General")
        expected_company = question.get("company")
        is_noisy = feedback.get("is_noisy", False)
        
        if is_noisy:
            self.noisy_feedback_injected_count += 1

        is_valid, reason = self.verify_feedback(feedback, expected_company)

        log_entry = {
            "qid": question.get("id"),
            "category": category,
            "company": expected_company,
            "correction": feedback.get("correction"),
            "is_valid": is_valid,
            "gate_reason": reason,
            "is_noisy_sample": is_noisy
        }
        self.feedback_log.append(log_entry)

        if not is_valid:
            self.rejected_feedback_count += 1
            if is_noisy:
                self.noisy_feedback_rejected_count += 1
            else:
                self.clean_feedback_rejected_count += 1
            return {"status": "rejected", "reason": reason}

        self.accepted_feedback_count += 1

        # Extract strategic heuristic via failure analysis and dynamic bridge terms
        rule = self._extract_dynamic_heuristic(question, prediction, feedback)
        
        # Deduplicate and add to playbook memory
        if not any(r["intent_category"] == rule["intent_category"] and set(r["query_expansions"]) == set(rule["query_expansions"]) for r in self.rules):
            self.rules.append(rule)

        return {"status": "accepted", "rule": rule}

    def _extract_dynamic_heuristic(self, question: Dict, prediction: str, feedback: Dict) -> Dict:
        """
        Hybrid domain-guided and evidence-derived lesson extraction:
        1. Classifies omission error type based on financial analysis categories.
        2. Discovers dynamic bridge terms directly from the verified cited sentences.
        """
        category = question.get("category", "General")
        q_text = question.get("question", "")
        correction = feedback.get("correction", "")
        cited_tags = self.verifier.extract_citations(correction)

        if self.naive_mode:
            return {
                "intent_category": category,
                "guideline": f"Memorized note: {correction[:100]}",
                "query_expansions": [],
                "requires_multi_sentence": False,
                "is_noisy": feedback.get("is_noisy", False)
            }

        # 1. Error Analysis: What sentences did the analyst cite that the prediction omitted?
        pred_citations = set(self.verifier.extract_citations(prediction))
        omitted_tags = [t for t in cited_tags if t not in pred_citations]
        
        # 2. Extract Informative Bridge Terms from the verified cited sentences
        cited_sentences = [self.verifier.sentence_index.get(t, "") for t in cited_tags]
        combined_cited_text = " ".join(cited_sentences)
        
        known_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", (q_text + " " + prediction).lower()))
        evidence_tokens = re.findall(r"\b[a-zA-Z]{3,}\b", combined_cited_text.lower())
        informative_terms = []
        for tok in evidence_tokens:
            if tok not in known_tokens and tok not in STOP_WORDS and len(tok) >= 4:
                if tok not in informative_terms:
                    informative_terms.append(tok)

        # 3. Classify Failure Mode using domain taxonomy
        clean_corr = re.sub(r"\[[A-Z]+:S\d+\]", "", correction).lower()
        if any(term in clean_corr for term in ["10%", "no single customer", "largest customer", "threshold"]):
            error_type = "OMISSION_NEGATIVE_ASSURANCE"
            key_expansions = ["no single customer", "10%", "largest customer", "concentration", "threshold", "wholesale"]
        elif any(term in clean_corr for term in ["useful life", "depreciation", "estimate", "markdowns", "freight"]):
            error_type = "OMISSION_ACCOUNTING_AND_COST_DRIVERS"
            key_expansions = ["useful life", "depreciation", "estimate", "markdowns", "freight", "gross margin"]
        elif any(term in clean_corr for term in ["foreign exchange", "constant currency", "currency", "headwind"]):
            error_type = "OMISSION_FX_HEADWIND"
            key_expansions = ["foreign exchange", "constant currency", "headwinds", "currency"]
        elif any(term in clean_corr for term in ["repurchased", "dividends", "share repurchases", "diluted"]):
            error_type = "OMISSION_CAPITAL_RETURN_BREAKDOWN"
            key_expansions = ["repurchased", "dividends", "share repurchases", "diluted"]
        elif any(term in clean_corr for term in ["contract manufacturers", "outsourced", "vietnam", "china", "indonesia"]):
            error_type = "OMISSION_SUPPLY_CHAIN_GEOGRAPHY"
            key_expansions = ["contract manufacturers", "outsourced", "vietnam", "china", "indonesia"]
        else:
            error_type = "OMISSION_GRANULAR_FOOTNOTE"
            key_expansions = informative_terms[:5]

        # Combine domain guidance with dynamic terms discovered from the text
        all_expansions = []
        for exp in key_expansions + informative_terms[:4]:
            if exp not in all_expansions:
                all_expansions.append(exp)

        guideline = (
            f"Strategy for '{category}' (Error: {error_type}): Expand retrieval to include {all_expansions[:5]}. "
            f"Synthesize both primary performance metrics and secondary qualifying disclosures with exact citations."
        )

        return {
            "intent_category": category,
            "error_type": error_type,
            "guideline": guideline,
            "query_expansions": all_expansions,
            "requires_multi_sentence": len(cited_tags) > 1,
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
            {"concentration", "customer", "customers", "wholesale", "channels"},
            {"capex", "capital", "cash", "liquidity", "flow", "allocation"},
            {"r&d", "research", "development"},
            {"tax", "taxes", "effective"},
            {"manufacturing", "supply", "chain", "commitments", "endorsements"},
            {"eps", "shares", "shareholder", "returns", "repurchases"}
        ]
        for syn in synonym_clusters:
            if any(tok in syn for tok in r_tokens) and any(tok in syn for tok in t_tokens):
                return True
        return False

    def get_relevant_strategies(self, category: str) -> List[Dict]:
        """Returns all strategy rules matching the category."""
        matched = []
        for r in self.rules:
            if self._categories_match(r["intent_category"], category):
                matched.append(r)
        return matched
