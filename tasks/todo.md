# Precio - TODO

## Done
- [x] Project structure and setup
- [x] Pydantic data models (DealInput, AgentProposal, RiskAssessment, ValidationResult, PricingResult)
- [x] BaseAgent class with OpenRouter API integration
- [x] Cost Agent with system prompt
- [x] Market Agent with system prompt
- [x] Value Agent with system prompt
- [x] Risk Agent with system prompt and custom output type
- [x] Arbiter Agent (synthesizes specialist proposals, 4096 max_tokens)
- [x] Validator Agent (sanity-checks final output)
- [x] Swarm orchestrator (parallel specialists -> arbiter -> validator)
- [x] FastAPI web app with form input and result display
- [x] Dark theme CSS
- [x] Windows-native run.bat launcher
- [x] All project docs (PLAN, spec, pricing-methodology, data-model, architecture, state, validation, handoff, todo, lessons)
- [x] Switched from Anthropic SDK to OpenRouter (openai SDK)
- [x] Research Agent: auto-populate client context from business URL (scrape + LLM)
- [x] Updated form: business URL replaces manual client context
- [x] Result page shows researched client context
- [x] Graceful fallback when scrape fails (LLM knowledge) or LLM fails (minimal context)
- [x] Resilient JSON parser for free model quirks (commas in numbers, truncation, code blocks)
- [x] Retry logic on JSON parse failures (all agents retry once)
- [x] Error page for graceful failure display
- [x] Arbiter max_tokens increased to 4096
- [x] End-to-end validation (tested: Google, Shopify, Stripe -- all pass)

## Up Next
- [ ] Tune agent system prompts based on output quality
- [ ] Add result persistence (save pricing results to disk)
- [ ] Implement Packaging Agent
- [ ] Add prompt contracts (formal input/output specs per agent)
- [ ] Automated regression tests for pricing quality
- [ ] Run more diverse test cases (training, design, small business)
