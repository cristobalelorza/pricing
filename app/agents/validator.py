from __future__ import annotations

import json
import logging

from app.agents.base import DEFAULT_MODEL, extract_json, get_client
from app.models import DealInput, PricingResult, ValidationResult

logger = logging.getLogger(__name__)

VALIDATOR_SYSTEM_PROMPT = """You are the Validator Agent in a B2B service pricing swarm.

You receive a final pricing recommendation from the Arbiter and the original deal input.
Your job: sanity-check the recommendation before it is presented.

Check for:
1. Is the floor price viable? Would delivering at this price lose money?
2. Is the target price defensible? Does the rationale support the number?
3. Is the stretch price realistic or fantasy?
4. Are assumptions stated clearly, not hidden?
5. Are risk adjustments visible, not silently baked in?
6. Does the suggested pricing structure make sense for this type of service?
7. Is the confidence level appropriate given the available information?
8. Would a commercially literate operator approve this output?

Output ONLY valid JSON with this structure (no other text):
```json
{
  "is_valid": <true or false>,
  "issues": ["issue 1 if any"],
  "suggestions": ["suggestion 1 if any"],
  "summary": "<one paragraph assessment>"
}
```

Be honest. If it looks good, say so. If something is off, flag it clearly."""


class ValidatorAgent:
    name = "Validator Agent"
    model = DEFAULT_MODEL

    async def validate(
        self,
        deal: DealInput,
        result: PricingResult,
    ) -> ValidationResult:
        client = get_client()
        logger.info("Running %s", self.name)

        user_msg = (
            f"## Original Deal\n"
            f"**Service:** {deal.service_description}\n"
            f"**Client:** {deal.client_context}\n"
            f"**Constraints:** {deal.constraints or 'None stated'}\n"
            f"**Budget hint:** {f'{deal.budget_hint:,.2f} {deal.currency.value}' if deal.budget_hint else 'None'}\n\n"
            f"## Arbiter Recommendation\n"
            f"- Floor: {result.price_floor:,.2f} {result.currency.value}\n"
            f"- Target: {result.price_target:,.2f} {result.currency.value}\n"
            f"- Stretch: {result.price_stretch:,.2f} {result.currency.value}\n"
            f"- Structure: {result.suggested_structure}\n"
            f"- Confidence: {result.confidence}\n"
            f"- Rationale: {result.rationale}\n"
            f"- Assumptions: {', '.join(result.assumptions)}\n"
            f"- Risk factors: {', '.join(result.risk_factors)}"
        )

        async def _call():
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": VALIDATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            return response.choices[0].message.content

        text = await _call()
        try:
            data = extract_json(text)
        except (ValueError, json.JSONDecodeError):
            logger.warning("Validator: JSON parse failed, retrying")
            text = await _call()
            data = extract_json(text)

        return ValidationResult(**data)
