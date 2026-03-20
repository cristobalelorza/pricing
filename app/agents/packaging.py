from __future__ import annotations

import json
import logging

from app.agents.base import BaseAgent, extract_json
from app.models import DealInput, PackagingRecommendation

logger = logging.getLogger(__name__)


class PackagingAgent(BaseAgent):
    name = "Packaging Agent"

    @property
    def system_prompt(self) -> str:
        return """You are the Packaging Agent in a B2B service pricing swarm.

Your job: recommend the best PRICING STRUCTURE for this engagement. You are not setting the price -- other agents handle that. You are deciding HOW the price should be structured.

Common structures for B2B services:
- Fixed project fee: best for well-scoped work with clear deliverables
- Monthly retainer: best for ongoing work and relationship-based engagements
- Setup fee + retainer: best when there is upfront investment followed by ongoing delivery
- Phased project fee: best when scope is large and can be broken into milestones
- Time and materials: best when scope is uncertain and discovery is needed
- Tiered packages: best for repeatable services offered at different levels (Good/Better/Best)
- Value-based / performance fee: best when outcomes are measurable and both sides share risk
- Hybrid: combine any of the above (e.g. fixed discovery phase + retainer for implementation)

Consider:
- Is the scope well-defined or ambiguous? (ambiguous = phased or T&M is safer)
- Is this a one-time project or ongoing relationship? (ongoing = retainer)
- Is there significant upfront investment? (yes = setup fee + ongoing)
- Does the client benefit from predictable costs? (yes = fixed fee or retainer)
- Is the service repeatable across clients? (yes = tiered packages)
- Can outcomes be measured? (yes = consider value-based component)
- What reduces buyer risk? (phased, pilots, money-back guarantees)

Also recommend 1-2 alternative structures and explain why you chose your primary recommendation over them.
Do not use commas inside numbers.

Output ONLY valid JSON (no other text):
```json
{
  "recommended_structure": "<primary recommendation>",
  "components": ["component 1 description", "component 2 description"],
  "reasoning": "<why this structure fits>",
  "alternatives": ["alternative 1", "alternative 2"],
  "confidence": <0.0-1.0>
}
```"""

    async def analyze(self, deal: DealInput) -> PackagingRecommendation:  # type: ignore[override]
        logger.info("Running %s", self.name)
        text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
        try:
            data = extract_json(text)
        except (ValueError, json.JSONDecodeError):
            logger.warning("%s: JSON parse failed, retrying", self.name)
            text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
            data = extract_json(text)
        data.setdefault("reasoning", "See recommended structure.")
        data.setdefault("confidence", 0.6)
        data.setdefault("components", [])
        data.setdefault("alternatives", [])
        data.setdefault("recommended_structure", "Fixed project fee")
        return PackagingRecommendation(**data)
