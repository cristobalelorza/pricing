from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.models import AgentProposal, DealInput

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# --- Model configuration ---
# Premium model (used for critical agents: Arbiter, Negotiation)
PREMIUM_MODEL = os.getenv("premium", "minimax/minimax-m2.7")

# Free models -- rotated across agents to avoid overusing any single one.
# Order: main (best), first fallback, second fallback (worst).
FREE_MODELS = [
    os.getenv("free_main", "stepfun/step-3.5-flash:free"),
    os.getenv("free_first_fallback", "nvidia/nemotron-3-super-120b-a12b:free"),
    os.getenv("free_second_fallback", "arcee-ai/trinity-large-preview:free"),
]
FREE_MODELS = [m for m in FREE_MODELS if m]

DEFAULT_MODEL = FREE_MODELS[0] if FREE_MODELS else "arcee-ai/trinity-large-preview:free"

# Weighted rotation: nemotron (reliable) gets more share than stepfun (fast but flaky).
# Pattern: nemotron, stepfun, nemotron, nemotron, stepfun -- roughly 60/40.
# Arcee is last-resort fallback only.
_rotation_idx = 0

def _build_weighted_rotation() -> list[str]:
    """Build a weighted rotation favoring the more reliable model."""
    if len(FREE_MODELS) < 2:
        return FREE_MODELS
    main, fallback1 = FREE_MODELS[0], FREE_MODELS[1]
    # fallback1 (nemotron) is more reliable, main (stepfun) is faster but flaky
    return [fallback1, main, fallback1, fallback1, main]

_ROTATION_SEQUENCE = _build_weighted_rotation()


def next_free_model() -> str:
    """Return the next free model in weighted rotation."""
    global _rotation_idx
    if not _ROTATION_SEQUENCE:
        return DEFAULT_MODEL
    model = _ROTATION_SEQUENCE[_rotation_idx % len(_ROTATION_SEQUENCE)]
    _rotation_idx += 1
    return model


