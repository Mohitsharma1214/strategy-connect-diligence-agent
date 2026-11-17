"""
Real EDGAR Form 10-K HTML & Table Parser.

Parses SEC EDGAR Form 10-K HTML filings (including Inline XBRL) to extract:
1. Verbatim visible text sentences (whitespace-collapsed).
2. Structured financial tables with exact (table_row, column, value) mapping.

Handles EDGAR-specific HTML patterns:
- Multi-column year headers (e.g. '2026', '2025', 'Change (2026)').
- Separate currency symbols ('$') and percentage symbols ('%').
- Negative numbers in parentheses (e.g. '(115,948)').
- Stacked sub-tables inheriting year columns (e.g. Gross Margin Percentages).
- Section-qualified row labels (e.g. 'Services (gross margin)', 'Products (gross margin percentage)').
"""

import os
import re
import warnings
from typing import Dict, List, Optional, Tuple
import bs4
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def collapse_whitespace(text: str) -> str:
    """Collapses all whitespace to single spaces and normalizes common Unicode punctuation."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("&nbsp;", " ")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    return " ".join(text.split())

class EdgarFilingParser:
    def __init__(self, filing_path: str):
        self.filing_path = filing_path
        self.soup: Optional[bs4.BeautifulSoup] = None
        self.raw_text: str = ""
        self.collapsed_text: str = ""
        self.sentences: List[str] = []
        self.table_cells: List[Dict[str, str]] = []
        self.tables_data: List[List[Dict[str, str]]] = []
        
        self._parse()

    def _parse(self):
        """Loads and parses the 10-K HTML filing."""
        with open(self.filing_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        self.soup = bs4.BeautifulSoup(content, "lxml")
        
        # 1. Extract and normalize narrative visible text
        # Filter script, style and noscript
        for unwanted in self.soup.find_all(["script", "style", "noscript"]):
            unwanted.decompose()

        self.raw_text = self.soup.get_text(separator=" ")
        self.collapsed_text = collapse_whitespace(self.raw_text)
        
        # Segment into clean sentences, filtering out XBRL taxonomy blobs and uninformative chunks
        raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", self.collapsed_text)
        self.sentences = [
            s.strip() for s in raw_sentences 
            if 15 <= len(s.strip()) <= 1500 and "fasb.org" not in s and "http://" not in s and "0000789019" not in s
        ]

        # 2. Extract structured financial tables
        self._extract_tables()

    def _normalize_cell_tokens(self, tokens: List[str]) -> List[str]:
        """Merges fragmented table cell tokens like ['15', '%'] -> ['15%'] and removes bare '$'."""
        merged = []
        for tok in tokens:
            tok = tok.strip()
            if not tok or tok == "$":
                continue
            if tok == "%" and merged:
                merged[-1] = merged[-1] + "%"
            elif tok == ")" and merged and merged[-1].startswith("("):
                merged[-1] = merged[-1] + ")"
            elif merged and merged[-1] == "(":
                merged[-1] = "(" + tok
            else:
                merged.append(tok)
        return merged

    def _extract_tables(self):
        """Extracts structured data from all HTML table elements."""
        tables = self.soup.find_all("table")
        last_known_columns = ["2026", "2025", "2024"]

        for tbl in tables:
            rows = tbl.find_all("tr")
            if len(rows) < 2:
                continue

            # Identify header rows (detecting fiscal years e.g. 2026, 2025, 2024, Change)
            hdr_candidates = []
            for r in rows[:8]:
                cells = [collapse_whitespace(c.get_text()) for c in r.find_all(["th", "td"])]
                clean_cells = self._normalize_cell_tokens(cells)
                if any(re.search(r"\b202[0-9]\b", c) for c in clean_cells):
                    hdr_candidates.append(clean_cells)

            # Build normalized column headers
            columns = []
            has_explicit_header = bool(hdr_candidates)
            has_row_label_in_header = False

            if has_explicit_header:
                base_hdr = hdr_candidates[-1]
                
                # Check if first element is a unit or empty description (e.g. 'Year Ended...', '(In millions)')
                first_cell = base_hdr[0] if base_hdr else ""
                if not re.search(r"\b202[0-9]\b", first_cell):
                    has_row_label_in_header = True
                    data_col_tokens = base_hdr[1:]
                else:
                    data_col_tokens = base_hdr

                prev_year = ""
                for c in data_col_tokens:
                    c_clean = c.strip()
                    if re.match(r"^202[0-9]$", c_clean):
                        columns.append(c_clean)
                        prev_year = c_clean
                    elif "change" in c_clean.lower() or "%" in c_clean:
                        col_name = f"Change ({prev_year})" if prev_year else "Change"
                        columns.append(col_name)
                    elif c_clean:
                        columns.append(c_clean)

                if columns:
                    last_known_columns = columns
            else:
                # Inherit columns from preceding table context if rows have matching column count
                columns = last_known_columns

            # Detect table title / section header from preceding text
            tbl_title = ""
            prev_elem = tbl.find_previous(["p", "div", "h1", "h2", "h3", "h4"])
            if prev_elem:
                title_text = collapse_whitespace(prev_elem.get_text())
                if len(title_text) < 120:
                    tbl_title = title_text

            # Parse data rows
            current_section = ""
            current_table_cells = []

            for r in rows:
                raw_cells = [collapse_whitespace(c.get_text()) for c in r.find_all(["td", "th"])]
                norm_cells = self._normalize_cell_tokens(raw_cells)
                if not norm_cells or (has_explicit_header and norm_cells in hdr_candidates):
                    continue

                # Check if this row is a section header (e.g. 'Services', 'Gross margin percentage:', 'Products')
                if len(norm_cells) == 1 or (len(norm_cells) == 2 and not re.search(r"\d", norm_cells[1])):
                    current_section = norm_cells[0].rstrip(":")
                    continue

                row_label = norm_cells[0]
                
                # Determine qualified row label based on section and context
                qualified_labels = [row_label]
                if current_section:
                    sec_clean = current_section.rstrip(":")
                    if sec_clean.lower() not in row_label.lower():
                        qualified_labels.append(f"{row_label} ({sec_clean})")
                    if "gross margin percentage" in sec_clean.lower():
                        qualified_labels.append(f"{row_label} (gross margin percentage)")
                    elif "gross margin" in sec_clean.lower():
                        qualified_labels.append(f"{row_label} (gross margin)")
                
                if "net sales by segment" in tbl_title.lower() or "segment" in tbl_title.lower():
                    qualified_labels.append(f"{row_label} (net sales by segment)")

                # If the row has 1 row label + values matching columns length
                data_values = norm_cells[1:]
                
                # Map data values to columns
                for q_label in qualified_labels:
                    val_idx = 0
                    for col_name in columns:
                        if val_idx >= len(data_values):
                            break
                        val = data_values[val_idx]
                        val_idx += 1

                        if re.search(r"\d", val):
                            cell_record = {
                                "table_row": q_label,
                                "base_row": row_label,
                                "column": col_name,
                                "value": val,
                                "section": current_section,
                                "table_title": tbl_title
                            }
                            self.table_cells.append(cell_record)
                            current_table_cells.append(cell_record)

            if current_table_cells:
                self.tables_data.append(current_table_cells)

    def find_sentence_quote(self, quote: str) -> Optional[str]:
        """
        Verifies if quote appears verbatim in the visible text after collapsing whitespace.
        Returns the exact matching sentence from the filing.
        """
        norm_q = collapse_whitespace(quote)
        # Fast substring check
        if norm_q in self.collapsed_text:
            return norm_q

        # Handle minor EDGAR spacing differences around symbols ($ 329.1 -> $329.1, 33 % -> 33%)
        q_alt = re.sub(r"\$\s+(\d)", r"$\1", norm_q)
        q_alt = re.sub(r"(\d)\s+%", r"\1%", q_alt)
        
        c_alt = re.sub(r"\$\s+(\d)", r"$\1", self.collapsed_text)
        c_alt = re.sub(r"(\d)\s+%", r"\1%", c_alt)

        if q_alt in c_alt:
            return norm_q

        return None

    def find_cell(self, table_row: str, column: str, value: str) -> Optional[Dict[str, str]]:
        """
        Finds a matching table cell by row label, column, and value.
        """
        row_norm = collapse_whitespace(table_row).lower()
        col_norm = collapse_whitespace(column).lower()
        val_norm = collapse_whitespace(value).replace("$", "").strip()

        for c in self.table_cells:
            c_row = c["table_row"].lower()
            c_base = c["base_row"].lower()
            c_col = c["column"].lower()
            c_val = c["value"].replace("$", "").strip()

            # Exact or qualified row match
            row_match = (
                row_norm == c_row or
                row_norm == c_base or
                row_norm in c_row or
                c_row in row_norm
            )
            col_match = (
                col_norm == c_col or
                col_norm in c_col or
                c_col in col_norm
            )
            val_match = (val_norm == c_val)

            if row_match and col_match and val_match:
                return c

        return None
