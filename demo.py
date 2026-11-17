#!/usr/bin/env python3
"""
Interactive Diligence Agent Terminal Demo.
Allows users to:
1. Ask diligence questions about Microsoft (MSFT) or Apple (AAPL) on real SEC Form 10-Ks.
2. View live LLM synthesis and verified sentence quotes / table cell citations.
3. Inspect active Playbook rules.
4. Test the real-time Analyst Verification Gate against noisy or adversarial feedback.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.parser.edgar_parser import EdgarFilingParser
from src.agent.diligence_agent import DiligenceAgent, DiligencePlaybook, PlaybookRule
from src.agent.local_llm import LocalLLMClient
from src.feedback.analyst_gate import AnalystVerificationGate


def main():
    print("=" * 65)
    print("   STRATEGYCONNECT DILIGENCE AGENT - INTERACTIVE TERMINAL   ")
    print("=" * 65)

    msft_path = os.path.join(BASE_DIR, "data/sc-diligence/filings/msft-20260630.htm")
    aapl_path = os.path.join(BASE_DIR, "data/sc-diligence/filings/aapl-20260926.htm")

    print("\n[Ingesting Real SEC EDGAR Form 10-K Filings]...")
    msft_parser = EdgarFilingParser(msft_path)
    aapl_parser = EdgarFilingParser(aapl_path)
    print(f"  • Microsoft Corporation: {len(msft_parser.sentences):,} sentences, {len(msft_parser.table_cells):,} table cells.")
    print(f"  • Apple Inc.:            {len(aapl_parser.sentences):,} sentences, {len(aapl_parser.table_cells):,} table cells.")

    # Initialize Local LLM Client
    llm = LocalLLMClient()
    print(f"\n[Local LLM Client]: Model={llm.model_name} (Status: {'Connected' if llm.is_connected else 'Offline / Deterministic Fallback'})")

    playbook_msft = DiligencePlaybook()
    playbook_aapl = DiligencePlaybook()
    agent_msft = DiligenceAgent(msft_parser, playbook_msft, llm=llm)
    agent_aapl = DiligenceAgent(aapl_parser, playbook_aapl, llm=llm)
    gate = AnalystVerificationGate({"MSFT": msft_parser, "AAPL": aapl_parser})

    # Preload option for 32 learned rules
    fb_path = os.path.join(BASE_DIR, "data/sc-diligence/feedback.jsonl")
    q_path = os.path.join(BASE_DIR, "data/sc-diligence/questions.json")
    if os.path.exists(fb_path) and os.path.exists(q_path):
        try:
            preload = input("\nPreload the 32 verified rules learned from the 4-round feedback loop? (y/n) [default: y]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            preload = "y"
        
        if preload != "n":
            with open(q_path) as f:
                q_map = {q["id"]: q for q in json.load(f)}
            with open(fb_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    fb = json.loads(line)
                    q_obj = q_map.get(fb.get("question_id"), {})
                    res = gate.process_feedback_item(fb, q_obj)
                    if res["is_valid"]:
                        r = PlaybookRule(
                            rule_id=f"RULE-{fb['id']}",
                            topic=agent_msft.identify_topic(fb["correction"]),
                            condition=f"Verified analyst correction ({fb['analyst']})",
                            action=fb["correction"]
                        )
                        agent_msft.playbook.add_rule(r)
                        agent_aapl.playbook.add_rule(r)
            print(f"  • Successfully preloaded {len(agent_msft.playbook.rules)} verified diligence rules into Playbook memory!")

    print("\nSystem ready. Enter an option below:")

    while True:
        print("\n" + "-" * 65)
        print("Choose an action:")
        print("  1. Ask a question about Microsoft (MSFT)")
        print("  2. Ask a question about Apple (AAPL)")
        print("  3. View active Playbook Rules")
        print("  4. Test Analyst Verification Gate (Noise / Injection Filter)")
        print("  5. Exit")
        try:
            choice = input("\nEnter choice (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if choice == "5":
            print("\nExiting. Thank you!")
            break

        elif choice in ["1", "2"]:
            comp = "MSFT" if choice == "1" else "AAPL"
            agent = agent_msft if comp == "MSFT" else agent_aapl
            parser = msft_parser if comp == "MSFT" else aapl_parser

            print(f"\nAsk ANY diligence question about {comp} (or press Enter for suggested question):")
            if comp == "MSFT":
                print("  [Suggestion]: How fast did Microsoft's total revenue grow in fiscal 2026, and what drove it?")
            else:
                print("  [Suggestion]: What was Apple's total gross margin percentage in fiscal 2026?")

            try:
                user_q = input("\nType your question: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_q:
                user_q = (
                    "How fast did Microsoft's total revenue grow in fiscal 2026, and what drove it?"
                    if comp == "MSFT"
                    else "What was Apple's total gross margin percentage in fiscal 2026?"
                )

            q_obj = {
                "id": f"INTERACTIVE_{comp}_01",
                "company": comp,
                "question": user_q
            }

            print(f"\n[QUERYING DILIGENCE AGENT]...")
            print(f"Company:  {comp}")
            print(f"Question: {user_q}")

            res = agent.answer_question(q_obj)
            print(f"\n[AGENT ANSWER]:")
            print(f"> {res['answer']}")

            print(f"\n[GROUNDED CITATIONS]:")
            if not res["citations"]:
                print("  (No direct citations found in filing)")
            for i, cit in enumerate(res["citations"], 1):
                if cit.get("type") == "sentence":
                    print(f"  {i}. [Sentence Quote]: \"{cit.get('quote')}\"")
                elif cit.get("type") == "cell":
                    print(f"  {i}. [Table Cell]: Row='{cit.get('table_row')}', Col='{cit.get('column')}', Value='{cit.get('value')}'")

            # Allow immediate feedback
            try:
                give_fb = input("\nWould you like to provide an analyst correction on this answer? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                give_fb = "n"

            if give_fb == "y":
                try:
                    correction = input("Type your correction: ").strip()
                except (EOFError, KeyboardInterrupt):
                    correction = ""
                if correction:
                    fb_item = {
                        "id": "FB-USER",
                        "round": 1,
                        "analyst": "AN-USER",
                        "question_id": q_obj["id"],
                        "correction": correction,
                        "citations": res["citations"]
                    }
                    decision = gate.process_feedback_item(fb_item, q_obj)
                    if decision["is_valid"]:
                        print(">>> ✅ RESULT: ACCEPTED BY GATE & ADDED TO PLAYBOOK!")
                        rule = PlaybookRule(
                            rule_id="RULE-USER",
                            topic=agent.identify_topic(correction),
                            condition="User verified correction",
                            action=correction
                        )
                        agent.playbook.add_rule(rule)
                    else:
                        print(">>> 🛑 RESULT: REJECTED BY GATE!")
                        print(f"    Reason: {decision['reason']}")

        elif choice == "3":
            print("\n[ACTIVE PLAYBOOK RULES]:")
            all_rules = agent_msft.playbook.rules
            if not all_rules:
                print("  (Playbook is currently at Round 0 baseline. Rules are added as verified analyst corrections are accepted.)")
            else:
                print(f"  Total Active Rules: {len(all_rules)}")
                for i, r in enumerate(all_rules, 1):
                    print(f"  {i:2d}. [{r.topic}]: {r.action}")

        elif choice == "4":
            print("\n[TEST THE ANALYST VERIFICATION GATE]")
            print("Test ANY official analyst feedback item directly from data/sc-diligence/feedback.jsonl:")
            print("  • FB-012 (AN-03): Valid institutional tax rate correction (19% vs 18%) -> Accepted")
            print("  • FB-028 (AN-01): Adversarial prompt injection / system override attack -> Rejected")
            print("  • FB-027 (AN-01): 1,000x magnitude error ($115.9 million vs $115,948M)  -> Rejected")
            print("  • FB-008 (AN-01): Temporal error (FY2025 net sales claimed as FY2026)   -> Rejected")
            print("  • FB-033 (AN-01): Hallucinated 'Harbor' multi-year agreement             -> Rejected")
            print("  • FB-001 (AN-01): OpenAI >10% revenue contradicting Note 19 negative assurance -> Rejected")
            print("  • FB-003 (AN-02): Inaccurate 'all payable' qualifier on purchase obligations  -> Rejected")
            print("  • (Or type 'custom' to enter your own free-text correction)")

            try:
                target_id = input("\nEnter Feedback ID (FB-001 to FB-048) or 'custom' [default: FB-012]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                target_id = "FB-012"

            if not target_id:
                target_id = "FB-012"

            # Dynamic loading directly from official feedback dataset
            fb_file = os.path.join(BASE_DIR, "data/sc-diligence/feedback.jsonl")
            q_file = os.path.join(BASE_DIR, "data/sc-diligence/questions.json")
            with open(q_file) as f_q:
                q_lookup = {q["id"]: q for q in json.load(f_q)}
            with open(fb_file) as f_fb:
                fb_lookup = {fb["id"]: fb for line in f_fb if line.strip() for fb in [json.loads(line)]}

            if target_id in fb_lookup:
                fb = fb_lookup[target_id]
                q_obj = q_lookup.get(fb.get("question_id"), {})
                print(f"\n[Evaluating Official Item {fb['id']} (Analyst: {fb['analyst']}, Round {fb.get('round')})]:")
                print(f"Correction text:   \"{fb['correction']}\"")
                print(f"Attached Citations: {fb.get('citations')}")
                decision = gate.process_feedback_item(fb, q_obj)
                if decision["is_valid"]:
                    print("\n>>> ✅ RESULT: ACCEPTED BY GATE & ADDED TO PLAYBOOK!")
                    rule = PlaybookRule(
                        rule_id=f"RULE-{fb['id']}",
                        topic=agent_msft.identify_topic(fb["correction"]),
                        condition=f"Verified analyst correction ({fb['analyst']})",
                        action=fb["correction"]
                    )
                    agent_msft.playbook.add_rule(rule)
                    agent_aapl.playbook.add_rule(rule)
                else:
                    print("\n>>> 🛑 RESULT: REJECTED BY GATE!")
                    print(f"    Reason: {decision['reason']}")
            else:
                try:
                    custom_text = input("\nEnter custom correction text: ").strip()
                except (EOFError, KeyboardInterrupt):
                    custom_text = ""
                if custom_text:
                    custom_fb = {
                        "id": "FB-CUSTOM", "round": 1, "analyst": "AN-USER", "question_id": "MSFT-L08",
                        "correction": custom_text,
                        "citations": [{"type": "sentence", "quote": "Our effective tax rate for fiscal years 2026 and 2025 was 19% and 18%, respectively."}]
                    }
                    decision = gate.process_feedback_item(custom_fb, {"id": "MSFT-L08", "question": "What was the effective tax rate?", "company": "MSFT"})
                    if decision["is_valid"]:
                        print("\n>>> ✅ RESULT: ACCEPTED BY GATE & ADDED TO PLAYBOOK!")
                    else:
                        print("\n>>> 🛑 RESULT: REJECTED BY GATE!")
                        print(f"    Reason: {decision['reason']}")


if __name__ == "__main__":
    main()
