# Precio - Lessons Learned

## Runtime Environment
- **Context**: User runs Claude Code from WSL2, but the app itself runs on Windows natively
- **Lesson**: Do not add WSL-specific networking hacks. Keep the app Windows-native with localhost:8000
- **Detection**: If "connection refused", check that Python + deps are installed on Windows and run.bat is used

## API Backend
- **Context**: User has OpenRouter key, not Anthropic. Uses openai SDK pointed at OpenRouter.
- **Lesson**: Do not assume Anthropic SDK. The project uses OpenRouter with openai-compatible API.
- **Model**: Configurable via AUTOCOMPRA_LLM_MODEL env var (default: arcee-ai/trinity-large-preview:free)

## Agent JSON Extraction
- **Problem**: Free LLM models produce invalid JSON in multiple ways:
  1. Markdown code block wrapping (`\`\`\`json ... \`\`\``)
  2. Commas in numbers (e.g. `1,088,750.00`)
  3. Truncated responses (model runs out of tokens mid-JSON)
  4. Trailing commas, single quotes, comments
- **Fix**: extract_json() in base.py handles all cases:
  - Strips markdown blocks
  - Removes commas from numbers (`while` loop for multi-comma like `1,088,750`)
  - Progressive line-trimming for truncated JSON (closes open braces/brackets/strings)
  - Regex cleanup for trailing commas, comments, single quotes
- **Lesson**: Free models are unreliable JSON producers. Always build resilient parsing.
- **Mitigation**: Arbiter uses 4096 max_tokens (up from 2048) to reduce truncation frequency.

## Stale __pycache__
- **Problem**: After editing Python files, uvicorn with --reload can still use stale .pyc files
- **Fix**: Delete __pycache__ directories before restarting when debugging
- **Lesson**: When a fix doesn't take effect, clear __pycache__ first

## Arbiter JSON Truncation
- **Problem**: Free models truncate the Arbiter's JSON response mid-string, especially when rationale is a long field placed early in the JSON
- **Fix**: Reorder JSON fields so numeric values come first (prices, confidence) and long text fields last (rationale). Also instruct the model to keep rationale under 200 words and not use commas in numbers.
- **Lesson**: When LLM output is truncated, put the most important fields first in the schema. The truncation repair can recover partial JSON but only if the critical fields are already complete.

## Linux Runtime
- **Context**: User runs Linux natively (not Windows, not WSL)
- **Lesson**: Provide run.sh alongside run.bat. Use python3, venv, and standard Linux paths.
- **Detection**: Check which OS the user is on before assuming Windows-native execution

## Docs Must Stay Current
- **Context**: User explicitly requires all project docs to be perfect and traceable
- **Lesson**: After any code change, update all affected docs before marking work done
- **Docs to check**: PLAN.md, spec.md, pricing-methodology.md, data-model.md, architecture.md, state.md, tasks/todo.md, tasks/lessons.md, validation.md, handoff.md, state/session-summary.md
