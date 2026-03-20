# Pricing - Current State

## Status: Deployed and Live

### Live URL
https://web-production-7a5eb.up.railway.app

### Architecture
- **App**: FastAPI + Jinja2 (Python), deployed on Railway via Docker
- **Database**: Supabase Cloud (PostgreSQL), with SQLite fallback for local dev
- **LLM**: OpenRouter API (10 agents, weighted model rotation with fallback chain)
- **Auth**: Custom bcrypt + signed session cookies
- **Default account**: admin / admin (9999 credits)

### What exists
- 10 LLM agents: Research, Cost, Market, Value, Risk, Packaging, Negotiation, Discovery, Arbiter, Validator
- Structured insights form (competitor scraping, cost inputs, delivery speed, client signals)
- Business management (shared across all users, persistent in Supabase)
- Service templates (reusable, shared across all users)
- Negotiation playbook (anchor price, concession ladder, objection responses, tactics)
- Discovery questions (standard, business-specific, indirect, signals to listen for)
- Location-aware pricing (provider + client location adjusts all agent outputs)
- SSE streaming progress page (real-time agent status updates)
- PDF export via WeasyPrint
- Comparison view (side-by-side two results)
- A/B model testing (premium vs free)
- Feedback/bug report widget on every page
- Light/dark mode toggle (persistent via localStorage)
- Search/filter history with notes per result
- Dashboard with stats and recent runs
- Freemium credit system (5 free runs, then add own API key)

### Tech Stack
- Python 3.13, FastAPI, Jinja2, Pydantic
- Supabase Cloud (PostgreSQL) via supabase-py SDK
- OpenRouter API via openai SDK
- WeasyPrint for PDF generation
- bcrypt for password hashing
- sse-starlette for SSE streaming
- Docker for deployment
- Railway for hosting

### Last updated
- Date: 2026-03-20
- Deployed to Railway, Supabase tables created via MCP
- All env vars set on Railway
