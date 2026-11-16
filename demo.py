#!/usr/bin/env python3
"""
Interactive Diligence Agent Terminal Demo.
Allows users/reviewers to:
1. Select a company (MSFT, AAPL, NKE).
2. Ask diligence questions and see sentence-level citations.
3. Inspect active Playbook rules.
4. Submit custom analyst corrections and watch the Verification Gate in real-time.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.signals.citation_verifier import CitationVerifier
from src.memory.playbook import DiligencePlaybook
from src.agent.diligence_agent import DiligenceAgent
from src.evaluation.scorer import DiligenceScorer

def main():
    print("=" * 65)
    print("   STRATEGYCONNECT DILIGENCE AGENT - INTERACTIVE DEMO   ")
    print("=" * 65)

    # 1. Load filings
    filings = {}
    filings_dir = os.path.join(BASE_DIR, "data/filings")
    for fname, comp in [("msft_10k_2023.txt", "MSFT"), ("aapl_10k_2023.txt", "AAPL"), ("nke_10k_2023.txt", "NKE")]:
        with open(os.path.join(filings_dir, fname), "r") as f:
            filings[comp] = f.read()

    with open(os.path.join(BASE_DIR, "data/questions.json"), "r") as f:
        all_questions = json.load(f)

    verifier = CitationVerifier(filings)
    playbook = DiligencePlaybook(verifier, naive_mode=False)
    agent = DiligenceAgent(filings, verifier, playbook=playbook)
    scorer = DiligenceScorer(verifier)

    print("\n[System Initialized]: 3 Filings Loaded (109 Sentences Indexed).")
    print("Playbook is currently active with Epistemic Verification Gate ON.\n")

    while True:
        print("-" * 65)
        print("Choose an action:")
        print("  1. Ask a question on Microsoft (MSFT)")
        print("  2. Ask a question on Apple (AAPL)")
        print("  3. Ask a question on Nike (NKE - UNSEEN Company)")
        print("  4. View active Playbook Rules")
        print("  5. Submit custom feedback / test the 20% Noise Filter")
        print("  6. Exit")
        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "6":
            print("\nExiting interactive demo. Thank you!")
            break

        elif choice in ["1", "2", "3"]:
            comp_map = {"1": "MSFT", "2": "AAPL", "3": "NKE"}
            comp = comp_map[choice]
            comp_qs = [q for q in all_questions if q["company"] == comp]
            print(f"\nSelect a diligence question for {comp}:")
            for i, q in enumerate(comp_qs[:5], 1):
                print(f"  {i}. [{q['category']}] {q['question']}")

            q_idx = input(f"\nSelect question (1-{min(5, len(comp_qs))}): ").strip()
            try:
                selected_q = comp_qs[int(q_idx) - 1]
            except Exception:
                selected_q = comp_qs[0]

            print(f"\n[QUERYING DILIGENCE AGENT]...")
            print(f"Question: {selected_q['question']}")
            
            # Answer question
            res = agent.answer_question(selected_q)
            print(f"\n[AGENT ANSWER] ({res['mode']} mode):")
            print(f"> {res['answer']}")
            
            # Score answer
            eval_res = scorer.score_answer(res["answer"], selected_q)
            print(f"\n[EVALUATION SCORE]: {eval_res['composite_score'] * 100:.1f} / 100")
            print(f"  • Factuality Recall: {eval_res['fact_recall'] * 100:.1f}%")
            print(f"  • Valid Citations:   {eval_res['valid_citations']}")
            if eval_res['invalid_citations']:
                print(f"  • Invalid Citations: {eval_res['invalid_citations']}")

        elif choice == "4":
            print("\n[ACTIVE PLAYBOOK RULES]:")
            if not playbook.rules:
                print("  (Playbook is currently empty. Rules are learned when feedback is submitted.)")
            else:
                for i, r in enumerate(playbook.rules, 1):
                    print(f"  {i}. [{r['category']}]: {r['guideline']}")
            print(f"\nTotal Feedback Processed: {playbook.accepted_feedback_count} accepted, {playbook.rejected_feedback_count} rejected.")

        elif choice == "5":
            print("\n[TEST THE REAL-TIME FEEDBACK GATE]")
            print("You can submit a correction to test how the gate accepts valid data and rejects noisy data.")
            print("Examples:")
            print("  • Valid: 'No single customer accounted for >10%. [MSFT:S030]'")
            print("  • Noisy/Fake tag: 'Azure grew 42% [MSFT:S999]'")
            print("  • Noisy/Fake number: 'Amazon is top customer with 18% share [MSFT:S001]'")
            
            fb_text = input("\nEnter feedback correction text: ").strip()
            if not fb_text:
                fb_text = "No single customer accounted for >10%. [MSFT:S030]"

            test_q = {"id": "CUSTOM_01", "category": "Customer Concentration", "company": "MSFT"}
            print(f"\nEvaluating feedback through Verification Gate...")
            fb_dict = {"correction": fb_text, "is_noisy": False}
            learn_res = playbook.learn_from_feedback(test_q, "", fb_dict, filings["MSFT"])

            if learn_res["status"] == "accepted":
                print(">>> ✅ RESULT: ACCEPTED & DISTILLED INTO PLAYBOOK!")
                print(f"    Added Rule: {learn_res['rule']['guideline']}")
            else:
                print(">>> 🛑 RESULT: REJECTED BY GATE!")
                print(f"    Reason: {learn_res['reason']}")

if __name__ == "__main__":
    main()
