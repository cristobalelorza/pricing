from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    CLP = "CLP"
    GBP = "GBP"


class DealInput(BaseModel):
    """What the user provides about the deal."""

    service_description: str = Field(
        ..., description="What service is being offered"
    )
    business_url: str = Field(
        ..., description="URL of the client's business website"
    )
    client_context: str = Field(
        default="", description="Auto-populated by Research Agent from business_url"
    )
    constraints: str = Field(
        default="", description="Timeline, budget caps, delivery constraints"
    )
    budget_hint: float | None = Field(
        default=None, description="Optional budget signal from the client"
    )
    currency: Currency = Field(default=Currency.USD)


class AgentProposal(BaseModel):
    """Output from a specialist agent."""

    agent_name: str
    price_floor: float = Field(description="Minimum viable price")
    price_target: float = Field(description="Recommended price")
    price_stretch: float = Field(description="Aspirational / high-value price")
    reasoning: str = Field(description="Why this agent recommends these numbers")
    assumptions: list[str] = Field(
        default_factory=list, description="Key assumptions made"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="0-1 confidence in this estimate"
    )


class RiskAssessment(BaseModel):
    """Output from the Risk Agent."""

    agent_name: str = "Risk Agent"
    risk_factors: list[str]
    risk_adjustment_pct: float = Field(
        description="Suggested % adjustment to price (positive = increase)"
    )
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class ValidationResult(BaseModel):
    """Output from the Validator Agent."""

    is_valid: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    summary: str


class PricingResult(BaseModel):
    """Final pricing recommendation after arbiter + validation."""

    price_floor: float
    price_target: float
    price_stretch: float
    currency: Currency
    suggested_structure: str = Field(
        description="e.g. 'Fixed project fee', 'Monthly retainer + setup fee'"
    )
    rationale: str
    assumptions: list[str]
    risk_factors: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    specialist_proposals: list[AgentProposal]
    risk_assessment: RiskAssessment
    validation: ValidationResult | None = None
