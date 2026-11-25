"""Unit tests for SearchEngine, intelligent scheduling, and Rezolve fallback.
"""

import pytest
from search_engine import SearchEngine
from rezolve_client import RezolveLabsClient


@pytest.fixture
def search_engine():
    return SearchEngine()


def test_catalogue_loaded(search_engine):
    assert len(search_engine.catalogue) == 1074
    assert "P0001" in search_engine.products_by_id


def test_candidate_filtering_exact(search_engine):
    filters = {
        "category": "running shoes",
        "colour": "green",
        "size": "7",
        "brand": "Strydo",
        "max_price": 6000
    }
    cands = search_engine.find_candidates(filters)
    assert len(cands) == 1
    assert cands[0]["product_id"] == "P0001"


def test_candidate_filtering_unsized(search_engine):
    filters = {
        "category": "headphones",
        "colour": "white",
        "brand": "Audora",
        "max_price": 800
    }
    cands = search_engine.find_candidates(filters)
    assert len(cands) == 1
    assert cands[0]["product_id"] == "P1002"


def test_no_matching_products(search_engine):
    filters = {
        "category": "running shoes",
        "colour": "gold",  # no gold running shoes in catalogue
        "size": "9"
    }
    cands = search_engine.find_candidates(filters)
    assert len(cands) == 0


def test_search_cache_deduplication(search_engine):
    search_engine.reset_session(max_searches=5)
    filters = {"category": "sneakers", "colour": "black"}

    # First search
    hits1, status1 = search_engine.search("black sneakers", filters, k=3)
    assert status1 == "searched"
    assert search_engine.search_count == 1

    # Second search with identical query & filters
    hits2, status2 = search_engine.search("black sneakers", filters, k=3)
    assert status2 == "cached"
    assert search_engine.search_count == 1  # count did not increase
    assert hits1 == hits2


def test_search_limit_enforcement(search_engine):
    search_engine.reset_session(max_searches=2)

    # First search
    _, s1 = search_engine.search("query 1", {"colour": "black"}, k=2)
    assert s1 == "searched"

    # Second search
    _, s2 = search_engine.search("query 2", {"colour": "blue"}, k=2)
    assert s2 == "searched"

    # Third search exceeds budget
    _, s3 = search_engine.search("query 3", {"colour": "green"}, k=2)
    assert s3 == "limit_reached"
    assert search_engine.search_count == 2


def test_rezolve_fallback_when_unconfigured(search_engine):
    # Unconfigured client
    client = RezolveLabsClient(api_key="", kb_id="")
    hits, status = client.semantic_search("running shoes", {"category": "running shoes"})
    assert hits == []
    assert status["mode"] == "mock_adapter"
    assert status["connected"] is False
