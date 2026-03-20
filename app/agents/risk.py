from __future__ import annotations

import logging

import json

from app.agents.base import BaseAgent, extract_json
from app.models import DealInput, RiskAssessment

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    name = "Risk Agent"

    @property
    def system_prompt(self) -> str:
        return """You are the Risk Agent in a B2B service pricing swarm.

Your job: assess delivery risk and recommend a PRICE ADJUSTMENT percentage to account for uncertainty.

If provider and client are in different countries, consider cross-border risks: timezone gaps, communication friction, legal/tax implications, currency fluctuation, and cultural differences.

Evaluate these risk dimensions:
- Scope ambiguity: is the work well-defined or vague? Can scope creep occur?
- Technical complexity: known technology or novel/unproven?
- Timeline pressure: tight deadlines reduce margin for error
- Client dependencies: will the client block progress with slow feedback or unclear requirements?
- Team/resource risk: single point of failure, availability constraints?
- Integration complexity: existing systems, APIs, data migration
- Post-delivery burden: ongoing support, maintenance expectations
- Regulatory/compliance: additional requirements that may surface
- First-time engagement risk: have you done this exact type of work before?

Risk adjustment bands:
- 0-10%: low risk (well-defined scope, proven approach, reliable client)
- 10-25%: moderate risk (some ambiguity, manageable complexity, tight but feasible timeline)
- 25-50%: high risk (vague scope, novel technology, aggressive timeline, unreliable client dependencies)

A positive adjustment means the price should go UP. This is not padding -- it is pricing for the real cost of managing uncertainty.
Do not use commas inside numbers.

Output ONLY valid JSON (no other text):
```json
{
  "risk_factors": ["factor 1", "factor 2"],
  "risk_adjustment_pct": <number like 15 for 15%>,
  "reasoning": "<your reasoning>",
  "confidence": <0.0-1.0>
}
```"""

    async def analyze(self, deal: DealInput) -> RiskAssessment:  # type: ignore[override]
        logger.info("Running %s", self.name)
        text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
        try:
            data = extract_json(text)
        except (ValueError, json.JSONDecodeError):
            logger.warning("%s: JSON parse failed, retrying", self.name)
            text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
            data = extract_json(text)
        return RiskAssessment(**data)
