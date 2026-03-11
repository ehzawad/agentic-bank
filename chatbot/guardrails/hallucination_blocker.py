"""G1: Hallucination Blocker.

Scans Claude's response for financial data not backed by tool results in the FactStore.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from chatbot.memory.models import Fact

FINANCIAL_PATTERNS = [
    r"\$[\d,]+\.?\d*",                       # Dollar amounts like $12,450.75
    r"[\d,]+\.\d{2}\s*(?:USD|EUR|GBP|BDT)",  # Currency amounts
    r"\d+\.?\d*\s*%\s*(?:APR|interest|rate)", # Interest rates
    r"[A-Z]{2,4}-\d{4}-\d+",                 # Reference IDs (DSP-2026-08847)
    r"BLK-\w+-\d+",                           # Block IDs
    r"WIR-\d{4}-\d+",                         # Wire transfer IDs
    r"APP-\d{4}-\d+",                         # Application IDs
    r"STM-\w+-\d+M",                          # Statement IDs
    r"FML-\d{4}-\d+",                         # Formal complaint IDs
]


@dataclass
class ScanResult:
    safe: bool = True
    ungrounded_claims: list[str] = field(default_factory=list)


class HallucinationBlocker:
    def scan(self, response_text: str, fact_entries: list[Fact]) -> ScanResult:
        found: list[str] = []
        for pattern in FINANCIAL_PATTERNS:
            matches = re.findall(pattern, response_text)
            found.extend(matches)

        if not found:
            return ScanResult(safe=True)

        # Build a set of all values in the fact store for cross-reference
        fact_values: set[str] = set()
        for fact in fact_entries:
            fact_values.update(_extract_values(fact.value))

        ungrounded = [m for m in found if not _is_grounded(m, fact_values)]

        if ungrounded:
            return ScanResult(safe=False, ungrounded_claims=ungrounded)
        return ScanResult(safe=True)


def _extract_values(value: object) -> set[str]:
    """Recursively extract string representations from a fact value."""
    strings: set[str] = set()
    if isinstance(value, dict):
        for v in value.values():
            strings.update(_extract_values(v))
    elif isinstance(value, list):
        for item in value:
            strings.update(_extract_values(item))
    else:
        strings.add(str(value))
    return strings


def _is_grounded(claim: str, fact_values: set[str]) -> bool:
    """Check if a claimed value appears in the fact store values.

    Uses exact numeric comparison to avoid substring false matches
    (e.g., "$100" should NOT match a fact value of "$1000").
    """
    clean = claim.strip().replace("$", "").replace(",", "").replace("%", "").strip()
    # Extract just the numeric part from claims like "19.99 APR"
    num_match = re.match(r"([\d.]+)", clean)
    clean_num = num_match.group(1) if num_match else clean

    # Try exact match on raw claim first
    if claim in fact_values:
        return True

    for fv in fact_values:
        fv_clean = str(fv).replace("$", "").replace(",", "").strip()
        # Exact numeric match (not substring)
        if clean_num == fv_clean:
            return True
        # Also allow the numeric part to appear as a whole number in the fact
        # e.g., claim "12450.75" in fact string "balance is 12450.75 USD"
        if re.search(r"(?<!\d)" + re.escape(clean_num) + r"(?!\d)", fv_clean):
            return True
    return False
