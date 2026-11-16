"""
Composite Diligence Scorer with Grounded Citation Verification.

Calculates multi-dimensional diligence quality:
1. Citation Recall & Precision (25% weight): Ground-truth citation alignment and tag validity.
2. Semantic Claim-to-Citation Support (25% weight): Verifies that numbers and assertions in
   each claim clause are strictly supported by the cited sentence.
3. Factual & Numerical Accuracy (30% weight): Verifies key financial facts, percentages,
   dollar amounts, and directional changes against reference data.
4. Anti-Gaming & Conciseness Penalty (20% weight): Penalizes citation stuffing, hallucinated tags,
   unsupported assertions, and evasive hedging.
"""

import math
import re
from typing import Dict, List, Tuple
from src.signals.citation_verifier import CitationVerifier

class DiligenceScorer:
    def __init__(self, verifier: CitationVerifier):
        self.verifier = verifier

    def score_answer(self, prediction: str, ground_truth: Dict) -> Dict:
        """
        Evaluates a predicted diligence answer against ground-truth facts and citations.
        Returns composite score (0.0 to 1.0) and granular sub-metrics.
        """
        cit_eval = self.verifier.verify_citations(prediction, ground_truth.get("company"))
        pred_citations = set(cit_eval["citations"])
        gt_citations = set(ground_truth.get("ground_truth_citations", []))

        # 1. Citation Recall & Precision
        cit_recall = len(pred_citations.intersection(gt_citations)) / len(gt_citations) if gt_citations else 1.0
        cit_precision = cit_eval["precision"]
        base_citation_score = (0.5 * cit_precision) + (0.5 * cit_recall)
        if not cit_eval["valid"]:
            base_citation_score *= 0.2

        # 2. Semantic Claim-to-Citation Grounding Support
        # Verifies that every asserted claim clause is strictly substantiated by its cited sentence
        supported_cits = 0
        claim_support_precision = 0.0
        
        if pred_citations:
            for cit in pred_citations:
                # Find the sentence clause containing or directly preceding this citation
                pattern = rf"([^.!?\n]*?{re.escape(cit)})"
                matches = re.findall(pattern, prediction)
                claim_clause = matches[0] if matches else prediction
                
                # Centralized semantic verification: enforces all numbers and directional consistency
                if self.verifier.check_claim_support(claim_clause, cit):
                    supported_cits += 1
            
            claim_support_precision = supported_cits / len(pred_citations)
        else:
            claim_support_precision = 0.0

        # 3. Factual & Numerical Accuracy
        key_facts = ground_truth.get("key_facts", [])
        facts_found = 0
        pred_lower = prediction.lower()
        
        for kf in key_facts:
            # Check numerical tokens first
            kf_numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", kf)
            num_matched = True
            if kf_numbers:
                num_matched = any(num.lower().replace("$", "").replace("%", "") in pred_lower for num in kf_numbers)
            
            # Check informative words
            kf_words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", kf.lower())]
            word_matched = True
            if kf_words:
                matched_words = sum(1 for w in kf_words if w in pred_lower)
                word_matched = (matched_words / len(kf_words)) >= 0.40
                
            if num_matched and word_matched:
                facts_found += 1
                
        fact_recall = facts_found / len(key_facts) if key_facts else 1.0

        # 4. Anti-Gaming & Conciseness Penalties
        gaming_penalty = 0.0
        
        # Penalize evasive hedging when fact is absent
        if any(h in pred_lower for h in ["not available", "does not provide", "cannot be determined"]):
            if fact_recall < 0.5:
                gaming_penalty += 0.35
        
        # Penalize citation stuffing (> 3 citations)
        if len(pred_citations) > 3:
            gaming_penalty += 0.20

        # Penalize ungrounded citations (citing sentences that do not support the claim)
        if pred_citations and claim_support_precision < 0.5:
            gaming_penalty += 0.30

        # Penalize invalid citations
        if not cit_eval["valid"]:
            gaming_penalty += 0.25

        # 5. Composite Score Calculation
        raw_score = (
            (0.25 * base_citation_score) +
            (0.25 * claim_support_precision) +
            (0.30 * fact_recall) +
            (0.20 * max(0.0, 1.0 - gaming_penalty))
        )
        
        composite_score = max(0.0, min(1.0, raw_score))

        return {
            "composite_score": round(composite_score, 4),
            "citation_recall": round(cit_recall, 4),
            "citation_precision": round(cit_precision, 4),
            "claim_support_precision": round(claim_support_precision, 4),
            "fact_recall": round(fact_recall, 4),
            "gaming_penalty": round(gaming_penalty, 4),
            "valid_citations": cit_eval["valid"]
        }

    def calibrate_with_human_judgments(self, calibration_dataset: List[Dict]) -> Dict:
        """
        Calculates Pearson correlation and Mean Absolute Error (MAE)
        between automated scorer composite scores and human expert scores.
        """
        human_scores = []
        automated_scores = []

        for item in calibration_dataset:
            pred = item["prediction"]
            gt = item["ground_truth"]
            h_score = item["human_score"]

            eval_res = self.score_answer(pred, gt)
            auto_score = eval_res["composite_score"]

            human_scores.append(h_score)
            automated_scores.append(auto_score)

        n = len(human_scores)
        mean_h = sum(human_scores) / n
        mean_a = sum(automated_scores) / n

        numerator = sum((h - mean_h) * (a - mean_a) for h, a in zip(human_scores, automated_scores))
        denom_h = math.sqrt(sum((h - mean_h) ** 2 for h in human_scores))
        denom_a = math.sqrt(sum((a - mean_a) ** 2 for a in automated_scores))

        pearson_r = numerator / (denom_h * denom_a) if denom_h > 0 and denom_a > 0 else 0.0
        mae = sum(abs(h - a) for h, a in zip(human_scores, automated_scores)) / n

        return {
            "pearson_correlation": round(pearson_r, 4),
            "mean_absolute_error": round(mae, 4),
            "n_samples": n
        }
