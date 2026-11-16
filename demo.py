#!/usr/bin/env python3
"""
Interactive Diligence Agent Terminal Demo.
Allows users to:
1. Select a company (MSFT, AAPL, NKE).
2. Type ANY custom investor diligence question freely in plain text.
3. Inspect active Playbook rules.
4. Submit custom analyst feedback in real time.
"""

import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.signals.citation_verifier import CitationVerifier
from src.memory.playbook import DiligencePlaybook
from src.agent.diligence_agent import DiligenceAgent
from src.evaluation.scorer import DiligenceScorer

def infer_category(question_text: str) -> str:
    """Infers the diligence category from user's free-text question."""
    q_lower = question_text.lower()
    if "customer" in q_lower or "concentration" in q_lower or "client" in q_lower:
        return "Customer Concentration"
    elif "margin" in q_lower or "depreciation" in q_lower or "useful life" in q_lower or "cost of revenue" in q_lower:
        return "Gross Margin & Accounting"
    elif "cloud" in q_lower or "azure" in q_lower or "segment" in q_lower or "mac" in q_lower or "direct" in q_lower:
        return "Segment Performance"
    elif "capex" in q_lower or "capital expenditure" in q_lower or "cash flow" in q_lower:
        return "Capital Allocation & Capex"
    elif "fx" in q_lower or "foreign exchange" in q_lower or "currency" in q_lower:
        return "FX Impact"
    elif "r&d" in q_lower or "research" in q_lower:
        return "R&D Investment"
    elif "debt" in q_lower or "cash" in q_lower or "liquidity" in q_lower:
        return "Balance Sheet & Debt"
    elif "headcount" in q_lower or "restructuring" in q_lower or "layoff" in q_lower or "employee" in q_lower:
        return "Restructuring & Headcount"
    return "General"

