"""
StrategyConnect Diligence Agent
Generalized, fully dynamic diligence agent running over any SEC EDGAR Form 10-K filing.
Extracts grounded financial answers with verbatim sentence quotes and exact table cell citations.
Zero hardcoded company templates: dynamically retrieves and synthesizes from filing primary text and tables.
"""

from __future__ import annotations
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from src.parser.edgar_parser import EdgarFilingParser
from src.agent.local_llm import LocalLLMClient


class PlaybookRule:
    """A diligence strategy rule learned from verified human analyst feedback."""
    def __init__(
        self,
        rule_id: str,
        topic: str,
        condition: str,
        action: str,
        expansion_terms: Optional[List[str]] = None,
        question_id: Optional[str] = None,
        company: Optional[str] = None,
        verified_answer: Optional[str] = None,
        verified_citations: Optional[List[Dict[str, Any]]] = None,
        contributing_analyst: Optional[str] = None,
        trust_weight: float = 1.0,
    ):
        self.rule_id = rule_id
        self.topic = topic
        self.condition = condition
        self.action = action
        self.expansion_terms = expansion_terms or []
        self.question_id = question_id
        self.company = company
        self.verified_answer = verified_answer
        self.verified_citations = verified_citations or []
        self.contributing_analyst = contributing_analyst
        self.trust_weight = trust_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "topic": self.topic,
            "condition": self.condition,
            "action": self.action,
            "expansion_terms": self.expansion_terms,
            "question_id": self.question_id,
            "company": self.company,
            "contributing_analyst": self.contributing_analyst,
            "trust_weight": self.trust_weight,
        }


class DiligencePlaybook:
    """Repository of verified diligence retrieval and synthesis strategies."""
    def __init__(self):
        self.rules: List[PlaybookRule] = []

    def add_rule(self, rule: PlaybookRule) -> None:
        for existing in self.rules:
            if existing.rule_id == rule.rule_id or (existing.question_id and existing.question_id == rule.question_id and existing.action == rule.action):
                return
        self.rules.append(rule)

    def get_rule_for_question(self, question_id: str) -> Optional[PlaybookRule]:
        for r in reversed(self.rules):
            if r.question_id == question_id:
                return r
        return None

    def get_rules_for_topic(self, topic: str) -> List[PlaybookRule]:
        return [r for r in self.rules if r.topic == topic or r.topic == "ALL"]

    def list_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.rules]


def _cell_to_citation(cell_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not cell_dict:
        return None
    return {
        "type": "cell",
        "table_row": cell_dict.get("table_row", ""),
        "column": cell_dict.get("column", ""),
        "value": cell_dict.get("value", "")
    }


def extract_keywords(text: str) -> List[str]:
    """Extract significant lower-cased keyword tokens from a query string."""
    tokens = re.findall(r"\b[A-Za-z0-9_]{3,}\b", text.lower())
    stop_words = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "the", "and", "for", "with", "from", "that", "this", "fiscal", "year",
        "company", "did", "was", "were", "are", "about", "among", "under", "into",
        "end", "change", "fast", "much", "many", "rate", "percentage"
    }
    return [t for t in tokens if t not in stop_words]


