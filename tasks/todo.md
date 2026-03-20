# Pricing - TODO

## Up Next
- [ ] Test live deployment with real pricing scenarios
- [ ] Enable Supabase RLS (Row Level Security) for production
- [ ] Add password change functionality in settings
- [ ] Mobile responsiveness testing and fixes
- [ ] Team onboarding documentation
- [ ] Improve error messages when agents fail or return empty

## Done (this session, 2026-03-19 to 2026-03-20)
- [x] Deployed to Railway (live at web-production-7a5eb.up.railway.app)
- [x] Supabase Cloud integration (PostgreSQL, tables created via MCP)
- [x] Auth system (bcrypt + signed cookies, login/register/logout)
- [x] Freemium credits (5 free runs, then add own API key)
- [x] Feedback widget on every page (saves to Supabase, export as markdown)
- [x] Feedback admin page (/admin/feedback)
- [x] Docker deployment (Dockerfile + .dockerignore)
- [x] Railway CLI setup and deployment
- [x] Location-aware pricing (provider + client location in all agents)
- [x] Shared businesses and services (all users see them)
- [x] Default admin account (admin/admin, auto-created)
- [x] Structured insights form (competitor scraping, cost inputs, delivery speed, client signals)
- [x] Business management (CRUD, linked pricing history)
- [x] Service templates (CRUD, auto-populate form)
- [x] Negotiation Agent (anchor price, concession ladder, tactics, objection responses)
- [x] Discovery Agent (standard, business-specific, indirect questions + signals)
- [x] Packaging Agent (structure recommendations with alternatives)
- [x] 10-agent swarm with weighted model rotation and fallback chains
- [x] Premium model (minimax) for Arbiter + Negotiation
- [x] Agent reliability (weighted rotation: nemotron 60%, stepfun 40%, arcee fallback)
- [x] SSE streaming progress page
- [x] Light/dark mode toggle (persistent via localStorage)
- [x] PDF export via WeasyPrint
- [x] Comparison view (side-by-side)
- [x] A/B model testing
- [x] Search/filter history with notes
- [x] Dashboard with stats
- [x] Re-run with changes
- [x] Edit/delete businesses and services
- [x] JS auto-populate from service template
- [x] 15 currencies (USD, EUR, GBP, AUD, CAD, CLP, BRL, MXN, JPY, INR, CHF, NZD, SGD, AED, ZAR)
- [x] UI redesign (Dark Terminal Luxury theme with DM Sans + JetBrains Mono)
- [x] Renamed Precio to Pricing
- [x] All agent prompts tuned with location awareness
- [x] Resilient JSON parser (commas, truncation, code blocks, progressive repair)
- [x] Pricing-strategy skill (combined from two skills.sh sources)
- [x] Prompt contracts (prompt-contracts.md)
