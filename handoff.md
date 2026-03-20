# Pricing - Handoff

## Current Objective
App is deployed and live. Focus on testing with real deals, polishing UX, and team onboarding.

## Exact Next Step
1. Test the live deployment with a real pricing scenario
2. Have team members register and try it
3. Review feedback from the feedback widget
4. Polish any UX issues found during real use

## Key Decisions Made
- 10-agent swarm: Research, Cost, Market, Value, Risk, Packaging, Negotiation, Discovery, Arbiter, Validator
- Parallel + Arbiter + Validator pattern
- OpenRouter API with weighted model rotation (nemotron 60%, stepfun 40%, arcee fallback)
- Premium model (minimax/minimax-m2.7) for Arbiter + Negotiation agents
- Supabase Cloud for database (PostgreSQL), SQLite fallback for local dev
- Custom auth with bcrypt (not Supabase Auth)
- Businesses and services are shared across all users; results are user-scoped
- Railway for deployment with Docker
- Structured insights replace single textarea (competitor scraping, cost inputs, delivery speed, client signals)
- Location-aware pricing (provider + client location)
- Freemium: 5 free runs, then add own OpenRouter key

## Infrastructure
- **Live URL**: https://web-production-7a5eb.up.railway.app
- **Database**: Supabase project jkvnlcosnhymvvmwimkl
- **Railway project**: appealing-quietude (service: web)
- **Railway CLI**: ~/.local/bin/railway (logged in as Cristobal Elorza)
- **Deploy command**: ~/.local/bin/railway up --service web

## Remaining High-Priority Items
- Enable RLS (Row Level Security) on Supabase tables for production security
- Add password change functionality
- Improve error messages when agents fail
- Add loading states for business/service CRUD
- Mobile responsiveness testing
- Team onboarding documentation
