"""Unit tests for Pydantic data models."""

from app.models import (
    AgentProposal,
    Currency,
    DealInput,
    PackagingRecommendation,
    PricingResult,
    RiskAssessment,
    ValidationResult,
)


def test_deal_input_minimal():
    deal = DealInput(
        service_description="Test service",
        business_url="example.com",
    )
    assert deal.currency == Currency.USD
    assert deal.client_context == ""
    assert deal.budget_hint is None


def test_deal_input_full():
    deal = DealInput(
        service_description="Security audit",
        business_url="stripe.com",
        client_context="Fintech company",
        constraints="3 months",
        budget_hint=50000.0,
        currency=Currency.EUR,
    )
    assert deal.budget_hint == 50000.0
    assert deal.currency == Currency.EUR


def test_agent_proposal():
    p = AgentProposal(
        agent_name="Cost Agent",
        price_floor=10000,
        price_target=15000,
        price_stretch=20000,
        reasoning="Test reasoning",
        assumptions=["assumption 1"],
        confidence=0.8,
    )
    assert p.price_floor < p.price_target < p.price_stretch
    assert 0 <= p.confidence <= 1


def test_risk_assessment():
    r = RiskAssessment(
        risk_factors=["scope ambiguity", "timeline pressure"],
        risk_adjustment_pct=15.0,
        reasoning="Moderate risk",
        confidence=0.7,
    )
    assert r.agent_name == "Risk Agent"
    assert len(r.risk_factors) == 2


def test_packaging_recommendation():
    p = PackagingRecommendation(
        recommended_structure="Phased project fee",
        components=["Phase 1: Discovery", "Phase 2: Build"],
        reasoning="Well-scoped project",
        alternatives=["Fixed fee", "Retainer"],
        confidence=0.85,
    )
    assert p.agent_name == "Packaging Agent"
    assert len(p.components) == 2
    assert len(p.alternatives) == 2


def test_validation_result():
    v = ValidationResult(
        is_valid=True,
        issues=[],
        suggestions=["Consider phased pricing"],
        summary="Pricing looks reasonable.",
    )
    assert v.is_valid
    assert len(v.issues) == 0


def test_pricing_result_full():
    proposals = [
        AgentProposal(
            agent_name="Cost Agent",
            price_floor=10000, price_target=15000, price_stretch=20000,
            reasoning="Cost-based", assumptions=["40hrs"], confidence=0.8,
        ),
        AgentProposal(
            agent_name="Market Agent",
            price_floor=12000, price_target=18000, price_stretch=25000,
            reasoning="Market-based", assumptions=["US rates"], confidence=0.7,
        ),
        AgentProposal(
            agent_name="Value Agent",
            price_floor=15000, price_target=22000, price_stretch=30000,
            reasoning="Value-based", assumptions=["10% of ROI"], confidence=0.6,
        ),
    ]
    risk = RiskAssessment(
        risk_factors=["scope creep"],
        risk_adjustment_pct=10.0,
        reasoning="Low-moderate risk",
        confidence=0.75,
    )
    packaging = PackagingRecommendation(
        recommended_structure="Fixed project fee",
        components=["Full delivery"],
        reasoning="Well-scoped",
        alternatives=["Retainer"],
        confidence=0.8,
    )
    result = PricingResult(
        price_floor=12000,
        price_target=18000,
        price_stretch=25000,
        currency=Currency.USD,
        suggested_structure="Fixed project fee",
        rationale="Balanced across all lenses",
        assumptions=["Standard timeline"],
        risk_factors=["scope creep"],
        confidence=0.75,
        specialist_proposals=proposals,
        risk_assessment=risk,
        packaging=packaging,
    )
    assert result.price_floor < result.price_target < result.price_stretch
    assert result.packaging is not None
    assert len(result.specialist_proposals) == 3
