"""Unit tests for IntentParser covering partial requests, code-mixing, numbers, and filters.
"""

import pytest
from intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


def test_empty_request(parser):
    res = parser.parse("")
    assert res["category"] is None
    assert res["colour"] is None
    assert res["size"] is None
    assert res["brand"] is None
    assert res["max_price"] is None
    assert res["is_correcting"] is False


def test_single_filter_category(parser):
    res = parser.parse("running shoes")
    assert res["category"] == "running shoes"
    assert res["colour"] is None


def test_single_filter_colour(parser):
    res = parser.parse("looking for black")
    assert res["colour"] == "black"
    assert res["category"] is None


def test_multi_filter_extraction(parser):
    res = parser.parse("Pacevo navy blue casual sneakers size 9 within 4500")
    assert res["brand"] == "Pacevo"
    assert res["colour"] == "navy"
    assert res["category"] == "sneakers"
    assert res["size"] == "9"
    assert res["max_price"] == 4500


def test_hindi_english_code_mixed(parser):
    res = parser.parse("Mujhe black shoes chahiye, size 9, budget 2000")
    assert res["colour"] == "black"
    assert res["size"] == "9"
    assert res["max_price"] == 2000

    res_hin2 = parser.parse("mere liye kaala Urbanyx jacket budget saadhe teen hazaar, M size milega?")
    assert res_hin2["colour"] == "black"
    assert res_hin2["brand"] == "Urbanyx"
    assert res_hin2["category"] == "jackets"
    assert res_hin2["max_price"] == 3500
    assert res_hin2["size"] == "M"

    res_hin3 = parser.parse("blue jogging shoes das number")
    assert res_hin3["colour"] == "blue"
    assert res_hin3["category"] == "running shoes"
    assert res_hin3["size"] == "10"


def test_natural_language_price(parser):
    res1 = parser.parse("under forty five hundred")
    assert res1["max_price"] == 4500

    res2 = parser.parse("below two thousand five hundred")
    assert res2["max_price"] == 2500

    res3 = parser.parse("less than 0.8k")
    assert res3["max_price"] == 800

    res4 = parser.parse("up to 1.5k")
    assert res4["max_price"] == 1500

    res5 = parser.parse("budget pandrah sau")
    assert res5["max_price"] == 1500


def test_apparel_and_footwear_sizes(parser):
    res1 = parser.parse("tee XXL")
    assert res1["size"] == "XXL"

    res2 = parser.parse("shirt extra large")
    assert res2["size"] == "XL"

    res3 = parser.parse("hoodie small")
    assert res3["size"] == "S"

    res4 = parser.parse("jeans waist 32")
    assert res4["size"] == "32"

    res5 = parser.parse("slides UK 7")
    assert res5["size"] == "7"
