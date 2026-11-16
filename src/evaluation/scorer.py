"""
Scorer for diligence answers and human agreement calibration.
Evaluates:
- Citation Precision & Grounding (35%)
- Factuality & Key Fact Coverage (40%)
- Conciseness & Anti-Gaming Penalty (25%)
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
        Scores an agent's answer against the reference answer and ground truth citations.
        Returns a dictionary with subscores and a composite score between 0.0 and 1.0.
        """
        # 1. Citation Grounding & Precision
        comp = ground_truth.get("company")
        cit_eval = self.verifier.verify_citations(prediction, expected_company=comp)
        
        pred_citations = set(cit_eval["valid_citations"])
        gt_citations = set(ground_truth.get("ground_truth_citations", []))
        
        # Citation recall: how many of the needed citations were retrieved?
        cit_recall = len(pred_citations.intersection(gt_citations)) / len(gt_citations) if gt_citations else 1.0
        
        # Citation precision: are the cited sentences actually valid?
        cit_precision = cit_eval["precision"]
        
        # Citation score combines precision and recall
        citation_score = 0.5 * cit_precision + 0.5 * cit_recall
        if not cit_eval["valid"]:
            citation_score *= 0.3

        # 2. Factuality & Key Fact Coverage
        key_facts = ground_truth.get("key_facts", [])
        facts_found = 0
        pred_lower = prediction.lower()
        
        for kf in key_facts:
            # Extract numerical and factual tokens
            kf_tokens = re.findall(r"(\$?\d+(?:\.\d+)?%?|[a-z0-9]+)", kf.lower())
            essential_tokens = [t for t in kf_tokens if len(t) > 2 or any(c.isdigit() for c in t)]
            if not essential_tokens:
                continue
            matched_tokens = sum(1 for t in essential_tokens if t in pred_lower)
            if matched_tokens / len(essential_tokens) >= 0.70:
                facts_found += 1
                
        fact_recall = facts_found / len(key_facts) if key_facts else 1.0

        # 3. Conciseness & Anti-Gaming Penalty
        gaming_penalty = 0.0
        if "not available" in pred_lower or "does not provide" in pred_lower or "cannot be determined" in pred_lower:
            if fact_recall < 0.5:
                # Evasive answer penalty
                gaming_penalty += 0.35
        
        # Citation stuffing penalty (citing > 4 sentences when 1-2 suffice)
        if len(pred_citations) > 4:
            gaming_penalty += 0.20

        # Composite Score (0.0 to 1.0)
        # Weights: 40% Factuality, 35% Citations, 25% Grounding & Non-gaming
        composite = (0.40 * fact_recall) + (0.35 * citation_score) + (0.25 * max(0.0, 1.0 - gaming_penalty))
        composite = max(0.0, min(1.0, composite))

        return {
            "composite_score": round(composite, 4),
            "fact_recall": round(fact_recall, 4),
            "citation_score": round(citation_score, 4),
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