class DiligenceAgent:
    """
    Generalized Diligence Agent that operates dynamically over any Form 10-K filing.
    Combines semantic sentence retrieval, table cell coordinate search,
    reflective playbook rules, and local open-weights LLM synthesis.
    """

    def __init__(self, parser: EdgarFilingParser, playbook: Optional[DiligencePlaybook] = None, llm: Optional[LocalLLMClient] = None):
        self.parser = parser
        self.playbook = playbook or DiligencePlaybook()
        self.llm = llm or LocalLLMClient()
        self.last_call_cost: float = 0.0
        self.total_cost: float = 0.0

    def identify_topic(self, text: str) -> str:
        """Classify general financial topic to activate relevant playbook strategies."""
        t_lower = text.lower()
        if "concentrat" in t_lower or ("customer" in t_lower and ("revenue" in t_lower or "net sales" in t_lower)):
            return "customer_concentration"
        if "gross margin" in t_lower or "margin percentage" in t_lower:
            return "gross_margin"
        if "property and equipment" in t_lower or "capex" in t_lower or "capital expenditures" in t_lower or "capital additions" in t_lower:
            return "capex_additions"
        if "repurchase" in t_lower or "buybacks" in t_lower or "dividend" in t_lower:
            return "capital_return"
        if "effective tax rate" in t_lower or "income tax" in t_lower:
            return "effective_tax_rate"
        if "remaining performance obligation" in t_lower or "rpo" in t_lower:
            return "rpo"
        if "lease" in t_lower or "commitments" in t_lower or "obligations" in t_lower:
            return "obligations_and_leases"
        if "employee" in t_lower or "headcount" in t_lower:
            return "headcount"
        if "diluted eps" in t_lower or "earnings per share" in t_lower:
            return "diluted_eps"
        if "net sales" in t_lower or "total revenue" in t_lower or "total revenues" in t_lower or "revenue grow" in t_lower:
            return "revenue_and_sales"
        return "general"

    def answer_question(self, question_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically answers any diligence question using the active Form 10-K parser.
        Strictly returns citations belonging to the active filing.
        """
        qid = question_obj.get("id", "")
        question_text = question_obj.get("question", "")
        topic = self.identify_topic(question_text)
        rules = self.playbook.get_rules_for_topic(topic)
        q_rule = self.playbook.get_rule_for_question(qid)

        # Priority 2: Check if verified feedback rule exists for this question
        if q_rule and q_rule.verified_citations:
            verified_cits = []
            for cit in q_rule.verified_citations:
                if cit.get("type") == "sentence":
                    if self.parser.find_sentence_quote(cit.get("quote", "")):
                        verified_cits.append(cit)
                elif cit.get("type") == "cell":
                    if self.parser.find_cell(cit.get("table_row", ""), cit.get("column", ""), cit.get("value", "")):
                        verified_cits.append(cit)
            if verified_cits:
                ans_text = q_rule.verified_answer or q_rule.action
                return {
                    "id": qid,
                    "answer": ans_text,
                    "citations": verified_cits
                }

        # 1. Build search query terms with general GAAP financial expansions
        query_terms = extract_keywords(question_text)
        expansion_terms = []

        # Standard GAAP / SEC Form 10-K financial terminology (universal across all industries):
        if topic == "customer_concentration":
            expansion_terms.extend(["customer", "concentration", "individual customer", "single customer", "10% of revenue", "10 percent", "10% or more", "major customer", "credit risk", "trade receivables", "total receivables", "receivables balance", "no entity represented", "concentration of credit risk"])
        elif topic == "gross_margin":
            expansion_terms.extend(["gross margin", "margin percentage", "cost of sales", "cost of revenue", "gross profit"])
        elif topic == "capex_additions":
            expansion_terms.extend(["property and equipment", "capital expenditures", "additions to property", "purchases of property"])
        elif topic == "capital_return":
            expansion_terms.extend(["repurchased", "share repurchase", "buybacks", "dividends paid", "dividends declared", "return of capital"])
        elif topic == "effective_tax_rate":
            expansion_terms.extend(["effective tax rate", "income tax", "provision for income taxes", "statutory rate", "foreign tax rate"])
        elif topic == "obligations_and_leases":
            expansion_terms.extend(["purchase obligations", "contractual obligations", "commitments", "leases", "uncommenced leases"])
        elif topic == "revenue_and_sales":
            expansion_terms.extend(["total revenue", "total revenues", "total net sales", "net sales", "revenue increased", "revenue grew", "recognized total revenues", "compared to the prior year"])
        elif topic == "headcount":
            expansion_terms.extend(["employed", "full-time employees", "headcount", "personnel", "workforce"])
        elif topic == "diluted_eps":
            expansion_terms.extend(["diluted earnings per share", "diluted eps", "diluted per share"])

        for r in rules:
            expansion_terms.extend(r.expansion_terms)

        # 2. Search Sentences in Active Filing
        best_sentences: List[Tuple[float, str]] = []
        for sent in self.parser.sentences:
            s_lower = sent.lower()
            score = 0
            # Direct keyword matching
            for t in query_terms:
                if t in s_lower:
                    score += 1.0
            # Playbook expansion matching
            for ext in expansion_terms:
                if ext.lower() in s_lower:
                    score += 3.0  # High weight for verified domain phrases
            # Favor quantitative sentences when question asks quantitative facts
            if any(c in sent for c in ["$", "%"]) and any(q_word in question_text.lower() for q_word in ["how fast", "how much", "rate", "%", "what was"]):
                score += 0.5
            # Match comparative intent: "compared to the prior year" / "compared to prior"
            if "compared" in query_terms and ("compared to the prior year" in s_lower or "compared to prior" in s_lower):
                score += 1.5
            # Demote sentences whose primary subject is a subordinate expense line when querying headline revenue
            if topic == "revenue_and_sales" and ("r&d expense as a percentage" in s_lower or "marketing expense" in s_lower):
                score -= 4.0
            if score > 0:
                best_sentences.append((score, sent))

        best_sentences.sort(key=lambda x: x[0], reverse=True)

        # 3. Search Financial Table Cells in Active Filing
        best_cells: List[Tuple[float, Dict[str, Any]]] = []
        for cell in self.parser.table_cells:
            row = cell.get("table_row", "")
            col = cell.get("column", "")
            sec = cell.get("section", "")
            cell_txt = f"{row} {col} {sec}".lower()
            score = 0
            for t in query_terms:
                if t in cell_txt:
                    score += 1.0
            # Prefer comparative year columns (2026, 2025, Change)
            if any(y in col for y in ["2026", "2025", "Change"]):
                score += 0.5
            if score > 0:
                best_cells.append((score, cell))

        best_cells.sort(key=lambda x: x[0], reverse=True)

        # 4. Decide Evidence Modality: Sentence vs. Table Cells
        citations = []
        context_str = ""

        # Check if table cells provide a direct coordinate answer (e.g. EPS, cash flow additions)
        table_preferred_topics = {"diluted_eps"}
        if topic == "capex_additions" and best_cells:
            cell_row = best_cells[0][1].get("table_row", "").lower()
            if any(term in cell_row for term in ["additions to property", "purchases of property", "capital additions"]):
                table_preferred_topics.add("capex_additions")
        prefer_table = topic in table_preferred_topics or (best_cells and best_cells[0][0] >= 3.0 and not best_sentences)

        if prefer_table and best_cells:
            top_row = best_cells[0][1].get("table_row", "")
            # Find all relevant year cells for this matched row label
            matched_row_cells = [c[1] for c in best_cells if c[1].get("table_row") == top_row][:4]
            for c in matched_row_cells:
                citations.append(_cell_to_citation(c))
            cell_desc = ", ".join([f"{c.get('column')}: {c.get('value')}" for c in matched_row_cells])
            context_str = f"From Financial Table '{top_row}': {cell_desc}."
            answer_text = f"{top_row} was {cell_desc}."
        elif best_sentences:
            top_sents = [best_sentences[0][1]]
            # Only append a second sentence if it directly shares the primary topic terms and complements
            if len(best_sentences) > 1:
                cand_sent = best_sentences[1][1]
                cand_lower = cand_sent.lower()
                # Do not attach secondary sentences from unrelated expense lines (e.g. R&D) when querying revenue
                is_irrelevant = any(bad in cand_lower for bad in ["r&d expense", "marketing expense", "overhead expense"])
                if not is_irrelevant and (topic in ["gross_margin", "customer_concentration"] or (len(top_sents[0]) < 80 and any(c in cand_sent for c in ["$", "%"]))):
                    top_sents.append(cand_sent)
            for s in top_sents:
                citations.append({"type": "sentence", "quote": s})
            context_str = " ".join(top_sents)
            answer_text = " ".join(top_sents)
        elif best_cells:
            # Fallback to top cell
            c = best_cells[0][1]
            citations.append(_cell_to_citation(c))
            context_str = f"{c.get('table_row')} ({c.get('column')}): {c.get('value')}"
            answer_text = context_str
        else:
            # No disclosures in this filing for this question
            return {
                "id": qid,
                "answer": "The provided filing does not contain relevant disclosure for this inquiry.",
                "citations": []
            }

        # 5. Model Synthesis via Local LLM Client (if active)
        if self.llm and self.llm.is_connected and context_str:
            playbook_hint = rules[0].action if rules else None
            llm_ans = self.llm.synthesize_diligence_answer(question_text, context_str, playbook_hint)
            if llm_ans and len(llm_ans.strip()) > 10:
                # Numerical faithfulness verification: ensure LLM synthesis did not distort numbers
                llm_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", llm_ans))
                llm_substantive = {n for n in llm_nums if len(n) > 1 or "." in n}
                ctx_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", context_str))
                faithful = True
                for num in llm_substantive:
                    if num not in ctx_nums and not any(num in c for c in ctx_nums):
                        faithful = False
                        break
                if faithful:
                    answer_text = llm_ans.strip()

        # Strict ground truth validation: verify all attached citations exist in active filing
        verified_citations = []
        for cit in citations:
            if cit.get("type") == "sentence":
                q = cit.get("quote", "")
                if self.parser.find_sentence_quote(q):
                    verified_citations.append(cit)
            elif cit.get("type") == "cell":
                if self.parser.find_cell(cit.get("table_row", ""), cit.get("column", ""), cit.get("value", "")):
                    verified_citations.append(cit)

        # If zero citations verified in this filing, answer cannot claim facts
        if not verified_citations:
            answer_text = "The provided filing does not contain relevant disclosure for this inquiry."

        return {
            "id": qid,
            "answer": answer_text,
            "citations": verified_citations
        }
