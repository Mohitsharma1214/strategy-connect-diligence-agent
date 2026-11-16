"""
Simulates scarce analyst feedback on deals, with configurable noise rate (default 20%).
Includes realistic human analyst corrections and realistic noisy/incorrect corrections.
Strictly MSFT and AAPL - zero Nike references to ensure complete unseen isolation.
"""

import random
import re
from typing import Dict, List, Optional

# Realistic noisy corrections (factual errors, hallucinated metrics, or invalid tags)
# Strictly MSFT & AAPL to prevent any unseen company leakage in the training pool.
NOISY_CORRECTIONS_POOL = [
    {
        "correction": "Azure revenue grew 42% according to internal sell-side reports. [MSFT:S999]",
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
        "correction": "Cellular carriers accounted for 25% of Apple net sales in fiscal 2023. [AAPL:S024]",
        "is_noisy": True,
        "reason": "Factually incorrect: no customer accounted for 10% or more."
    },
    {
        "correction": "Microsoft's server useful life was shortened to 3 years, increasing depreciation expense by $2.5B. [MSFT:S025]",
        "is_noisy": True,
        "reason": "Factual inversion: useful life was extended to 6 years, decreasing depreciation."
    },
    {
        "correction": "Apple's Services gross margin contracted by 400 basis points due to App Store headwinds. [AAPL:S013]",
        "is_noisy": True,
        "reason": "Unsupported claim: Services gross margin expanded."
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
        Samples a scarce batch (batch_size=5) of corrections on the training set.
        Injects noisy feedback with probability `noise_rate` (default 20%).
        """
        selected_questions = self.rng.sample(questions, min(batch_size, len(questions)))
        feedback_items = []

        for q in selected_questions:
            qid = q["id"]
            pred = predictions.get(qid, "")
            
            # Decide if this correction is noisy
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
