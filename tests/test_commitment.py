"""Unit tests for CommitmentEngine safety and wrong commitment prevention.
"""

import pytest
from commitment_engine import CommitmentEngine


@pytest.fixture
def engine():
    return CommitmentEngine()


def test_no_commit_on_ambiguity(engine):
    # Multiple candidates -> must wait
    candidates = [{"product_id": "P0001"}, {"product_id": "P0002"}]
    filters = {"category": "running shoes", "colour": "green"}
    should, reason, conf = engine.evaluate(filters, candidates, "green running shoes", 3)
    assert should is False
    assert "Ambiguous" in reason


def test_no_commit_when_size_missing_for_sized_category(engine):
    # Only 1 candidate matches, but size has not been specified yet
    candidates = [{"product_id": "P0001"}]
    filters = {"category": "running shoes", "colour": "green"}
    should, reason, conf = engine.evaluate(filters, candidates, "Strydo green running shoes", 4)
    assert should is False
    assert "Size required" in reason


def test_commit_on_closing_phrase(engine):
    # 1 candidate, category, colour, size all known, and shopper starts a closing phrase
    candidates = [{"product_id": "P0086"}]
    filters = {"category": "sneakers", "colour": "navy", "size": "7", "brand": "Loomsy"}
    text = "Loomsy navy blue casual sneakers size 7 for my brother"
    should, reason, conf = engine.evaluate(filters, candidates, text, 10)
    assert should is True
    assert "closing phrase" in reason
    assert conf >= 0.95


def test_commit_on_resolved_correction(engine):
    # Correction occurred and replacement size is articulated
    candidates = [{"product_id": "P0553"}]
    filters = {"category": "kurtas", "colour": "maroon", "size": "XS", "brand": "Tanaro", "max_price": 1500}
    text = "show me maroon size M, oops, XS Tanaro kurta max 1500"
    should, reason, conf = engine.evaluate(filters, candidates, text, 11)
    assert should is True
    assert "Correction resolved" in reason


def test_no_commit_during_in_flight_transition(engine):
    candidates = [{"product_id": "P0001"}]
    filters = {"category": "running shoes", "colour": "green", "size": "7"}
    text = "Strydo green running shoes size 7 and"
    should, reason, conf = engine.evaluate(filters, candidates, text, 7)
    assert should is False
    assert "transition" in reason
