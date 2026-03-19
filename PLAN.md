# Precio - Implementation Plan

## Current Phase: Working End-to-End, Tuning Next

### What was built
- 7-agent pricing swarm: Research, Cost, Market, Value, Risk, Arbiter, Validator
- Research Agent auto-scrapes business URL and builds client profile via LLM
- Parallel + Arbiter + Validator pattern via asyncio.gather()
- FastAPI web UI with dark theme (form, loading state, result display, error page)
- Pydantic data models for all inputs/outputs
- Resilient JSON parser for free LLM model quirks (comma numbers, truncation, code blocks)
- Retry logic on all agent calls
- Output: floor / target / stretch prices + structure + rationale + assumptions + risk + validation

### Decisions made
- **LLM backend**: OpenRouter API via openai SDK, model configurable via AUTOCOMPRA_LLM_MODEL env var
- **Default model**: arcee-ai/trinity-large-preview:free
- **Swarm pattern**: Parallel + Arbiter + Validator (per CLAUDE.md default)
- **Research method**: scrape URL with requests/BeautifulSoup, then LLM summarization; fallback to LLM knowledge if scrape fails
- **UI**: FastAPI + Jinja2 + vanilla CSS (no JS frameworks)
- **Runtime**: Windows-native via run.bat at localhost:8000
- **Arbiter max_tokens**: 4096 (free model truncates at 2048)
- **No Packaging Agent yet**: deferred until core methodology is validated with more test cases

### What is next
1. Tune agent system prompts based on output quality across more test cases
2. Add result persistence (save pricing results to disk/JSON for review)
3. Implement Packaging Agent (pricing structure recommendations)
4. Add prompt contracts (input/output format guarantees per agent)
5. Automated regression tests for pricing quality

### Open questions
- What margin range should Cost Agent default to? Currently 20-40%.
- Should results persist to JSON files, SQLite, or something else?
- When to promote Packaging Agent from optional to default?
- Should the Research Agent also try to scrape /about and /pricing pages?
