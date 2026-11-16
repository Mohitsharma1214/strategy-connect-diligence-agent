"""
Citation Verifier and Automatic Grounding Signal.
Checks sentence/cell level citations against the underlying document text.
"""

import re
from typing import Dict, List, Tuple

class CitationVerifier:
    def __init__(self, filings: Dict[str, str]):
        """
        filings: mapping of company/doc_id to the raw indexed filing text.
        """
        self.filings = filings
        self.sentence_index = self._build_sentence_index()

    def _build_sentence_index(self) -> Dict[str, str]:
        index = {}
        # Pattern: [DOC:Sxxx] Text
        pattern = re.compile(r"\[([A-Z]+:S\d+)\]\s*(.*)")
        for comp, text in self.filings.items():
            for line in text.strip().split("\n"):
                match = pattern.match(line.strip())
                if match:
                    tag = f"[{match.group(1)}]"
                    sentence_text = match.group(2).strip()
                    index[tag] = sentence_text
        return index

    def extract_citations(self, text: str) -> List[str]:
        """Extracts all [DOC:Sxxx] citations from text."""
        return re.findall(r"\[[A-Z]+:S\d+\]", text)

    def verify_citations(self, answer: str, expected_company: str = None) -> Dict:
        """
        Verifies that:
        1. Answer has at least one citation.
        2. Citations exist in the indexed filings.
        3. Citations belong to the queried company.
        """
        citations = self.extract_citations(answer)
        if not citations:
            return {
                "valid": False,
                "precision": 0.0,
                "citations": [],
                "valid_citations": [],
                "invalid_citations": [],
                "reason": "Missing citations. Every answer must carry at least one citation."
            }

        valid_citations = []
        invalid_citations = []

        for cit in citations:
            if cit in self.sentence_index:
                # Check company match if expected_company is supplied
                if expected_company:
                    cit_comp = cit[1:].split(":")[0]
                    if cit_comp != expected_company:
                        invalid_citations.append((cit, "Citation company mismatch"))
                        continue
                valid_citations.append(cit)
            else:
                invalid_citations.append((cit, "Citation ID not found in filings"))

        precision = len(valid_citations) / len(citations) if citations else 0.0
        return {
            "valid": len(invalid_citations) == 0 and len(valid_citations) > 0,
            "precision": precision,
            "citations": citations,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "citation_texts": {cit: self.sentence_index.get(cit, "") for cit in valid_citations}
        }

    def check_claim_entailment(self, claim: str, citation_tag: str) -> bool:
        """
        Checks whether the cited sentence factually supports numbers or keywords in the claim.
        """
        if citation_tag not in self.sentence_index:
            return False
        source_sentence = self.sentence_index[citation_tag].lower()
        # Extract numbers, percentages, dollar amounts from claim
        claim_numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", claim)
        if not claim_numbers:
            return True # No specific numeric claims
        # At least one key number must be supported in the cited sentence
        supported = any(num.lower() in source_sentence for num in claim_numbers)
        return supported

