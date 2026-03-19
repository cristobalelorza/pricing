from __future__ import annotations

import json
import logging

from app.agents.base import DEFAULT_MODEL, extract_json, get_client
from app.models import (
    AgentProposal,
    DealInput,
    PricingResult,
    RiskAssessment,
)

logger = logging.getLogger(__name__)

ARBITER_SYSTEM_PROMPT = """You are the Arbiter Agent in a B2B service pricing swarm.

You receive independent analyses from specialist agents (Cost, Market, Value, Risk).
Your job: synthesize their inputs into a FINAL pricing recommendation.

Rules:
- Never go below the Cost Agent's floor unless explicitly marked as strategic pricing.
- Weight Value Agent higher when credible ROI evidence exists.
- Weight Market Agent higher when the service is commoditized.
- Apply the Risk Agent's adjustment to the final numbers.
- If specialists disagree significantly, explain why you chose your final numbers.
- Recommend a pricing STRUCTURE (fixed fee, retainer, hybrid, tiered) not just an amount.
- State your assumptions clearly.
- Do not hide uncertainty.

Output ONLY valid JSON with this structure (no other text):
```json
{
  "price_floor": <number>,
  "price_target": <number>,
  "price_stretch": <number>,
  "suggested_structure": "<e.g. Monthly retainer + setup fee>",
  "rationale": "<clear explanation of how you arrived at these numbers>",
  "assumptions": ["assumption 1", "assumption 2"],
  "risk_factors": ["risk 1", "risk 2"],
  "confidence": <0.0-1.0>
}
```"""


class ArbiterAgent:
    name = "Arbiter Agent"
    model = DEFAULT_MODEL

    async def synthesize(
        self,
        deal: DealInput,
        proposals: list[AgentProposal],
        risk: RiskAssessment,
    ) -> PricingResult:
        client = get_client()
        logger.info("Running %s", self.name)

        specialist_text = "\n\n".join(
            f"### {p.agent_name}\n"
            f"- Floor: {p.price_floor:,.2f}\n"
            f"- Target: {p.price_target:,.2f}\n"
            f"- Stretch: {p.price_stretch:,.2f}\n"
            f"- Confidence: {p.confidence}\n"
            f"- Reasoning: {p.reasoning}\n"
            f"- Assumptions: {', '.join(p.assumptions)}"
            for p in proposals
        )

        risk_text = (
            f"### Risk Assessment\n"
            f"- Factors: {', '.join(risk.risk_factors)}\n"
            f"- Suggested adjustment: +{risk.risk_adjustment_pct}%\n"
            f"- Reasoning: {risk.reasoning}\n"
            f"- Confidence: {risk.confidence}"
        )

        user_msg = (
            f"## Deal\n"
            f"**Service:** {deal.service_description}\n"
            f"**Client:** {deal.client_context}\n"
            f"**Constraints:** {deal.constraints or 'None stated'}\n"
            f"**Budget hint:** {f'{deal.budget_hint:,.2f} {deal.currency.value}' if deal.budget_hint else 'None'}\n"
            f"**Currency:** {deal.currency.value}\n\n"
            f"## Specialist Analyses\n\n{specialist_text}\n\n{risk_text}"
        )

        async def _call():
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": ARBITER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            return response.choices[0].message.content

        text = await _call()
        try:
            data = extract_json(text)
        except (ValueError, json.JSONDecodeError):
            logger.warning("Arbiter: JSON parse failed, retrying")
            text = await _call()
            data = extract_json(text)

        # Fill defaults for fields that may be missing from truncation
        data.setdefault("suggested_structure", "Fixed project fee")
        data.setdefault("rationale", "See specialist proposals for details.")
        data.setdefault("assumptions", [])
        data.setdefault("risk_factors", [r for r in risk.risk_factors])
        data.setdefault("confidence", 0.5)

        return PricingResult(
            **data,
            currency=deal.currency,
            specialist_proposals=proposals,
            risk_assessment=risk,
        )
