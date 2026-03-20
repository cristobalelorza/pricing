# Pricing - Lessons Learned

## Runtime Environment
- **Context**: User runs Linux natively (Kali)
- **Lesson**: Use run.sh with venv. App deploys via Docker on Railway.

## API Backend
- **Context**: Uses OpenRouter API with openai-compatible SDK. Multiple models.
- **Lesson**: Do not assume a single model. The app rotates across free models (stepfun, nemotron, arcee) with premium (minimax) for critical agents.
- **Models configured via .env**: premium, free_main, free_first_fallback, free_second_fallback

## Free Model Rotation
- **Problem**: Free models have rate limits (8-20 req/min). Firing 10 agents in parallel hammers one provider.
- **Fix**: Weighted round-robin rotation: nemotron gets 60% of requests (more reliable), stepfun 40% (faster but returns empty sometimes). Arcee is last-resort fallback only.
- **Lesson**: Never hit a single free model with all agents at once. Rotate and stagger.

## Agent JSON Extraction
- **Problem**: Free LLM models produce invalid JSON (commas in numbers, truncation, code blocks, trailing commas)
- **Fix**: extract_json() in base.py: strips markdown, removes number commas, progressive line-trimming, comma-position fallback, auto-close braces
- **Lesson**: Always build resilient JSON parsing for free models. Put numeric fields first in schema so truncation loses text, not numbers.

## Arbiter Truncation
- **Problem**: Free models truncate long Arbiter responses mid-string
- **Fix**: Reorder JSON fields (prices first, rationale last). Instruct "keep rationale under 200 words" and "no commas in numbers".
- **Lesson**: Most important fields first in the JSON schema. Premium model (minimax) mostly avoids this.

## Truncation Defaults
- **Problem**: All agent models can return truncated JSON missing fields. Pydantic validation crashes.
- **Fix**: Every agent's analyze() method has setdefault() for all optional fields before constructing the Pydantic model.
- **Lesson**: Always add setdefault() for every field that could be truncated. Don't trust the model to always produce complete JSON.

## Supabase Connection
- **Problem**: Supabase new API keys use `sb_secret_...` format, not the old JWT `eyJ...` format. Supabase Python SDK works with both.
- **Fix**: Use the secret key as the SUPABASE_KEY. Works for all REST API operations.
- **Lesson**: The Supabase REST API cannot run raw DDL SQL. Use Supabase MCP or SQL Editor for table creation.

## Supabase MCP
- **Context**: Installed supabase MCP plugin for direct SQL access from Claude
- **Lesson**: Use mcp__supabase__apply_migration for DDL (CREATE TABLE), mcp__supabase__execute_sql for DML (INSERT, UPDATE, SELECT). Need personal access token (sbp_...) not project key.

## Database Env Loading
- **Problem**: db.py loaded before main.py called load_dotenv(), so SUPABASE_URL/KEY were empty
- **Fix**: Add load_dotenv() at the top of db.py itself
- **Lesson**: Any module that reads env vars at import time must call load_dotenv() itself.

## Auth Redirect
- **Problem**: Login redirect used HTTP 302, causing browsers to re-POST to /dashboard (405 Method Not Allowed)
- **Fix**: Use 303 See Other (forces GET on redirect)
- **Lesson**: Always use 303 for POST->redirect->GET flows, never 302.

## Login Form Validation
- **Problem**: HTML type="email" prevented logging in as "admin" (not an email)
- **Fix**: Changed to type="text" for the login/register email field
- **Lesson**: If usernames and emails are both valid, use type="text" not type="email".

## Railway Deployment
- **Context**: App deployed via Railway CLI
- **Railway CLI location**: ~/.local/bin/railway
- **Deploy command**: ~/.local/bin/railway up --service web
- **Env vars**: Set via railway variables set (not from .env file)
- **Lesson**: Railway can't auto-read .env from git (security). Set vars via CLI or dashboard.
