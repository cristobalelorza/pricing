# Pricing - Architecture

## System Overview

```
Browser (any device)
    |
    v
Railway (Docker container)
    |
    v
FastAPI (app/main.py) -- serves HTML, handles auth, manages jobs
    |
    +-- Auth middleware (app/auth.py) -- signed session cookies
    |
    +-- Supabase Cloud (PostgreSQL) -- users, businesses, services, results, feedback
    |   (falls back to SQLite for local dev)
    |
    v
Research Agent (app/agents/researcher.py)
  - scrapes business URL + competitor URL with BeautifulSoup
  - LLM summarizes into client_context
  - fallback chain across free models
    |
    v
DealInput + StructuredInsights (client context, competitor intel, cost inputs, location)
    |
    v
Swarm Orchestrator (app/swarm.py) -- SSE streaming progress
    |
    |-- asyncio.gather() with staggered starts (0.5s each)
    |
    |   Weighted model rotation: nemotron 60%, stepfun 40%, arcee fallback
    |
    v                v              v            v            v             v           v
Cost Agent      Market Agent   Value Agent   Risk Agent  Packaging    Negotiation  Discovery
(free model)    (free model)   (free model)  (free)      (free)       (PREMIUM)    (free)
    |                |              |            |            |             |           |
    v                v              v            v            v             v           v
AgentProposal  AgentProposal  AgentProposal  RiskAssess  PackagingRec  NegPlaybook  DiscQuestions
    |                |              |            |            |             |           |
    +----------------+--------------+------------+------------+-------------+-----------+
    |
    v
Arbiter Agent (PREMIUM model -- minimax/minimax-m2.7)
    |
    v
PricingResult (floor/target/stretch + structure + rationale)
    |
    v
Validator Agent (free model with fallback chain)
    |
    v
PricingResult + ValidationResult + NegotiationPlaybook + DiscoveryQuestions
    |
    v
Saved to Supabase (results table, JSONB)
    |
    v
result.html (SSE redirect from progress.html)
```

## Key Design Decisions

### 10-Agent Swarm
- 7 specialists run in parallel (Cost, Market, Value, Risk, Packaging, Negotiation, Discovery)
- Arbiter synthesizes all inputs into final recommendation
- Validator sanity-checks before presenting
- Research runs first (needs URL scrape before specialists)

### Multi-Model Strategy
- Premium (minimax/minimax-m2.7): Arbiter + Negotiation -- critical reasoning agents
- Free models rotate: nemotron (reliable) gets 60%, stepfun (fast) gets 40%
- Arcee as last-resort fallback
- Automatic fallback on empty responses or 429 rate limits

### Database
- Supabase Cloud (PostgreSQL) for production -- persistent, multi-user
- SQLite fallback for local development (no setup needed)
- Toggle via SUPABASE_URL + SUPABASE_KEY env vars
- Businesses and services are shared; results are user-scoped

### Auth
- Custom bcrypt + HMAC-signed session cookies
- Not using Supabase Auth (simpler, already working)
- Freemium: 5 free credits, then users add own OpenRouter key
- Daily rate limit: 20 runs/day

### Location Awareness
- Provider and client locations flow to all agents
- Cost Agent adjusts labor rates for provider location
- Market Agent benchmarks against client's local market
- Risk Agent flags cross-border delivery risks

### Structured Insights
- Compartmentalized form: competitor intel, cost inputs, delivery speed, client signals
- Competitor URL auto-scraped and compared via LLM
- All agents receive structured insights in their prompts

## File Map

| File | Purpose |
|------|---------|
| app/main.py | FastAPI app, all routes, auth routes, job management |
| app/models.py | Pydantic models (DealInput, StructuredInsights, Business, ServiceTemplate, all agent outputs) |
| app/db.py | Database layer (Supabase + SQLite dual backend) |
| app/auth.py | Session auth middleware, cookie signing |
| app/storage.py | Legacy JSON file storage (kept for backward compat) |
| app/swarm.py | Orchestrator (parallel specialists -> arbiter -> validator) |
| app/agents/base.py | BaseAgent, model rotation, fallback chain, JSON parser |
| app/agents/researcher.py | Research Agent: scrape URL + LLM profiling |
| app/agents/cost.py | Cost specialist (location-aware) |
| app/agents/market.py | Market specialist (location-aware) |
| app/agents/value.py | Value specialist (location-aware) |
| app/agents/risk.py | Risk specialist (cross-border aware) |
| app/agents/packaging.py | Packaging specialist |
| app/agents/negotiation.py | Negotiation playbook (premium model) |
| app/agents/discovery.py | Discovery questions generator |
| app/agents/arbiter.py | Synthesizer (premium model) |
| app/agents/validator.py | Sanity checker |
| app/templates/ | 15 Jinja2 templates (form, result, progress, history, dashboard, businesses, services, auth, etc.) |
| static/style.css | Dark Terminal Luxury theme with light mode |
| migrations/001_init.sql | Supabase table creation SQL |
| Dockerfile | Railway deployment |
| Procfile | Process definition |
| railway.json | Railway config |
