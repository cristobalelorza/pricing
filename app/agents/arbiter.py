from __future__ import annotations

import asyncio
import json
import logging

from app.agents.base import PREMIUM_MODEL, extract_json, get_client
from app.models import (
    AgentProposal,
    DealInput,
    PackagingRecommendation,
    PricingResult,
    RiskAssessment,
)

logger = logging.getLogger(__name__)

ARBITER_SYSTEM_PROMPT = """You are the Arbiter Agent in a B2B service pricing swarm.

You receive independent analyses from specialist agents (Cost, Market, Value, Risk).
Your job: synthesize their inputs into a FINAL pricing recommendation.

Synthesis rules:
- Never go below the Cost Agent's floor unless explicitly marked as strategic pricing.
- Weight Value Agent higher when credible ROI evidence exists.
- Weight Market Agent higher when the service is commoditized.
- Apply the Risk Agent's percentage adjustment to the final numbers.
- If specialists disagree significantly, explain the tension in your rationale.
- Use the Packaging Agent's structure recommendation as your primary guide for the suggested_structure field.
- Do not use commas inside numbers. Write 50000 not 50,000.

Output ONLY valid JSON. Put numeric fields first, text fields last. Keep rationale under 200 words.
```json
{
  "price_floor": <number>,
  "price_target": <number>,
  "price_stretch": <number>,
  "confidence": <0.0-1.0>,
  "suggested_structure": "<e.g. Monthly retainer + setup fee>",
  "risk_factors": ["risk 1", "risk 2"],
  "assumptions": ["assumption 1", "assumption 2"],
  "rationale": "<concise explanation of how you arrived at these numbers>"
}
```"""


class ArbiterAgent:
    name = "Arbiter Agent"
    model = PREMIUM_MODEL

    async def synthesize(
        self,
        deal: DealInput,
        proposals: list[AgentProposal],
        risk: RiskAssessment,
        packaging: PackagingRecommendation | None = None,
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

        packaging_text = ""
        if packaging:
            packaging_text = (
                f"\n\n### Packaging Recommendation\n"
                f"- Structure: {packaging.recommended_structure}\n"
                f"- Components: {', '.join(packaging.components)}\n"
                f"- Reasoning: {packaging.reasoning}\n"
                f"- Alternatives: {', '.join(packaging.alternatives)}\n"
                f"- Confidence: {packaging.confidence}"
            )

        user_msg = (
            f"## Deal\n"
            f"**Service:** {deal.service_description}\n"
            f"**Client:** {deal.client_context}\n"
            f"**Constraints:** {deal.constraints or 'None stated'}\n"
            f"**Budget hint:** {f'{deal.budget_hint:,.2f} {deal.currency.value}' if deal.budget_hint else 'None'}\n"
            f"**Currency:** {deal.currency.value}\n\n"
            f"## Specialist Analyses\n\n{specialist_text}\n\n{risk_text}{packaging_text}"
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

        text = None
        for attempt in range(3):
            try:
                text = await _call()
                if text and text.strip():
                    break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    await asyncio.sleep((attempt + 1) * 3)
                    continue
                raise

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
