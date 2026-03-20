"""Tests for the resilient JSON parser in base.py."""

from app.agents.base import extract_json


def test_clean_json():
    text = '{"price_floor": 10000, "price_target": 15000}'
    result = extract_json(text)
    assert result["price_floor"] == 10000
    assert result["price_target"] == 15000


def test_markdown_code_block():
    text = '```json\n{"price_floor": 10000}\n```'
    result = extract_json(text)
    assert result["price_floor"] == 10000


def test_commas_in_numbers():
    text = '{"price_floor": 1,088,750.00, "price_target": 2,500,000}'
    result = extract_json(text)
    assert result["price_floor"] == 1088750.00
    assert result["price_target"] == 2500000


def test_trailing_comma():
    text = '{"price_floor": 10000, "price_target": 15000,}'
    result = extract_json(text)
    assert result["price_floor"] == 10000


def test_single_quotes():
    text = "{'price_floor': 10000, 'price_target': 15000}"
    result = extract_json(text)
    assert result["price_floor"] == 10000


def test_truncated_json_simple():
    text = '{"price_floor": 10000, "price_target": 15000, "reasoning": "This is a trun'
    result = extract_json(text)
    assert result["price_floor"] == 10000
    assert result["price_target"] == 15000


def test_truncated_json_multiline():
    text = """{
  "price_floor": 50000,
  "price_target": 75000,
  "price_stretch": 100000,
  "confidence": 0.8,
  "suggested_structure": "Fixed fee",
  "rationale": "The cost agent floor is 50000 and the market supports"""
    result = extract_json(text)
    assert result["price_floor"] == 50000
    assert result["price_target"] == 75000
    assert result["confidence"] == 0.8


def test_truncated_with_array():
    text = """{
  "price_floor": 30000,
  "risk_factors": ["scope creep", "timeline pressure"],
  "assumptions": ["standard timeline", "us-based te"""
    result = extract_json(text)
    assert result["price_floor"] == 30000
    assert "scope creep" in result["risk_factors"]


def test_json_with_surrounding_text():
    text = "Here is my analysis:\n{\"price_floor\": 10000}\nThat's my recommendation."
    result = extract_json(text)
    assert result["price_floor"] == 10000


def test_comments_removed():
    text = """{
  "price_floor": 10000, // minimum
  "price_target": 15000 // recommended
}"""
    result = extract_json(text)
    assert result["price_floor"] == 10000
    assert result["price_target"] == 15000
