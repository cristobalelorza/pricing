# Precio - Handoff

## Current Objective
Tune prompt quality and add result persistence.

## Exact Next Step
1. Run more diverse test cases (training, design, audit) to stress-test prompts
2. Review specialist agent reasoning quality -- are they giving useful, differentiated perspectives?
3. Add result persistence so pricing history is reviewable
4. Consider adding Packaging Agent

## Key Decisions Made
- 7-agent swarm: Research, Cost, Market, Value, Risk, Arbiter, Validator
- Parallel + Arbiter + Validator pattern (per CLAUDE.md default)
- OpenRouter API via openai SDK (model: arcee-ai/trinity-large-preview:free, configurable)
- Research Agent: scrape business URL + LLM profiling (replaces manual client context input)
- FastAPI + Jinja2 for web UI (no SPA complexity)
- Runs on Windows natively via run.bat at localhost:8000
- Resilient JSON parser handles free model quirks (comma numbers, truncation, code blocks)
- All agents retry once on JSON parse failure

## Active Constraints
- App runs on Windows natively (not WSL) -- Python must be installed on Windows
- Free LLM model truncates long responses; arbiter uses 4096 max_tokens to compensate
- No persistence yet -- results shown in browser only, not saved
- No Packaging Agent yet

## Tested and Passing
- Google.com (website redesign): Floor $47.5K / Target $81.2K / Stretch $102.5K
- Shopify.com (API integration): Floor $75K / Target $147K / Stretch $206K
- Stripe.com (security audit): Floor $47.5K / Target $62.5K / Stretch $81.2K
- All passed validation

## Remaining High-Priority Items
- Tune agent system prompts based on output quality
- Add result persistence
- Implement Packaging Agent
- Add prompt contracts
- Automated regression tests for pricing quality
