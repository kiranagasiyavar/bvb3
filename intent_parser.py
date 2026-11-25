"""Intent Parser for Anticipatory Commerce.

Provides word-by-word, phrase-level, and conversational incremental parsing:
- Category, Colour, Size, Budget (max_price), and Brand detection.
- Natural language numbers & Hindi-English code-mixed phrases.
- Precision disambiguation (e.g., navy blue -> navy, t-shirt -> t-shirts, running sneakers -> running shoes).
- Dynamic correction handling with segmented multi-part resolution.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from config import (
    BRANDS,
    CATEGORY_PATTERNS,
    COLOUR_PATTERNS,
    NUMBER_WORDS,
    HINDI_SIZE_NUMBERS,
    CORRECTION_PATTERN,
    UNSIZED_CATEGORIES,
    CLOSING_TRIGGER
)


class IntentParser:
    """Incremental natural language parser for shopping intent & constraint extraction."""

    def __init__(self):
        self.brands = BRANDS
        self.category_patterns = CATEGORY_PATTERNS
        self.colour_patterns = COLOUR_PATTERNS

    def parse(self, text: str) -> Dict[str, Any]:
        """Extract all active filters from incremental text, properly resolving corrections."""
        if not text or not text.strip():
            return {
                "category": None,
                "colour": None,
                "size": None,
                "brand": None,
                "max_price": None,
                "confidences": {k: 0.0 for k in ("category", "colour", "size", "brand", "max_price")},
                "statuses": {k: "uncertain" for k in ("category", "colour", "size", "brand", "max_price")},
                "has_correction": False,
                "is_correcting": False
            }

        # Check if text contains correction phrase
        has_correction = bool(CORRECTION_PATTERN.search(text))

        # Check if the very last word/phrase is an in-flight correction marker
        words = text.strip().split()
        last_token = words[-1].lower().strip(",.!?") if words else ""
        is_correcting = last_token in {
            "oops", "sorry", "wait", "no", "actually", "meant", "mean",
            "rather", "change", "nahi", "matlab"
        }

        # Split text into correction segments
        parts = CORRECTION_PATTERN.split(text)

        resolved_filters = {
            "category": None,
            "colour": None,
            "size": None,
            "brand": None,
            "max_price": None
        }

        # Progressively apply each segment so newer values override older ones
        for part in parts:
            pt = part.strip()
            if not pt:
                continue
            part_filters = self._extract_single_segment(pt)
            for k, v in part_filters.items():
                if v is not None:
                    resolved_filters[k] = v

        confidences = {}
        statuses = {}
        for k, v in resolved_filters.items():
            if v is not None:
                confidences[k] = 0.95
                statuses[k] = "confirmed"
            else:
                confidences[k] = 0.0
                statuses[k] = "uncertain"

        return {
            **resolved_filters,
            "confidences": confidences,
            "statuses": statuses,
            "has_correction": has_correction,
            "is_correcting": is_correcting
        }

    def _extract_single_segment(self, segment: str) -> Dict[str, Any]:
        """Extract filters from a single coherent segment of text."""
        filters = {
            "category": None,
            "colour": None,
            "size": None,
            "brand": None,
            "max_price": None
        }

        # 1. Brand matching
        for b in self.brands:
            if re.search(rf"\b{re.escape(b)}\b", segment, flags=re.IGNORECASE):
                filters["brand"] = b

        # 2. Colour matching with boundary check
        col_spots = []
        for col, patterns in self.colour_patterns:
            for pat in patterns:
                for m in re.finditer(pat, segment, flags=re.IGNORECASE):
                    # Disambiguation: avoid matching blue in 'navy blue'
                    if col == "blue":
                        pre = segment[max(0, m.start() - 6):m.end()].lower()
                        if "navy" in pre:
                            continue
                    # Disambiguation: avoid matching green in 'olive green'
                    if col == "green":
                        pre = segment[max(0, m.start() - 7):m.end()].lower()
                        if "olive" in pre:
                            continue
                    col_spots.append((m.start(), col))
        if col_spots:
            col_spots.sort()
            filters["colour"] = col_spots[-1][1]

        # 3. Category matching with disambiguation
        cat_spots = []
        for cat, patterns in self.category_patterns:
            for pat in patterns:
                for m in re.finditer(pat, segment, flags=re.IGNORECASE):
                    # Disambiguation: shirts vs t-shirts
                    if cat == "shirts":
                        pre = segment[max(0, m.start() - 4):m.end()].lower()
                        if re.search(r"\bt[\s\-_]+", pre):
                            continue
                    # Disambiguation: sneakers vs running sneakers
                    if cat == "sneakers":
                        pre = segment[max(0, m.start() - 9):m.end()].lower()
                        if "running" in pre or "jogging" in pre:
                            continue
                    cat_spots.append((m.start(), cat))
        if cat_spots:
            cat_spots.sort()
            filters["category"] = cat_spots[-1][1]

        # 4. Size extraction
        size_val = self._extract_size(segment)
        if size_val:
            filters["size"] = size_val

        # 5. Price extraction
        price_val = self._extract_price(segment)
        if price_val:
            filters["max_price"] = price_val

        return filters

    def _extract_size(self, text: str) -> Optional[str]:
        """Extract apparel or footwear size from text."""
        t = text.lower()

        # Hindi size expressions (e.g. 'das number', 'saat number')
        m_hin = re.search(r"\b(che|chhe|saat|aath|nau|das|gyaarah)\s+number\b", t)
        if m_hin:
            return HINDI_SIZE_NUMBERS.get(m_hin.group(1))

        # Multi-word apparel sizes
        if re.search(r"\b(?:double\s+extra\s+large|double\s+xl|2xl|xxl)\b", t):
            return "XXL"
        if re.search(r"\b(?:extra\s+large)\b", t):
            return "XL"
        if re.search(r"\b(?:extra\s+small)\b", t):
            return "XS"
        if re.search(r"\b(?:small)\b", t):
            return "S"
        if re.search(r"\b(?:medium)\b", t):
            return "M"
        if re.search(r"\b(?:large)\b", t):
            return "L"

        # Explicit keywords: 'size 9', 'uk 7', 'waist 32'
        m = re.findall(r"\b(?:size|uk|waist)\s+([a-z0-9]+)\b", t)
        if m:
            val = m[-1]
            val_u = val.upper()
            if val_u in {"XS", "S", "M", "L", "XL", "XXL"}:
                return val_u
            if val in {"6", "7", "8", "9", "10", "11", "28", "30", "32", "34", "36"}:
                return val
            if val in NUMBER_WORDS and str(NUMBER_WORDS[val]) in {"6", "7", "8", "9", "10", "11"}:
                return str(NUMBER_WORDS[val])

        # Reverse keywords: '9 uk', '32 waist', 'M size'
        m2 = re.findall(r"\b([a-z0-9]+)\s+(?:uk|size|waist)\b", t)
        if m2:
            val = m2[-1]
            val_u = val.upper()
            if val_u in {"XS", "S", "M", "L", "XL", "XXL"}:
                return val_u
            if val in {"6", "7", "8", "9", "10", "11", "28", "30", "32", "34", "36"}:
                return val
            if val in NUMBER_WORDS and str(NUMBER_WORDS[val]) in {"6", "7", "8", "9", "10", "11"}:
                return str(NUMBER_WORDS[val])

        # Standalone uppercase abbreviations
        m3 = re.findall(r"\b(XXL|2XL|XL|XS|M|L|S)\b", text)
        if m3:
            val = m3[-1]
            return "XXL" if val in {"2XL", "XXL"} else val

        # Footwear number words adjacent to category (e.g. 'eight slides', 'nine running shoes')
        m_foot = re.search(
            r"\b(six|seven|eight|nine|ten|eleven)\s+(?:slides?|sandals?|shoes?|sneakers?|kicks|runners?|floaters?)\b",
            t
        )
        if m_foot:
            w = m_foot.group(1)
            # Ensure not followed by hundred / thousand
            tail = t[m_foot.start():m_foot.end() + 10]
            if not re.search(r"\b(?:hundred|thousand)\b", tail):
                return str(NUMBER_WORDS[w])

        return None

    def _extract_price(self, text: str) -> Optional[int]:
        """Extract budget constraint in rupees from numeric, shorthand, or natural language."""
        t = text.lower()

        # Hindi expressions
        if re.search(r"\bsaadhe\s+teen\s+hazaar\b", t):
            return 3500
        if re.search(r"\bdhai\s+hazaar\b", t):
            return 2500
        if re.search(r"\b(?:dedh\s+hazaar|pandrah\s+sau)\b", t):
            return 1500
        if re.search(r"\bsatrah\s+sau\b", t):
            return 1700
        if re.search(r"\bpaanch\s+hazaar\b", t):
            return 5000
        if re.search(r"\bdo\s+hazaar\b", t):
            return 2000

        # Post-number Hindi budget keywords: '2000 tak', '1700 se kam', '1500 ke andar'
        post_hin = re.findall(r"\b([\d,]+)\s*(?:tak|se\s+kam|ke\s+andar)\b", t)
        if post_hin:
            try:
                val = int(post_hin[-1].replace(",", ""))
                if val >= 100:
                    return val
            except ValueError:
                pass

        # Shorthand k notation: '4k', '0.8k', '1.5k', '2.5k'
        k_match = re.findall(
            r"(?:under|below|less\s+than|within|max|up\s+to|budget|not\s+more\s+than|around|inside|tak)\s*(?:rs\.?\s*|₹\s*)?([\d\.]+)\s*k\b",
            t
        )
        if k_match:
            try:
                return int(float(k_match[-1]) * 1000)
            except ValueError:
                pass

        # Direct digits: '2000', '1,500', '₹3500'
        d_match = re.findall(
            r"(?:under|below|less\s+than|within|max|up\s+to|budget|not\s+more\s+than|around|inside|tak)\s*(?:rs\.?\s*|₹\s*)?([\d,]+)\b",
            t
        )
        if d_match:
            try:
                val_str = d_match[-1].replace(",", "")
                val = int(val_str)
                # Avoid confusing size numbers (6-36) as budgets
                if val >= 100:
                    return val
            except ValueError:
                pass

        # Natural language word numbers (e.g. 'forty five hundred', 'two thousand five hundred')
        text_to_val = {
            "forty five hundred": 4500,
            "thirty seven hundred": 3700,
            "thirty five hundred": 3500,
            "twenty five hundred": 2500,
            "twenty three hundred": 2300,
            "seventeen hundred": 1700,
            "sixteen hundred": 1600,
            "fifteen hundred": 1500,
            "fourteen hundred": 1400,
            "thirteen hundred": 1300,
            "twelve hundred": 1200,
            "eleven hundred": 1100,
            "one thousand five hundred": 1500,
            "one thousand one hundred": 1100,
            "one thousand seven hundred": 1700,
            "two thousand five hundred": 2500,
            "two thousand three hundred": 2300,
            "three thousand five hundred": 3500,
            "four thousand five hundred": 4500,
            "six thousand five hundred": 6500,
            "seventy five hundred": 7500,
            "two thousand": 2000,
            "three thousand": 3000,
            "four thousand": 4000,
            "five thousand": 5000,
            "six thousand": 6000,
            "seven thousand": 7000,
            "eight thousand": 8000,
            "nine thousand": 9000,
            "one thousand": 1000,
            "four hundred": 400,
            "five hundred": 500,
            "six hundred": 600,
            "seven hundred": 700,
            "eight hundred": 800,
            "nine hundred": 900
        }

        # Sort patterns by length descending so longer phrases match first
        sorted_phrases = sorted(text_to_val.keys(), key=len, reverse=True)
        matched_spans = []
        for phrase in sorted_phrases:
            pat = rf"\b{re.escape(phrase)}\b"
            for m in re.finditer(pat, t):
                s, e = m.start(), m.end()
                if any(existing_s <= s and e <= existing_e for existing_s, existing_e, _ in matched_spans):
                    continue
                matched_spans.append((s, e, text_to_val[phrase]))

        if matched_spans:
            matched_spans.sort(key=lambda x: x[0])
            return matched_spans[-1][2]

        return None
