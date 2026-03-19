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

Your job: assess delivery risk and recommend a PRICE ADJUSTMENT percentage.

Consider:
- Scope ambiguity: is the service well-defined or vague?
- Technical complexity and unknowns
- Timeline pressure: tight deadlines increase risk
- Client dependencies: will the client block progress?
- Team availability and capacity
- Integration complexity with existing systems
- Support and maintenance burden post-delivery
- Regulatory or compliance requirements
- Currency and payment risk

A positive adjustment means the price should go UP to account for risk.
Typical adjustments: 0-10% for low risk, 10-25% for moderate, 25-50% for high risk.

Output ONLY valid JSON with this structure (no other text):
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
