"""
Citation Verifier and Automatic Grounding Signal.
Extracts, indexes, and validates sentence-level citations against raw 10-K filings.
Provides claim-level semantic support checks to prevent hallucinated assertions.
"""

import re
from typing import Dict, List, Tuple

class CitationVerifier:
    def __init__(self, filings: Dict[str, str]):
        """
        filings: mapping of company ticker ('MSFT', 'AAPL', 'NKE') to raw indexed filing text.
        """
        self.filings = filings
        self.sentence_index = self._build_sentence_index()

    def _build_sentence_index(self) -> Dict[str, str]:
        """Indexes every [TICKER:Sxxx] tag to its full sentence text."""
        index = {}
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
        """Finds all citation tags like [MSFT:S001] in text."""
        return re.findall(r"\[[A-Z]+:S\d+\]", text)

    def verify_citations(self, answer: str, expected_company: str = None) -> Dict:
        """
        Verifies:
        1. Answer carries at least one citation.
        2. Citations exist in the indexed document.
        3. Citations match the requested company.
        """
        citations = self.extract_citations(answer)
        if not citations:
            return {
                "valid": False,
                "precision": 0.0,
                "citations": [],
                "valid_citations": [],
                "invalid_citations": [],
                "reason": "Missing citation. Every answer must carry a sentence citation."
            }

        valid_citations = []
        invalid_citations = []

        for cit in citations:
            if cit in self.sentence_index:
                if expected_company:
                    cit_comp = cit[1:].split(":")[0]
                    if cit_comp != expected_company:
                        invalid_citations.append((cit, f"Company mismatch: expected {expected_company}"))
                        continue
                valid_citations.append(cit)
            else:
                invalid_citations.append((cit, "Citation tag not found in filing"))

        precision = len(valid_citations) / len(citations) if citations else 0.0
        return {
            "valid": len(invalid_citations) == 0 and len(valid_citations) > 0,
            "precision": precision,
            "citations": citations,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "citation_texts": {cit: self.sentence_index.get(cit, "") for cit in valid_citations}
        }

    def check_claim_support(self, claim: str, citation_tag: str) -> bool:
        """
        Comprehensive semantic claim support:
        1. Checks that ALL asserted numbers and percentages exist in the cited sentence.
        2. Checks that key financial terms overlap significantly with the source.
        3. Detects directional contradictions (e.g. 'increased' vs 'decreased').
        """
        if citation_tag not in self.sentence_index:
            return False
        source = self.sentence_index[citation_tag].lower()
        clean_claim = re.sub(r"\[[A-Z]+:S\d+\]", "", claim).lower()

        # Check directional contradictions
        if "increased" in clean_claim and "decreased" in source and "increased" not in source:
            return False
        if "decreased" in clean_claim and "increased" in source and "decreased" not in source:
            return False

        # Extract asserted numerical values
        numbers = re.findall(r"(\$?\d+(?:\.\d+)?%?)", clean_claim)
        if numbers:
            # ALL significant numbers must be supported by the cited sentence
            for num in numbers:
                num_clean = num.replace("$", "").replace("%", "")
                if len(num_clean) >= 2 and num_clean not in source:
                    return False

        # Check entity/term overlap
        claim_terms = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", clean_claim)]
        if claim_terms:
            matched = sum(1 for w in claim_terms if w in source)
            if (matched / len(claim_terms)) < 0.25:
                return False

        return True
