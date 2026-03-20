"""Contract validation tests -- verify agent outputs meet prompt contracts.

These tests validate saved pricing results against the formal contracts
defined in prompt-contracts.md. Run after generating pricing results.
"""

import json
import sqlite3
from pathlib import Path

import pytest

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "precio.db"


def _load_results():
    """Load all saved pricing results from SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT filename, deal_json, result_json FROM results").fetchall()
    conn.close()
    results = []
    for row in rows:
        try:
            results.append((
                row["filename"],
                {"deal": json.loads(row["deal_json"]), "result": json.loads(row["result_json"])},
            ))
        except (json.JSONDecodeError, Exception):
            continue
    return results


RESULTS = _load_results()


@pytest.mark.skipif(not RESULTS, reason="No saved results to validate")
class TestPricingContracts:
    """Validate all saved results against prompt contracts."""

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_price_ordering(self, name, data):
        r = data["result"]
        assert r["price_floor"] <= r["price_target"]
        assert r["price_target"] <= r["price_stretch"]

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_prices_positive(self, name, data):
        r = data["result"]
        assert r["price_floor"] > 0
        assert r["price_target"] > 0
        assert r["price_stretch"] > 0

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_confidence_range(self, name, data):
        assert 0 <= data["result"]["confidence"] <= 1

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_rationale(self, name, data):
        assert data["result"]["rationale"] and len(data["result"]["rationale"]) > 10

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_structure(self, name, data):
        assert data["result"]["suggested_structure"] and len(data["result"]["suggested_structure"]) > 3

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_specialist_proposals(self, name, data):
        assert len(data["result"]["specialist_proposals"]) == 3
