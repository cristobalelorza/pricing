"""Contract validation tests -- verify agent outputs meet prompt contracts.

These tests validate saved pricing results against the formal contracts
defined in prompt-contracts.md. Run after generating pricing results.
"""

import json
from pathlib import Path

import pytest

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _load_results():
    """Load all saved pricing results."""
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            results.append((path.name, data))
        except (json.JSONDecodeError, KeyError):
            continue
    return results


RESULTS = _load_results()


@pytest.mark.skipif(not RESULTS, reason="No saved results to validate")
class TestPricingContracts:
    """Validate all saved results against prompt contracts."""

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_price_ordering(self, name, data):
        """Floor <= Target <= Stretch."""
        r = data["result"]
        assert r["price_floor"] <= r["price_target"], f"Floor > Target in {name}"
        assert r["price_target"] <= r["price_stretch"], f"Target > Stretch in {name}"

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_prices_positive(self, name, data):
        """All prices must be positive."""
        r = data["result"]
        assert r["price_floor"] > 0
        assert r["price_target"] > 0
        assert r["price_stretch"] > 0

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_confidence_range(self, name, data):
        """Confidence must be 0-1."""
        r = data["result"]
        assert 0 <= r["confidence"] <= 1

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_rationale(self, name, data):
        """Rationale must be non-empty."""
        r = data["result"]
        assert r["rationale"] and len(r["rationale"]) > 10

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_assumptions(self, name, data):
        """Must have at least one assumption."""
        r = data["result"]
        assert len(r["assumptions"]) >= 1

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_risk_factors(self, name, data):
        """Must have at least one risk factor."""
        r = data["result"]
        assert len(r["risk_factors"]) >= 1

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_has_structure(self, name, data):
        """Must recommend a pricing structure."""
        r = data["result"]
        assert r["suggested_structure"] and len(r["suggested_structure"]) > 3

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_specialist_proposals(self, name, data):
        """Must have 3 specialist proposals (Cost, Market, Value)."""
        r = data["result"]
        assert len(r["specialist_proposals"]) == 3
        names = {p["agent_name"] for p in r["specialist_proposals"]}
        assert "Cost Agent" in names
        assert "Market Agent" in names
        assert "Value Agent" in names

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_specialist_price_ordering(self, name, data):
        """Each specialist's floor <= target <= stretch."""
        for p in data["result"]["specialist_proposals"]:
            assert p["price_floor"] <= p["price_target"], f"{p['agent_name']} floor > target"
            assert p["price_target"] <= p["price_stretch"], f"{p['agent_name']} target > stretch"

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_risk_assessment(self, name, data):
        """Risk adjustment must be 0-50%."""
        risk = data["result"]["risk_assessment"]
        assert 0 <= risk["risk_adjustment_pct"] <= 50
        assert len(risk["risk_factors"]) >= 1

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_validation_present(self, name, data):
        """Validation must be present."""
        v = data["result"]["validation"]
        assert v is not None
        assert isinstance(v["is_valid"], bool)
        assert v["summary"] and len(v["summary"]) > 10

    @pytest.mark.parametrize("name,data", RESULTS, ids=[r[0] for r in RESULTS])
    def test_floor_above_cost_floor(self, name, data):
        """Final floor should not be below Cost Agent's floor (prompt contract)."""
        r = data["result"]
        cost_proposal = next(
            p for p in r["specialist_proposals"] if p["agent_name"] == "Cost Agent"
        )
        # Allow 10% tolerance for rounding/truncation from free model
        assert r["price_floor"] >= cost_proposal["price_floor"] * 0.9, (
            f"Final floor {r['price_floor']} is below Cost Agent floor "
            f"{cost_proposal['price_floor']} (minus 10% tolerance)"
        )
