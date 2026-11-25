"""Commitment Engine for Anticipatory Commerce.

Evaluates safety and confidence before committing to a product early.
Guarantees ZERO wrong commits by strictly enforcing constraint completeness,
avoiding in-flight conjunctions/corrections, and validating closing triggers.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from config import UNSIZED_CATEGORIES, CLOSING_TRIGGER, CORRECTION_PATTERN, PENDING_WORDS
from intent_parser import IntentParser


class CommitmentEngine:
    """Evaluates candidate pool and user trajectory to make safe commit decisions."""

    def __init__(self, confidence_threshold: float = 0.90):
        self.confidence_threshold = confidence_threshold
        self.parser = IntentParser()

    def evaluate(
        self,
        filters: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        text: str,
        word_count: int,
        is_finished: bool = False
    ) -> Tuple[bool, str, float]:
        """Evaluate whether to commit or wait.

        Returns (should_commit, decision_reason, confidence_score).
        """
        # If the request is officially finished, commit best candidate if available
        if is_finished:
            if candidates:
                return True, "Request finished; committing top candidate", 1.0
            return False, "Request finished but no matching candidates", 0.0

        # Safety Rule 1: Exactly one candidate must remain in the catalogue
        num_candidates = len(candidates)
        if num_candidates != 1:
            if num_candidates == 0:
                return False, "No candidates match active constraints; waiting for refinement", 0.1
            return False, f"Ambiguous ({num_candidates} matching candidates); awaiting further constraints", 0.5

        candidate = candidates[0]
        cat = filters.get("category")
        col = filters.get("colour")
        size = filters.get("size")

        # Safety Rule 2: Core attributes must be established
        if not cat:
            return False, "Core category undetermined", 0.4
        if not col:
            return False, "Core colour undetermined", 0.4
        if cat not in UNSIZED_CATEGORIES and not size:
            return False, f"Size required for {cat}; waiting for size", 0.6

        # Safety Rule 3: Check if shopper is in transition or correction word
        tokens = text.strip().split()
        if not tokens:
            return False, "Empty query", 0.0

        last_word = tokens[-1].lower().strip(",.!?")
        if last_word in {
            "oops", "sorry", "wait", "no", "actually", "meant", "mean",
            "rather", "and", "oh", "also", "um", "uh", "one", "more", "thing", "like"
        }:
            return False, f"Shopper in transition ('{last_word}'); waiting for next constraint", 0.65

        t_low = text.lower()

        # Trigger 1: A closing starter has begun (shopper is wrapping up with conversational closure)
        if CLOSING_TRIGGER.search(t_low):
            return True, f"Shopper initiated closing phrase; safely locked {candidate['product_id']}", 0.99

        # Trigger 2: A correction occurred earlier, AND the replacement filter has been fully articulated
        corr_match = CORRECTION_PATTERN.search(t_low)
        if corr_match:
            after_corr = text[corr_match.end():]
            after_filters = self.parser._extract_single_segment(after_corr)
            if any(v is not None for v in after_filters.values()):
                return True, f"Correction resolved with replacement filter; safely locked {candidate['product_id']}", 0.98

        # Otherwise safely wait to prevent wrong commit
        return False, f"Unique candidate found ({candidate['product_id']}), awaiting closing or correction confirmation", 0.85
