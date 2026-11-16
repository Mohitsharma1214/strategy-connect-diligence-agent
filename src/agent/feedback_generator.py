"""
Simulates scarce analyst feedback on deals, with configurable noise rate (default 20%).
Includes realistic human analyst corrections and realistic noisy/incorrect corrections.
"""

import random
from typing import Dict, List, Optional

# Realistic noisy corrections (factual errors, hallucinated metrics, or invalid tags)
NOISY_CORRECTIONS_POOL = [
    {
        "correction": "Azure growth was actually 42% according to internal sell-side reports. [MSFT:S999]",
        "is_noisy": True,
        "reason": "Hallucinated metric and invalid citation tag [MSFT:S999]."
    },
    {
        "correction": "Amazon is Microsoft's largest customer accounting for 18% of revenue. [MSFT:S001]",
        "is_noisy": True,
        "reason": "Factually incorrect: no single customer accounts for >10%."
    },
    {
        "correction": "Apple's Mac revenue increased by 15% due to enterprise M2 adoption. [AAPL:S888]",
        "is_noisy": True,
        "reason": "Directly contradicts 10-K: Mac revenue fell 27%."
    },
    {
        "correction": "Gross margin contracted because marketing expenses surged 40%. [NKE:S777]",
        "is_noisy": True,
        "reason": "Factual error: gross margin was driven by inventory markdowns and freight."
    },
    {
        "correction": "Cellular carriers accounted for 25% of Apple net sales in fiscal 2023. [AAPL:S024]",
        "is_noisy": True,
        "reason": "Factually incorrect: no customer accounted for 10% or more."
    }
]

class FeedbackSimulator:
    def __init__(self, noise_rate: float = 0.20, seed: int = 42):
        self.noise_rate = noise_rate
        self.rng = random.Random(seed)

    def generate_feedback_batch(
        self,
        questions: List[Dict],
        predictions: Dict[str, str],
        batch_size: int = 5
    ) -> List[Dict]:
        """
        Samples a handful (batch_size) of corrections on the training set.
        Injects noisy feedback with probability `noise_rate`.
        """
        # Select questions to provide feedback on
        selected_questions = self.rng.sample(questions, min(batch_size, len(questions)))
        feedback_items = []

        for q in selected_questions:
            qid = q["id"]
            pred = predictions.get(qid, "")
            
            # Decide if this correction will be noisy (approx 1 in 5, or 20%)
            is_noisy = self.rng.random() < self.noise_rate

            if is_noisy:
                noisy_item = self.rng.choice(NOISY_CORRECTIONS_POOL)
                feedback = {
                    "question_id": qid,
                    "question": q,
                    "prediction": pred,
                    "correction": noisy_item["correction"],
                    "is_noisy": True,
                    "noise_reason": noisy_item["reason"]
                }
            else:
                # Valid analyst correction providing ground truth insight
                ref = q["reference_answer"]
                cits = " ".join(q.get("ground_truth_citations", []))
                correction_text = f"Correction: The complete answer is: {ref} {cits}"
                feedback = {
                    "question_id": qid,
                    "question": q,
                    "prediction": pred,
                    "correction": correction_text,
                    "is_noisy": False,
                    "noise_reason": None
                }

            feedback_items.append(feedback)

        return feedback_items