def main():
    print("=" * 65)
    print("   STRATEGYCONNECT DILIGENCE AGENT - INTERACTIVE TERMINAL   ")
    print("=" * 65)

    filings = {}
    filings_dir = os.path.join(BASE_DIR, "data/filings")
    for fname, comp in [("msft_10k_2023.txt", "MSFT"), ("aapl_10k_2023.txt", "AAPL"), ("nke_10k_2023.txt", "NKE")]:
        with open(os.path.join(filings_dir, fname), "r") as f:
            filings[comp] = f.read()

    verifier = CitationVerifier(filings)
    playbook = DiligencePlaybook(verifier, naive_mode=False)
    agent = DiligenceAgent(filings, verifier, playbook=playbook)

    print("\n[System Ready]: 3 Companies Loaded:")
    print("  • Microsoft Corporation (MSFT)")
    print("  • Apple Inc. (AAPL)")
    print("  • NIKE, Inc. (NKE - Unseen Evaluation Company)")
    print("Playbook is active with Real-Time Grounding Gate ON.\n")

    while True:
        print("-" * 65)
        print("Choose an action:")
        print("  1. Ask a question about Microsoft (MSFT)")
        print("  2. Ask a question about Apple (AAPL)")
        print("  3. Ask a question about Nike (NKE - UNSEEN Company)")
        print("  4. View active Playbook Rules")
        print("  5. Submit custom feedback / test the 20% Noise Filter")
        print("  6. Exit")
        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "6":
            print("\nExiting. Thank you!")
            break

        elif choice in ["1", "2", "3"]:
            comp_map = {"1": "MSFT", "2": "AAPL", "3": "NKE"}
            comp = comp_map[choice]
            
            print(f"\nAsk ANY question about {comp} (or press Enter for suggested question):")
            print("Examples:")
            if comp == "MSFT":
                print("  • How concentrated is revenue among top customers?")
                print("  • What was gross margin and how did server useful life impact it?")
                print("  • What drove growth in the Intelligent Cloud segment?")
            elif comp == "AAPL":
                print("  • Why did Mac sales decline last year?")
                print("  • Where is Apple's manufacturing concentrated?")
                print("  • How much was returned to shareholders via buybacks and dividends?")
            elif comp == "NKE":
                print("  • Why did NIKE's gross margin contract 250 bps?")
                print("  • How concentrated is wholesale revenue with Foot Locker?")
                print("  • Where is footwear manufacturing geographically concentrated?")

            user_q = input("\nType your question: ").strip()
            if not user_q:
                # Default suggestion
                user_q = "How concentrated is revenue among top customers?" if comp != "NKE" else "Why did gross margin contract last year?"

            cat = infer_category(user_q)
            q_payload = {
                "id": f"LIVE_{comp}_01",
                "company": comp,
                "category": cat,
                "question": user_q
            }

            print(f"\n[QUERYING DILIGENCE AGENT]...")
            print(f"Company:  {comp}")
            print(f"Category: {cat}")
            print(f"Question: {user_q}")

            res = agent.answer_question(q_payload)
            print(f"\n[AGENT ANSWER]:")
            print(f"> {res['answer']}")

            # Citations check
            cit_eval = verifier.verify_citations(res["answer"], expected_company=comp)
            print(f"\n[AUDIT & GROUNDING CHECK]:")
            print(f"  • Valid Citations:   {cit_eval['valid_citations']}")
            if cit_eval["invalid_citations"]:
                print(f"  • Invalid Citations: {cit_eval['invalid_citations']}")

            # Allow immediate analyst feedback
            print("\n" + "." * 65)
            give_fb = input("Would you like to provide an analyst correction on this answer? (y/n): ").strip().lower()
            if give_fb == "y":
                correction = input("Type your correction: ").strip()
                if correction:
                    fb_dict = {"correction": correction, "is_noisy": False}
                    learn_res = playbook.learn_from_feedback(q_payload, res["answer"], fb_dict)
                    if learn_res["status"] == "accepted":
                        print(">>> ✅ RESULT: ACCEPTED & ADDED TO PLAYBOOK!")
                        print(f"    New Rule: {learn_res['rule']['guideline']}")
                    else:
                        print(">>> 🛑 RESULT: REJECTED BY GATE!")
                        print(f"    Reason: {learn_res['reason']}")

        elif choice == "4":
            print("\n[ACTIVE PLAYBOOK RULES]:")
            if not playbook.rules:
                print("  (Playbook is currently empty. Rules are learned when feedback is submitted.)")
            else:
                for i, r in enumerate(playbook.rules, 1):
                    cat_name = r.get("intent_category", r.get("category", "General"))
                    print(f"  {i}. [{cat_name}]: {r['guideline']}")
            print(f"\nTotal Feedback Processed: {playbook.accepted_feedback_count} accepted, {playbook.rejected_feedback_count} rejected.")

        elif choice == "5":
            print("\n[TEST THE REAL-TIME FEEDBACK GATE]")
            print("Try typing a real correction OR a noisy/hallucinated correction to test the gate:")
            print("  • Valid: 'No single customer accounted for >10%. [MSFT:S030]'")
            print("  • Noisy/Fake tag: 'Azure grew 42% [MSFT:S999]'")
            print("  • Noisy/Fake number: 'Amazon is top customer with 18% share [MSFT:S001]'")
            
            fb_text = input("\nEnter correction text: ").strip()
            if not fb_text:
                fb_text = "No single customer accounted for >10%. [MSFT:S030]"

            test_q = {"id": "CUSTOM_01", "category": "Customer Concentration", "company": "MSFT"}
            print(f"\nEvaluating feedback through Verification Gate...")
            fb_dict = {"correction": fb_text, "is_noisy": False}
            learn_res = playbook.learn_from_feedback(test_q, "", fb_dict)

            if learn_res["status"] == "accepted":
                print(">>> ✅ RESULT: ACCEPTED & DISTILLED INTO PLAYBOOK!")
                print(f"    New Rule: {learn_res['rule']['guideline']}")
            else:
                print(">>> 🛑 RESULT: REJECTED BY GATE!")
                print(f"    Reason: {learn_res['reason']}")

if __name__ == "__main__":
    main()
