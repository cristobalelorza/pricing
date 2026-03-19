from __future__ import annotations

import asyncio
import logging

from app.agents import (
    ArbiterAgent,
    CostAgent,
    MarketAgent,
    RiskAgent,
    ValidatorAgent,
    ValueAgent,
)
from app.models import DealInput, PricingResult

logger = logging.getLogger(__name__)


async def run_swarm(deal: DealInput) -> PricingResult:
    """Run the full pricing swarm: specialists -> arbiter -> validator."""

    cost_agent = CostAgent()
    market_agent = MarketAgent()
    value_agent = ValueAgent()
    risk_agent = RiskAgent()
    arbiter = ArbiterAgent()
    validator = ValidatorAgent()

    # Phase 1: Run all specialists in parallel
    logger.info("Phase 1: Running specialist agents in parallel")
    cost_result, market_result, value_result, risk_result = await asyncio.gather(
        cost_agent.analyze(deal),
        market_agent.analyze(deal),
        value_agent.analyze(deal),
        risk_agent.analyze(deal),
    )

    proposals = [cost_result, market_result, value_result]

    # Phase 2: Arbiter synthesizes
    logger.info("Phase 2: Arbiter synthesizing")
    result = await arbiter.synthesize(deal, proposals, risk_result)

    # Phase 3: Validator sanity-checks
    logger.info("Phase 3: Validator checking")
    validation = await validator.validate(deal, result)
    result.validation = validation

    logger.info(
        "Swarm complete. Target: %s %s, Valid: %s",
        f"{result.price_target:,.2f}",
        result.currency.value,
        validation.is_valid,
    )

    return result
