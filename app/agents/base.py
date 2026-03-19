from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.models import AgentProposal, DealInput

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

DEFAULT_MODEL = os.getenv("AUTOCOMPRA_LLM_MODEL", "arcee-ai/trinity-large-preview:free")


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
        for trim in range(min(len(lines), 15)):
            attempt = "\n".join(lines[: len(lines) - trim])
            attempt = attempt.rstrip().rstrip(",")
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

    logger.error("Failed to parse JSON from LLM response:\n%s", text[:500])
    raise ValueError(f"Could not extract valid JSON from LLM response")


class BaseAgent(ABC):
    """Base class for specialist pricing agents."""

    name: str = "BaseAgent"
    model: str = DEFAULT_MODEL

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
        parts.append(f"## Currency\nProvide all prices in {deal.currency.value}.")
        return "\n\n".join(parts)

    async def _call_llm(self, system: str, user_msg: str) -> str:
        """Call LLM and return raw text response. Retries once on failure."""
        client = get_client()
        for attempt in range(2):
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
            )
            text = response.choices[0].message.content
            if text and text.strip():
                return text
            logger.warning("%s: empty response on attempt %d", self.name, attempt + 1)
        return text or ""

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
