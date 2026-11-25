"""Official Agent implementation for Anticipatory Commerce Challenge.

Compatible with evaluate.py harness:
    python evaluate.py --agent agent.py
"""

from typing import Dict, Any, Optional
from prediction_engine import PredictionEngine
from rezolve_client import RezolveLabsClient


class Agent:
    """Anticipatory Commerce Agent for word-by-word streaming shopper evaluation."""

    def __init__(self, tools):
        self.tools = tools
        self.rezolve = RezolveLabsClient()
        self.engine = PredictionEngine(
            tools=tools,
            rezolve_client=self.rezolve,
            confidence_threshold=0.90,
            max_searches=10
        )

    def start(self, request_id: str):
        """A new shopper request begins."""
        self.engine.start(request_id)

    def observe(self, word: str) -> Optional[Dict[str, Any]]:
        """Process one incoming word from the shopper.

        Returns:
            None to wait, or
            dict containing:
                "commit": "P0123" (optional)
                "filters": {...} (active parsed filters)
                "confidence": 0.95 (confidence percentage)
        """
        state = self.engine.observe_word(word)

        res: Dict[str, Any] = {
            "filters": state["detected_filters"],
            "confidence": state["confidence"]
        }

        if state["decision"] == "COMMIT" and state["committed_id"]:
            res["commit"] = state["committed_id"]

        return res

    def finish(self) -> Optional[str]:
        """The request is complete. Return final product_id."""
        return self.engine.finish()
