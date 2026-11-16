"""
Scorer for diligence answers and human agreement calibration.
Evaluates:
- Factuality & Key Fact Coverage (35%)
- Citation Recall & Precision (20%)
- Semantic Claim-to-Citation Grounding Support (25%)
- Conciseness & Anti-Gaming Penalty (20%)
"""

import re
from typing import Dict, List
import numpy as np
from src.signals.citation_verifier import CitationVerifier

class DiligenceScorer:
    def __init__(self, verifier: CitationVerifier):
        self.verifier = verifier

    def score_answer(self, prediction: str, ground_truth: Dict) -> Dict:
        """
        Scores an agent's answer against reference answers, ground truth citations,
        and verifies that each claim is semantically grounded by its cited source sentence.
        """
        comp = ground_truth.get("company")
        cit_eval = self.verifier.verify_citations(prediction, expected_company=comp)
        
        pred_citations = set(cit_eval["valid_citations"])
        gt_citations = set(ground_truth.get("ground_truth_citations", []))
        
        # 1. Citation Recall & Precision
        cit_recall = len(pred_citations.intersection(gt_citations)) / len(gt_citations) if gt_citations else 1.0
        cit_precision = cit_eval["precision"]
        base_citation_score = (0.5 * cit_precision) + (0.5 * cit_recall)
        if not cit_eval["valid"]:
            base_citation_score *= 0.3

        # 2. Semantic Claim-to-Citation Grounding Support
        # Verifies that each citation actually supports the claim it is attached to (closes the loophole!)
        supported_cits = 0
        claim_support_precision = 0.0
        
        if pred_citations:
            for cit in pred_citations:
                source_sentence = self.verifier.sentence_index.get(cit, "").lower()
                # Find the sentence clause containing or directly preceding this citation
                pattern = rf"([^.!?\n]*?{re.escape(cit)})"
                matches = re.findall(pattern, prediction)
                claim_clause = matches[0] if matches else prediction
                
                # Extract key numbers, percentages, and entities from that claim clause
                claim_clean = re.sub(r"\[[A-Z]+:S\d+\]", "", claim_clause)
                claim_numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", claim_clean)
                claim_entities = [w for w in re.findall(r"\w+", claim_clean.lower()) if len(w) > 4]
                
                # Check support: numbers must match source, or major entities must overlap
                numbers_supported = True
                if claim_numbers:
                    numbers_supported = any(num.lower().replace("$", "").replace("%", "") in source_sentence for num in claim_numbers)
                
                entities_supported = True
                if claim_entities:
                    matched_ent = sum(1 for e in claim_entities if e in source_sentence)
                    entities_supported = (matched_ent / len(claim_entities)) >= 0.35
                
                if numbers_supported and entities_supported:
                    supported_cits += 1
            
            claim_support_precision = supported_cits / len(pred_citations)

        # 3. Factuality & Key Fact Coverage
        key_facts = ground_truth.get("key_facts", [])
        facts_found = 0
        pred_lower = prediction.lower()
        
        for kf in key_facts:
            kf_tokens = re.findall(r"(\$?\d+(?:\.\d+)?%?|[a-z0-9]+)", kf.lower())
            essential_tokens = [t for t in kf_tokens if len(t) > 2 or any(c.isdigit() for c in t)]
            if not essential_tokens:
                continue
            matched_tokens = sum(1 for t in essential_tokens if t in pred_lower)
            if matched_tokens / len(essential_tokens) >= 0.70:
                facts_found += 1
                
        fact_recall = facts_found / len(key_facts) if key_facts else 1.0

        # 4. Conciseness & Anti-Gaming Penalty
        gaming_penalty = 0.0
        if "not available" in pred_lower or "does not provide" in pred_lower or "cannot be determined" in pred_lower:
            if fact_recall < 0.5:
                gaming_penalty += 0.35
        
        # Citation stuffing penalty (citing > 4 sentences when 1-2 suffice)
        if len(pred_citations) > 4:
            gaming_penalty += 0.25

        # If claims are not supported by their cited sentences, penalize heavily
        if pred_citations and claim_support_precision < 0.5:
            gaming_penalty += 0.30

        # Composite Score (0.0 to 1.0)
        # 35% Factuality, 20% Citation Presence, 25% Semantic Claim Support, 20% Non-Gaming
        composite = (
            (0.35 * fact_recall) +
            (0.20 * base_citation_score) +
            (0.25 * claim_support_precision) +
            (0.20 * max(0.0, 1.0 - gaming_penalty))
        )
        composite = max(0.0, min(1.0, composite))

        return {
            "composite_score": round(composite, 4),
            "fact_recall": round(fact_recall, 4),
            "citation_score": round(base_citation_score, 4),
            "claim_support_precision": round(claim_support_precision, 4),
            "cit_precision": round(cit_precision, 4),
            "cit_recall": round(cit_recall, 4),
            "gaming_penalty": round(gaming_penalty, 4),
            "valid_citations": list(pred_citations),
            "invalid_citations": cit_eval["invalid_citations"]
        }

    def calibrate_with_human_judgments(self, sample_pairs: List[Dict]) -> Dict:
        """
        Computes Pearson correlation and Mean Absolute Error between automated scores and human expert scores.
        """
        auto_scores = []
        human_scores = []
        
        for item in sample_pairs:
            auto_res = self.score_answer(item["prediction"], item["ground_truth"])
            auto_scores.append(auto_res["composite_score"])
            human_scores.append(item["human_score"])
            
        auto_arr = np.array(auto_scores)
        human_arr = np.array(human_scores)
        
        corr = float(np.corrcoef(auto_arr, human_arr)[0, 1])
        mae = float(np.mean(np.abs(auto_arr - human_arr)))
        
        return {
            "pearson_correlation": round(corr, 4),
            "mean_absolute_error": round(mae, 4),
            "n_samples": len(sample_pairs)
        }