# Legacy compat
MODEL_TIERS = {
    "free": DEFAULT_MODEL,
    "premium": PREMIUM_MODEL,
}


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
    return _client


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, resilient to common LLM output issues."""
    if not text:
        raise ValueError("Empty LLM response -- cannot extract JSON")
    # Strip markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fix common LLM JSON issues:
    cleaned = text
    # Fix numbers with commas like 1,088,750.00 -> 1088750.00 (repeat until stable)
    while re.search(r"(\d),(\d)", cleaned):
        cleaned = re.sub(r"(\d),(\d)", r"\1\2", cleaned)
    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    # Remove single-line comments
    cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
    # Replace single quotes with double quotes (but not inside strings)
    cleaned = cleaned.replace("'", '"')
    # Remove <number> placeholders that some models leave
    cleaned = re.sub(r"<[^>]+>", "0", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Last resort: find the first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Handle truncated JSON: progressively trim from the end until parseable
    if "{" in cleaned:
        # Find where JSON object starts
        start = cleaned.index("{")
        body = cleaned[start:]

        # Try trimming lines from the end until we can close it
        lines = body.split("\n")
        for trim in range(min(len(lines), 40)):
            attempt = "\n".join(lines[: len(lines) - trim])
            attempt = attempt.rstrip().rstrip(",")
            # Strip trailing incomplete key-value pairs (e.g. truncated mid-key or mid-value)
            attempt = re.sub(r',\s*"[^"]*$', '', attempt)
            # Close any open strings, arrays, objects
            open_braces = attempt.count("{") - attempt.count("}")
            open_brackets = attempt.count("[") - attempt.count("]")
            # Check for unterminated string (odd number of unescaped quotes)
            quote_count = len(re.findall(r'(?<!\\)"', attempt))
            if quote_count % 2 != 0:
                attempt += '"'
            attempt += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
            try:
                return json.loads(attempt)
            except json.JSONDecodeError:
                continue

        # More aggressive: try truncating at each comma position from the end
        for i in range(len(body) - 1, 0, -1):
            if body[i] == ',':
                attempt = body[:i].rstrip()
                open_braces = attempt.count("{") - attempt.count("}")
                open_brackets = attempt.count("[") - attempt.count("]")
                quote_count = len(re.findall(r'(?<!\\)"', attempt))
                if quote_count % 2 != 0:
                    attempt += '"'
                attempt += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
                try:
                    return json.loads(attempt)
                except json.JSONDecodeError:
                    continue

    logger.error("Failed to parse JSON from LLM response:\n%s", text[:500])
    raise ValueError(f"Could not extract valid JSON from LLM response")


class BaseAgent(ABC):
    """Base class for specialist pricing agents."""

    name: str = "BaseAgent"
    model_tier: str = "free"  # "free" or "premium"

    @property
    def model(self) -> str:
        if self.model_tier == "premium":
            return PREMIUM_MODEL
        return next_free_model()

    def _get_fallback_models(self, primary: str) -> list[str]:
        """Ordered fallback list starting from the given primary model."""
        if self.model_tier == "premium":
            return [PREMIUM_MODEL]
        # Start with the assigned model, then the rest of FREE_MODELS in order
        fallbacks = [primary]
        for m in FREE_MODELS:
            if m not in fallbacks:
                fallbacks.append(m)
        return fallbacks

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def _build_user_message(self, deal: DealInput) -> str:
        parts = [
            f"## Service Description\n{deal.service_description}",
            f"## Client Context\n{deal.client_context}",
        ]
        if deal.constraints:
            parts.append(f"## Constraints\n{deal.constraints}")
        if deal.budget_hint is not None:
            parts.append(
                f"## Budget Signal\nClient hinted at a budget of {deal.budget_hint:,.2f} {deal.currency.value}"
            )

        # Structured insights (compartmentalized)
        si = deal.structured_insights
        if si:
            intel_parts = []

            # Our cost basis
            if si.our_hours_estimate or si.our_hourly_rate:
                cost_lines = []
                if si.our_hours_estimate:
                    cost_lines.append(f"- Estimated hours to deliver: {si.our_hours_estimate}")
                if si.our_hourly_rate:
                    cost_lines.append(f"- Our hourly rate (opportunity cost): {si.our_hourly_rate} {deal.currency.value}/hr")
                intel_parts.append("### Our Cost Basis\n" + "\n".join(cost_lines))

            # Delivery speed
            if si.delivery_speed == "fast" and si.fast_delivery_days:
                intel_parts.append(
                    f"### Delivery Timeline\n"
                    f"- Speed: FAST (urgent)\n"
                    f"- Fast delivery: {si.fast_delivery_days} days\n"
                    f"- Normal delivery would be: {si.normal_delivery_days or 'not specified'} days\n"
                    f"- Urgency premium should be applied."
                )
            elif si.normal_delivery_days:
                intel_parts.append(
                    f"### Delivery Timeline\n"
                    f"- Speed: Normal\n"
                    f"- Timeline: {si.normal_delivery_days} days"
                )

            # Competitor intelligence
            if si.has_competitor:
                comp_lines = ["### Competitor Service"]
                if si.competitor_url:
                    comp_lines.append(f"- Competitor URL: {si.competitor_url}")
                if si.competitor_monthly_price is not None:
                    comp_lines.append(f"- Client pays competitor: {si.competitor_monthly_price:,.2f} {deal.currency.value}/month")
                if si.competitor_likes:
                    comp_lines.append(f"- What client likes about competitor: {si.competitor_likes}")
                if si.competitor_dislikes:
                    comp_lines.append(f"- What client dislikes/missing: {si.competitor_dislikes}")
                if si.competitor_features:
                    comp_lines.append(f"- Competitor features (scraped): {si.competitor_features[:500]}")
                intel_parts.append("\n".join(comp_lines))

            # Client signals
            signal_lines = []
            if si.wtp_signals:
                signal_lines.append(f"- WTP signals: {si.wtp_signals}")
            if si.owner_priorities:
                signal_lines.append(f"- Owner priorities: {', '.join(si.owner_priorities)}")
            if si.deal_breakers:
                signal_lines.append(f"- Deal breakers: {si.deal_breakers}")
            if signal_lines:
                intel_parts.append("### Client Signals\n" + "\n".join(signal_lines))

            if si.additional_notes:
                intel_parts.append(f"### Additional Notes\n{si.additional_notes}")

            if intel_parts:
                parts.append("## Competitive Intelligence\n" + "\n\n".join(intel_parts))

        # Legacy plain-text insights (backward compat)
        elif deal.insights:
            parts.append(
                f"## Competitive Intelligence\n"
                f"The following insights are known about this client.\n\n"
                f"{deal.insights}"
            )

        parts.append(f"## Currency\nProvide all prices in {deal.currency.value}.")
        return "\n\n".join(parts)

    async def _call_llm(self, system: str, user_msg: str) -> str:
        """Call LLM with round-robin model selection and fallback chain."""
        client = get_client()
        primary = self.model  # picks via rotation for free tier
        models = self._get_fallback_models(primary)
        last_error = None

        for model_idx, model_id in enumerate(models):
            for attempt in range(2):
                try:
                    response = await client.chat.completions.create(
                        model=model_id,
                        max_tokens=2048,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_msg},
                        ],
                    )
                    text = response.choices[0].message.content
                    if text and text.strip():
                        if model_idx > 0:
                            logger.info("%s: succeeded with fallback %s", self.name, model_id)
                        return text
                    logger.warning("%s: empty from %s, trying next", self.name, model_id)
                    break  # empty response -> move to next model, don't retry same
                except Exception as e:
                    last_error = e
                    if "429" in str(e):
                        if attempt == 0:
                            await asyncio.sleep(3)
                            continue
                        logger.warning("%s: rate limited on %s, falling back", self.name, model_id)
                        break  # move to next model
                    raise

        if last_error:
            raise last_error
        return ""

    async def analyze(self, deal: DealInput) -> AgentProposal:
        logger.info("Running %s", self.name)
        text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
        try:
            data = extract_json(text)
        except (ValueError, json.JSONDecodeError):
            logger.warning("%s: JSON parse failed, retrying", self.name)
            text = await self._call_llm(self.system_prompt, self._build_user_message(deal))
            data = extract_json(text)
        data["agent_name"] = self.name
        return AgentProposal(**data)
