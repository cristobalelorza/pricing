from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.agents.base import FREE_MODELS, extract_json, get_client, next_free_model

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are a Business Research Agent. Given scraped content from a company's website, produce a concise client profile.

Extract and infer:
- Company name
- Industry / sector
- Company size (employees, revenue tier if visible; estimate if not)
- What they do (core products/services)
- Geographic focus (where they operate)
- Likely pain points or reasons they might need external services
- Any other relevant business context

If the scraped content is limited or unclear, make reasonable inferences from the domain name and whatever is available. State when you are inferring vs. when you have direct evidence.

Output a clear, structured paragraph that a pricing analyst can use to understand this client. Do NOT output JSON -- output plain text, 150-300 words."""

FALLBACK_SYSTEM_PROMPT = """You are a Business Research Agent. The user will give you a business URL or name. Based on your knowledge, produce a concise client profile.

Estimate:
- Company name (from the domain)
- Likely industry / sector
- Probable company size
- What they likely do
- Geographic focus
- Likely pain points

Be honest about what you're estimating vs. what you know. Output plain text, 150-300 words."""

MAX_SCRAPE_CHARS = 4000
REQUEST_TIMEOUT = 10


def _scrape_url(url: str) -> str | None:
    """Fetch a URL and extract visible text content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script, style, nav, footer noise
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    # Extract useful pieces
    parts = []

    title = soup.title
    if title:
        parts.append(f"Page title: {title.get_text(strip=True)}")

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        parts.append(f"Description: {meta_desc['content']}")

    # Headings
    for h in soup.find_all(["h1", "h2", "h3"], limit=10):
        text = h.get_text(strip=True)
        if text:
            parts.append(text)

    # Main body text
    body_text = soup.get_text(separator="\n", strip=True)
    parts.append(body_text)

    combined = "\n".join(parts)
    return combined[:MAX_SCRAPE_CHARS]


class ResearcherAgent:
    name = "Research Agent"

    async def research(self, business_url: str) -> str:
        """Scrape a business URL and produce a client profile via LLM."""
        logger.info("Researching business: %s", business_url)

        scraped = _scrape_url(business_url)

        client = get_client()

        if scraped:
            domain = urlparse(
                business_url if "://" in business_url else f"https://{business_url}"
            ).netloc
            user_msg = (
                f"Business URL: {business_url}\n"
                f"Domain: {domain}\n\n"
                f"## Scraped Website Content\n{scraped}"
            )
            system = RESEARCH_SYSTEM_PROMPT
        else:
            logger.info("Scrape failed, falling back to LLM knowledge for %s", business_url)
            user_msg = f"Business URL: {business_url}\nThe website could not be scraped. Use your knowledge to estimate a client profile."
            system = FALLBACK_SYSTEM_PROMPT

        # Try models with fallback chain
        for model_id in FREE_MODELS:
            try:
                response = await client.chat.completions.create(
                    model=model_id,
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_msg},
                    ],
                )
                text = response.choices[0].message.content
                if text and text.strip():
                    logger.info("Research complete for %s (%d chars, model: %s)", business_url, len(text.strip()), model_id)
                    return text.strip()
                logger.warning("Research: empty from %s, trying next", model_id)
            except Exception as e:
                logger.warning("Research: %s failed (%s), trying next", model_id, e)
                continue

        return f"Research failed for {business_url}. Pricing agents should work with limited context."
