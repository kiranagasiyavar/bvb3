"""Prediction Engine for Anticipatory Commerce.

Coordinates intent parsing, intelligent search scheduling, candidate retrieval,
and early commitment decisions.
"""

from typing import Dict, Any, List, Optional, Tuple
from intent_parser import IntentParser
from search_engine import SearchEngine
from commitment_engine import CommitmentEngine
from rezolve_client import RezolveLabsClient


class PredictionEngine:
    """End-to-end prediction engine for incremental anticipatory shopping."""

    def __init__(
        self,
        tools=None,
        rezolve_client: Optional[RezolveLabsClient] = None,
        confidence_threshold: float = 0.90,
        max_searches: int = 5
    ):
        self.parser = IntentParser()
        self.search_engine = SearchEngine(tools=tools, rezolve_client=rezolve_client)
        self.commitment_engine = CommitmentEngine(confidence_threshold=confidence_threshold)
        self.max_searches = max_searches

        # Session tracking
        self.words: List[str] = []
        self.committed_id: Optional[str] = None
        self.committed_at_word: Optional[int] = None
        self.committed_product: Optional[Dict[str, Any]] = None

    def start(self, request_id: str):
        """Start a new shopping request session."""
        self.words = []
        self.committed_id = None
        self.committed_at_word = None
        self.committed_product = None
        self.search_engine.reset_session(max_searches=self.max_searches)

    def observe_word(self, word: str, use_rezolve: bool = False) -> Dict[str, Any]:
        """Process an incremental incoming word."""
        self.words.append(word)
        return self.predict_state(use_rezolve=use_rezolve)

    def set_text(self, text: str, use_rezolve: bool = False) -> Dict[str, Any]:
        """Process full or partial text string directly (useful for UI typing & demo mode)."""
        self.words = text.strip().split()
        return self.predict_state(use_rezolve=use_rezolve)

    def predict_state(self, use_rezolve: bool = False) -> Dict[str, Any]:
        """Compute the complete prediction state for current words."""
        text = " ".join(self.words)
        word_count = len(self.words)

        # 1. Parse intent & constraints
        parsed = self.parser.parse(text)
        filters = {
            "category": parsed["category"],
            "colour": parsed["colour"],
            "size": parsed["size"],
            "brand": parsed["brand"],
            "max_price": parsed["max_price"]
        }

        # 2. Fast candidate retrieval from catalogue
        candidates = self.search_engine.find_candidates(filters)

        # 3. Evaluate commit decision
        should_commit = False
        decision_reason = "Awaiting information"
        confidence = 0.5

        if self.committed_id is None:
            should_commit, decision_reason, confidence = self.commitment_engine.evaluate(
                filters=filters,
                candidates=candidates,
                text=text,
                word_count=word_count,
                is_finished=False
            )

            search_status = "idle"
            if should_commit:
                # Trigger official counted search to lock in the candidate
                hits, search_status = self.search_engine.search(
                    query=text,
                    filters=filters,
                    k=5,
                    use_rezolve=use_rezolve
                )
                if hits:
                    best = hits[0]
                    self.committed_id = best["product_id"]
                    self.committed_at_word = word_count
                    self.committed_product = best
                    decision_reason = f"Safely committed to {best['title']} ({best['product_id']})"
                else:
                    should_commit = False
                    decision_reason = "Search yielded 0 hits; deferred commitment"
        else:
            # Already committed: verify if commitment is still valid or if user changed constraints
            candidate_p = self.search_engine.products_by_id.get(self.committed_id)
            if candidate_p and self.search_engine.matches_all(candidate_p, filters):
                should_commit = True
                decision_reason = f"Product locked: {candidate_p['title']} ({self.committed_id})"
                confidence = 0.99
            else:
                # Conflict detected! Invalidate commitment to avoid wrong commit!
                self.committed_id = None
                self.committed_product = None
                should_commit = False
                decision_reason = "Constraint update conflicted with prior commit; retracted safely"
                confidence = 0.5
            search_status = "cached"

        # Overall confidence score
        if self.committed_id:
            overall_confidence = 0.99
            decision_label = "COMMIT"
        elif should_commit:
            overall_confidence = confidence
            decision_label = "COMMIT"
        else:
            active_filters = sum(1 for v in filters.values() if v is not None)
            overall_confidence = min(0.90, max(0.20, active_filters * 0.20))
            decision_label = "WAIT"

        return {
            "words": list(self.words),
            "text": text,
            "word_count": word_count,
            "detected_filters": filters,
            "confidences": parsed["confidences"],
            "statuses": parsed["statuses"],
            "has_correction": parsed["has_correction"],
            "is_correcting": parsed["is_correcting"],
            "candidates": candidates[:10],
            "candidate_count": len(candidates),
            "decision": decision_label,
            "decision_reason": decision_reason,
            "confidence": overall_confidence,
            "committed_id": self.committed_id,
            "committed_product": self.committed_product,
            "committed_at_word": self.committed_at_word,
            "search_count": self.search_engine.search_count,
            "searches_wasted": max(0, self.search_engine.search_count - 1),
            "search_history": list(self.search_engine.search_history)
        }

    def finish(self) -> Optional[str]:
        """Shopper finished typing. Return final product_id, resolving gracefully."""
        text = " ".join(self.words)
        parsed = self.parser.parse(text)
        final_filters = {
            "category": parsed["category"],
            "colour": parsed["colour"],
            "size": parsed["size"],
            "brand": parsed["brand"],
            "max_price": parsed["max_price"]
        }

        # If we already have a committed product and it satisfies final filters, keep it
        if self.committed_id is not None:
            p = self.search_engine.products_by_id.get(self.committed_id)
            if p and self.search_engine.matches_all(p, final_filters):
                return self.committed_id

        # Progressive filter relaxation for maximum robustness
        clean_filters = {k: v for k, v in final_filters.items() if v is not None}
        drop_orders = [
            [],
            ["max_price"],
            ["max_price", "brand"],
            ["max_price", "size"],
            ["brand"],
            ["size"],
            ["colour"],
            ["category"]
        ]

        for drop in drop_orders:
            cur_f = dict(clean_filters)
            for d in drop:
                cur_f.pop(d, None)
            hits, _ = self.search_engine.search(text, cur_f, k=1)
            if hits:
                return hits[0]["product_id"]

        hits, _ = self.search_engine.search(text, {}, k=1)
        if hits:
            return hits[0]["product_id"]

        return self.committed_id
