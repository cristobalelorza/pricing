# Precio - Handoff

## Current Objective
Model upgrade and advanced features.

## Exact Next Step
1. Switch to a better LLM model for higher quality outputs
2. Add comparison view (compare two pricing runs side by side)
3. Add result detail view from history page
4. Export pricing results as PDF or formatted report

## Key Decisions Made
- 7-agent swarm: Research, Cost, Market, Value, Risk, Arbiter, Validator
- Parallel + Arbiter + Validator pattern (per CLAUDE.md default)
- OpenRouter API via openai SDK (model: arcee-ai/trinity-large-preview:free, configurable)
- Research Agent: scrape business URL + LLM profiling (replaces manual client context input)
- FastAPI + Jinja2 for web UI (no SPA complexity)
- Linux-native via run.sh (run.bat kept for Windows)
- Resilient JSON parser handles free model quirks (comma numbers, truncation, code blocks)
- All agents retry once on JSON parse failure
- Results persisted as JSON to results/ directory
- Pricing-strategy skill created from two skills.sh sources (used to inform agent prompts)
- 8-agent swarm: Research, Cost, Market, Value, Risk, Packaging, Arbiter, Validator
- Packaging Agent runs in parallel with specialists, feeds into Arbiter
- Prompt contracts defined in prompt-contracts.md
- 89 automated tests (models, JSON parser, contract validation across 6 saved results)
- SSE streaming progress page with real-time agent status updates
- Async job architecture (POST returns immediately, background swarm)
- sse-starlette dependency added

## Active Constraints
- Free LLM model truncates long responses; arbiter uses 4096 max_tokens + field reordering to compensate

## Tested and Passing
- Google.com (website redesign): Floor $47.5K / Target $81.2K / Stretch $102.5K
- Shopify.com (API integration): Floor $75K / Target $147K / Stretch $206K
- Stripe.com (security audit): Floor $47.5K / Target $62.5K / Stretch $81.2K
- HubSpot.com (AI workshop): Floor $18K / Target $26K / Stretch $34K
- Notion.so (brand redesign): Floor $60K / Target $90K / Stretch $120K
- Deloitte.com (AI training): Floor $14K / Target $21K / Stretch $26K
- AngiesList.com (WordPress redesign): Floor $5.25K / Target $7K / Stretch $8.75K (validation failed -- correctly flagged overpricing vs budget)
- Siemens.com (ERP migration): Floor $1.875M / Target $2.625M / Stretch $3.375M EUR
- Chipotle.com (mobile app MVP): Floor $231K / Target $375K / Stretch $481K
- 7/8 passed validation (1 intentionally flagged by Validator)

## Remaining High-Priority Items
- Better LLM model for higher quality outputs
- Comparison view for pricing runs
- Result detail view from history page
- PDF/report export
