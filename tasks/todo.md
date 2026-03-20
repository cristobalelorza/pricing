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
- [ ] Improve model quality (try paid models for better reasoning)
- [ ] Add multi-currency comparison normalization
- [ ] Add team/stakeholder sharing (shareable result links)
- [ ] Dashboard with pricing analytics across all runs

## Recently Completed
- [x] Model tier system (free/cheap/mid/premium) with UI selector
- [x] Rate limit handling (backoff retries + staggered agent launches for free models)
- [x] History detail view (click any row in /history to see full result)
- [x] PDF export (weasyprint, professional report format, download from result page)
- [x] Comparison view (/compare -- side-by-side two pricing runs)
- [x] Re-run with changes (pre-fills form from a previous result, edit insights and re-price)
- [x] Insights input field (competitive intelligence: current vendors, WTP signals, pain points)
- [x] Negotiation Agent (anchor price, concession ladder, objection responses, tactics)
- [x] Discovery Agent (standard, business-specific, indirect questions + signals to listen for)
- [x] 10-agent swarm: Research + Cost + Market + Value + Risk + Packaging + Negotiation + Discovery + Arbiter + Validator
- [x] 101 automated tests all passing
- [x] SSE streaming progress page (real-time agent status updates in browser)
- [x] Async job architecture (POST /price returns immediately, background processing)
- [x] Ran 3 more diverse test cases (training/Deloitte, small biz/Angie's List, ERP migration/Siemens)
- [x] 89 automated tests all passing (models, JSON parser, contract validation across 6 results)
- [x] Implemented Packaging Agent (recommends pricing structure with components and alternatives)
- [x] Added prompt contracts (prompt-contracts.md -- formal input/output specs per agent)
- [x] Linux launcher (run.sh replaces run.bat for Linux)
- [x] Tuned agent system prompts (all specialist + arbiter prompts improved)
- [x] Added result persistence (JSON files saved to results/ directory)
- [x] Added /history page to view past pricing results
- [x] Fixed Arbiter truncation (reordered JSON fields, increased truncation recovery, added "no commas" instruction)
- [x] Fixed extract_json truncation recovery (increased line trim from 15 to 40, added comma-position fallback)
- [x] Created pricing-strategy skill (combined from two skills.sh sources, tested with 3 evals)
- [x] Fixed run.bat error message (referenced wrong API key name)
