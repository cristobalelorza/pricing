from __future__ import annotations

import asyncio
import logging

from app.agents import (
    ArbiterAgent,
    CostAgent,
    DiscoveryAgent,
    MarketAgent,
    NegotiationAgent,
    PackagingAgent,
    RiskAgent,
    ValidatorAgent,
    ValueAgent,
)
from app.models import DealInput, PricingResult

logger = logging.getLogger(__name__)


async def _noop_status(s: str):
    pass


async def run_swarm_streaming(
    deal: DealInput,
    on_status=None,
) -> PricingResult:
    """Run the full pricing swarm with status callbacks for streaming progress."""
    if on_status is None:
        on_status = _noop_status

    cost_agent = CostAgent()
    market_agent = MarketAgent()
    value_agent = ValueAgent()
    risk_agent = RiskAgent()
    packaging_agent = PackagingAgent()
    negotiation_agent = NegotiationAgent()
    discovery_agent = DiscoveryAgent()
    arbiter = ArbiterAgent()
    validator = ValidatorAgent()

    # Phase 1: Run all specialists in parallel
    await on_status("specialists")
    logger.info("Phase 1: Running specialist agents in parallel")

    _agent_idx = 0

    async def _run_agent(agent, deal, name):
        nonlocal _agent_idx
        # Small stagger so rotation assigns different models before requests fire
        delay = _agent_idx * 0.5
        _agent_idx += 1
        if delay > 0:
            await asyncio.sleep(delay)
        result = await agent.analyze(deal)
        await on_status(f"done:{name}")
        return result

    (
        cost_result, market_result, value_result,
        risk_result, packaging_result,
        negotiation_result, discovery_result,
    ) = await asyncio.gather(
        _run_agent(cost_agent, deal, "Cost Agent"),
        _run_agent(market_agent, deal, "Market Agent"),
        _run_agent(value_agent, deal, "Value Agent"),
        _run_agent(risk_agent, deal, "Risk Agent"),
        _run_agent(packaging_agent, deal, "Packaging Agent"),
        _run_agent(negotiation_agent, deal, "Negotiation Agent"),
        _run_agent(discovery_agent, deal, "Discovery Agent"),
    )

    proposals = [cost_result, market_result, value_result]

    # Phase 2: Arbiter synthesizes
    await on_status("arbiter")
    logger.info("Phase 2: Arbiter synthesizing")
    result = await arbiter.synthesize(deal, proposals, risk_result, packaging_result)
    result.packaging = packaging_result
    result.negotiation = negotiation_result
    result.discovery = discovery_result

    # Phase 3: Validator sanity-checks
    await on_status("validator")
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
