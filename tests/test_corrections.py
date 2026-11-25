"""Unit tests for Natural Language Corrections and Late Constraints.
"""

import pytest
from intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


def test_colour_correction(parser):
    text = "Black running shoes, no wait, white running shoes"
    res = parser.parse(text)
    assert res["colour"] == "white"
    assert res["category"] == "running shoes"
    assert res["has_correction"] is True


def test_size_correction(parser):
    text = "Urbanyx slides in black size 8 UK, sorry, size 7 UK budget 700"
    res = parser.parse(text)
    assert res["size"] == "7"
    assert res["colour"] == "black"
    assert res["brand"] == "Urbanyx"
    assert res["max_price"] == 700


def test_brand_correction(parser):
    text = "casual sneakers by Pacevo within 3.5k in navy blue, UK 10. actually, make it Kudova"
    res = parser.parse(text)
    assert res["brand"] == "Kudova"
    assert res["colour"] == "navy"
    assert res["size"] == "10"
    assert res["max_price"] == 3500


def test_category_correction(parser):
    text = "navy Loomsy shirt size M, max 2300, no, change that to dress"
    res = parser.parse(text)
    assert res["category"] == "dresses"
    assert res["brand"] == "Loomsy"
    assert res["colour"] == "navy"
    assert res["size"] == "M"
    assert res["max_price"] == 2300


def test_budget_correction(parser):
    text = "red bag pack under 2000, wait, I meant under 1000"
    res = parser.parse(text)
    assert res["max_price"] == 1000
    assert res["colour"] == "red"
    assert res["category"] == "backpacks"


def test_late_constraint(parser):
    text = "show me Sonquil headphones under 7,500, also, in blue for my brother"
    res = parser.parse(text)
    assert res["brand"] == "Sonquil"
    assert res["category"] == "headphones"
    assert res["max_price"] == 7500
    assert res["colour"] == "blue"
