"""Search Engine and Intelligent Scheduler for Anticipatory Commerce.

Integrates local catalog search, fast candidate filtering, search deduplication,
and optional Rezolve Labs Semantic Search.
"""

import csv
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from config import CATALOGUE_PATH, UNSIZED_CATEGORIES
from rezolve_client import RezolveLabsClient


def load_catalogue(path: Path = CATALOGUE_PATH) -> List[Dict[str, Any]]:
    """Load catalogue rows with parsed integer prices."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["price"] = int(r["price"])
    return rows


class SearchEngine:
    """Unified search manager and scheduler."""

    def __init__(self, tools=None, rezolve_client: Optional[RezolveLabsClient] = None):
        self.tools = tools
        self.rezolve = rezolve_client or RezolveLabsClient()
        self.catalogue = load_catalogue()
        self.products_by_id = {p["product_id"]: p for p in self.catalogue}

        # Session tracking
        self.search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.search_count: int = 0
        self.max_searches: int = 5
        self.search_history: List[Dict[str, Any]] = []

    def reset_session(self, max_searches: int = 5):
        """Reset search scheduler state for a new shopper query."""
        self.search_cache.clear()
        self.search_count = 0
        self.max_searches = max_searches
        self.search_history.clear()

    def find_candidates(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fast in-memory catalogue filter verification."""
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        cat = clean_filters.get("category")
        is_unsized = cat in UNSIZED_CATEGORIES if cat else False

        candidates = []
        for p in self.catalogue:
            # Check category
            if "category" in clean_filters and p["category"].lower() != str(clean_filters["category"]).lower():
                continue
            # Check colour
            if "colour" in clean_filters and p["colour"].lower() != str(clean_filters["colour"]).lower():
                continue
            # Check brand
            if "brand" in clean_filters and p["brand"].lower() != str(clean_filters["brand"]).lower():
                continue
            # Check size (if not unsized)
            if "size" in clean_filters and not is_unsized:
                if p["size"].lower() != str(clean_filters["size"]).lower():
                    continue
            # Check max_price
            if "max_price" in clean_filters:
                if p["price"] > clean_filters["max_price"]:
                    continue
            candidates.append(p)
        return candidates

    def matches_all(self, product: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a specific product satisfies all active constraints."""
        clean = {k: v for k, v in filters.items() if v is not None}
        cat = clean.get("category")
        is_unsized = cat in UNSIZED_CATEGORIES if cat else False

        for k, v in clean.items():
            if k == "max_price":
                if product["price"] > v:
                    return False
            elif k in ("category", "colour", "brand"):
                if product[k].lower() != str(v).lower():
                    return False
            elif k == "size":
                if not is_unsized and product["size"].lower() != str(v).lower():
                    return False
        return True

    def search(
        self,
        query: str,
        filters: Dict[str, Any],
        k: int = 5,
        use_rezolve: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Execute early search via tools (or local fallback), checking cache first.

        Returns (results, status_code: 'cached' | 'searched' | 'limit_reached').
        """
        clean_filters = {k: v for k, v in filters.items() if v is not None}

        # Create signature for deduplication
        filter_sig = tuple(sorted((k, str(v)) for k, v in clean_filters.items()))
        cache_key = f"{query.strip().lower()}|{filter_sig}|{k}"

        if cache_key in self.search_cache:
            return self.search_cache[cache_key], "cached"

        if self.search_count >= self.max_searches:
            # Return last cached or empty without wasting search count
            return self.find_candidates(clean_filters)[:k], "limit_reached"

        hits: List[Dict[str, Any]] = []

        # If Rezolve semantic search is enabled and live
        if use_rezolve and self.rezolve.is_configured:
            raw_hits, meta = self.rezolve.semantic_search(query, clean_filters, limit=k)
            if self.tools:
                self.tools.record_search(1)
            self.search_count += 1

            # Map Rezolve hits back to catalogue objects
            for h in raw_hits:
                p_id = h.get("id") or h.get("product_id")
                if p_id in self.products_by_id:
                    prod = dict(self.products_by_id[p_id])
                    if self.matches_all(prod, clean_filters):
                        hits.append(prod)

            self.search_history.append({
                "type": "rezolve_semantic",
                "query": query,
                "filters": clean_filters,
                "count": len(hits)
            })

        # Otherwise use local tool search or fallback
        if not hits:
            if self.tools:
                hits = self.tools.search(query, clean_filters, k=k)
            else:
                hits = self.find_candidates(clean_filters)[:k]

            self.search_count += 1
            self.search_history.append({
                "type": "local_catalog",
                "query": query,
                "filters": clean_filters,
                "count": len(hits)
            })

        self.search_cache[cache_key] = hits
        return hits, "searched"
