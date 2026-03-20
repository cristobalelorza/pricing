# Session Summary - 2026-03-19 to 2026-03-20

## What happened
1. Analyzed two pricing skills from skills.sh, created a combined pricing-strategy skill
2. Adapted app for Linux (run.sh), tuned all agent prompts
3. Added result persistence, history page, PDF export
4. Implemented Packaging Agent, Negotiation Agent, Discovery Agent (10-agent swarm)
5. Added structured insights form (competitor scraping, cost inputs, delivery speed, client signals)
6. Added business management and service templates with CRUD
7. Built SSE streaming progress page, comparison view, A/B testing
8. Added light/dark mode, search/filter history, notes per result, dashboard
9. Switched from SQLite to Supabase Cloud (PostgreSQL) with SQLite fallback
10. Added auth system (bcrypt + session cookies), freemium credits
11. Added feedback widget on every page
12. Added location-aware pricing (provider + client location)
13. Created Docker deployment, deployed to Railway
14. Set up Railway CLI, configured env vars, verified live deployment
15. Renamed project from Precio to Pricing

## Key decisions
- Supabase Cloud over Docker self-hosted (simpler, free, no maintenance)
- Custom auth over Supabase Auth (already built, simpler)
- Weighted model rotation (nemotron 60%, stepfun 40%) over single-model
- Premium minimax for Arbiter + Negotiation only (cost optimization)
- Shared businesses/services, user-scoped results
- 303 redirects for all POST handlers (not 302)

## Live deployment
- URL: https://web-production-7a5eb.up.railway.app
- Railway project: appealing-quietude
- Supabase project: jkvnlcosnhymvvmwimkl
