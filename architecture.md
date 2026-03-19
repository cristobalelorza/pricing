# Precio - Architecture

## System Overview

```
Browser (Windows)
    |
    v
FastAPI (app/main.py) -- serves HTML + handles form POST
    |
    v
Research Agent (app/agents/researcher.py)
  - scrapes business URL with requests + BeautifulSoup
  - LLM summarizes into client_context
  - fallback to LLM knowledge if scrape fails
    |
    v
DealInput (client_context auto-populated)
    |
    v
Swarm Orchestrator (app/swarm.py)
    |
    |-- asyncio.gather() --------+----------+----------+
    |                            |          |          |
    v                            v          v          v
Cost Agent                 Market Agent  Value Agent  Risk Agent
(app/agents/cost.py)       (market.py)  (value.py)   (risk.py)
    |                            |          |          |
    v                            v          v          v
AgentProposal              AgentProposal  AgentProposal  RiskAssessment
    |                            |          |          |
    +----------------------------+----------+----------+
    |
    v
Arbiter Agent (app/agents/arbiter.py)
    |
    v
PricingResult
    |
    v
Validator Agent (app/agents/validator.py)
    |
    v
PricingResult + ValidationResult
    |
    v
result.html (rendered and returned to browser)
    |
    (on error) --> error.html
```

## Key Design Decisions

### Parallel + Arbiter + Validator
- Specialists work independently to avoid anchoring bias
- Parallel execution via asyncio.gather() for speed (~30-60s total)
- Arbiter synthesizes after seeing all perspectives
- Validator catches issues before presenting to user

### LLM Backend
- OpenRouter API (OpenAI-compatible) via `openai` SDK
- Default model: `arcee-ai/trinity-large-preview:free` (configurable via AUTOCOMPRA_LLM_MODEL env var)
- Can switch to any OpenRouter model by changing the env var

### Resilient JSON Parsing
- Free models produce invalid JSON: commas in numbers, truncated responses, code blocks
- extract_json() in base.py handles all cases with progressive repair
- All agents retry once on JSON parse failure

### Shared Infrastructure
- BaseAgent class (app/agents/base.py): shared OpenRouter API call logic, JSON extraction, retry
- Single AsyncOpenAI client (module-level singleton, pointed at OpenRouter)
- All agents receive the same DealInput, produce typed Pydantic outputs

### Web Layer
- FastAPI for async request handling
- Jinja2 templates (no SPA, no JS framework)
- Static CSS (dark theme)
- Runs on Windows natively via `run.bat` at http://localhost:8000

## File Map

| File | Purpose |
|------|---------|
| app/main.py | FastAPI app, routes, startup |
| app/models.py | Pydantic data models |
| app/swarm.py | Orchestrator (parallel -> arbiter -> validator) |
| app/agents/base.py | BaseAgent class, API client, JSON parser |
| app/agents/researcher.py | Research Agent: scrape URL + LLM client profiling |
| app/agents/cost.py | Cost specialist |
| app/agents/market.py | Market specialist |
| app/agents/value.py | Value specialist |
| app/agents/risk.py | Risk specialist |
| app/agents/arbiter.py | Synthesizer |
| app/agents/validator.py | Sanity checker |
| app/templates/index.html | Input form |
| app/templates/result.html | Pricing result display |
| app/templates/error.html | Error display |
| app/templates/base.html | Layout |
| static/style.css | UI styling |
| run.bat | Windows launch script |
