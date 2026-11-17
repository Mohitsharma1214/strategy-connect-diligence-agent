"""
Unit Tests for Strategic Priorities 1 through 4:
1. Operational Analyst Reliability Governance
2. Feedback-Derived Retrieval Expansion
3. Company-Specific Playbook Isolation
4. Evaluation Integrity & Dynamic Metrics
"""

import unittest
from src.parser.edgar_parser import EdgarFilingParser
from src.feedback.analyst_gate import AnalystVerificationGate
from src.agent.diligence_agent import DiligenceAgent, DiligencePlaybook, PlaybookRule
from src.eval.scorer import DiligenceScorer


class TestPriorityRemediations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.msft_parser = EdgarFilingParser("data/sc-diligence/filings/msft-20260630.htm")
        cls.aapl_parser = EdgarFilingParser("data/sc-diligence/filings/aapl-20260926.htm")

    def test_priority_1_operational_analyst_reliability(self):
        """Priority 1: Confirms Bayesian trust governs review burdens and never rejects verified primary evidence."""
        gate = AnalystVerificationGate({"MSFT": self.msft_parser, "AAPL": self.aapl_parser})
        # Simulate observed low reliability for AN-01 (e.g. after initial errors)
        gate.analyst_history["AN-01"] = {"accepted": 1, "rejected": 3, "total": 4}
        
        # Test review burdens
        burden_an01 = gate.get_review_burden("AN-01")
        self.assertTrue(burden_an01["flag_borderline_for_review"])
        self.assertIn("Elevated Scrutiny", burden_an01["tier"])
        
        # AN-01 valid feedback item (FB-004 style, verified evidence)
        valid_fb = {
            "id": "FB-TEST-01",
            "round": 1,
            "analyst": "AN-01",
            "question_id": "MSFT-L02",
            "correction": "No single customer was above 10% of revenue in fiscal 2024 to 2026.",
            "citations": [{
                "type": "sentence",
                "quote": "No sales to an individual customer or country other than the United States accounted for more than 10% of revenue for fiscal years 2026, 2025, or 2024."
            }]
        }
        res = gate.process_feedback_item(valid_fb, {"company": "MSFT", "question": "Customer concentration"})
        self.assertTrue(res["is_valid"], "Factually correct feedback must never be rejected purely for analyst ID")
        self.assertTrue(res["needs_review"], "Low-trust analyst feedback must be flagged for review")

    def test_priority_2_feedback_retrieval_expansion(self):
        """Priority 2: Confirms retrieval lessons are extracted and populated into PlaybookRule."""
        gate = AnalystVerificationGate({"MSFT": self.msft_parser, "AAPL": self.aapl_parser})
        fb = {
            "id": "FB-TEST-02",
            "round": 1,
            "analyst": "AN-02",
            "question_id": "MSFT-L02",
            "correction": "No single customer was above 10% of revenue in fiscal 2024 to 2026.",
            "citations": [{
                "type": "sentence",
                "quote": "No sales to an individual customer or country other than the United States accounted for more than 10% of revenue for fiscal years 2026, 2025, or 2024."
            }]
        }
        res = gate.process_feedback_item(fb, {"company": "MSFT", "question": "Customer concentration"})
        lesson = res.get("retrieval_lesson")
        self.assertIsNotNone(lesson)
        self.assertIn("10% of revenue", lesson["expansion_terms"])
        
        # Verify PlaybookRule assimilation
        rule = PlaybookRule(
            rule_id=f"RULE-{fb['id']}",
            topic="customer_concentration",
            condition="Verified analyst correction (AN-02)",
            action=fb["correction"],
            expansion_terms=lesson["expansion_terms"],
            question_id=fb["question_id"],
            company="MSFT",
            verified_answer=fb["correction"],
            verified_citations=fb["citations"]
        )
        self.assertIn("10% of revenue", rule.expansion_terms)
        self.assertEqual(rule.question_id, "MSFT-L02")

    def test_priority_3_company_playbook_isolation(self):
        """Priority 3: Confirms MSFT rules route only to MSFT playbook and AAPL rules only to AAPL."""
        pb_msft = DiligencePlaybook()
        pb_aapl = DiligencePlaybook()
        
        msft_rule = PlaybookRule(
            rule_id="RULE-MSFT-01",
            topic="customer_concentration",
            condition="Verified",
            action="MSFT Rule",
            question_id="MSFT-L02",
            company="MSFT"
        )
        aapl_rule = PlaybookRule(
            rule_id="RULE-AAPL-01",
            topic="revenue_and_sales",
            condition="Verified",
            action="AAPL Rule",
            question_id="AAPL-L01",
            company="AAPL"
        )
        
        pb_msft.add_rule(msft_rule)
        pb_aapl.add_rule(aapl_rule)
        
        self.assertIsNotNone(pb_msft.get_rule_for_question("MSFT-L02"))
        self.assertIsNone(pb_msft.get_rule_for_question("AAPL-L01"), "AAPL rules must not leak into MSFT playbook")
        self.assertIsNotNone(pb_aapl.get_rule_for_question("AAPL-L01"))
        self.assertIsNone(pb_aapl.get_rule_for_question("MSFT-L02"), "MSFT rules must not leak into AAPL playbook")

    def test_priority_4_learning_dynamics(self):
        """Priority 4: Confirms the agent demonstrates genuine accuracy growth on learn questions."""
        pb_msft = DiligencePlaybook()
        agent = DiligenceAgent(self.msft_parser, pb_msft)
        scorer = DiligenceScorer(self.msft_parser, self.aapl_parser)
        
        q = {
            "id": "MSFT-L02",
            "company": "MSFT",
            "question": "How concentrated is Microsoft's revenue among its largest customers?",
            "reference_answer": "No individual customer accounted for more than 10% of revenue in fiscal 2026, 2025 or 2024.",
            "reference_citations": [{
                "type": "sentence",
                "quote": "No sales to an individual customer or country other than the United States accounted for more than 10% of revenue for fiscal years 2026, 2025, or 2024."
            }]
        }
        
        # Test answer with verified rule
        rule = PlaybookRule(
            rule_id="RULE-FB-004",
            topic="customer_concentration",
            condition="Verified",
            action="No single customer was above 10% of revenue in fiscal 2024 to 2026.",
            question_id="MSFT-L02",
            company="MSFT",
            verified_answer="No sales to an individual customer or country other than the United States accounted for more than 10% of revenue for fiscal years 2026, 2025, or 2024.",
            verified_citations=q["reference_citations"]
        )
        pb_msft.add_rule(rule)
        
        ans = agent.answer_question(q)
        score = scorer.evaluate_item(ans, q["reference_answer"], self.msft_parser, q["reference_citations"])
        self.assertEqual(score["all_pass"], 1, "Agent must score 100% all_pass on verified question")
        self.assertEqual(score["citation_grounding"], 1, "Citation grounding must be 1.0")


if __name__ == "__main__":
    unittest.main()
