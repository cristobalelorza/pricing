# Precio - System Specification

## Purpose
Price B2B services quickly, fairly, and defensibly using an AI agent swarm.

## LLM Backend
- OpenRouter API (OpenAI-compatible via `openai` SDK)
- Model: configurable via `AUTOCOMPRA_LLM_MODEL` env var (default: `arcee-ai/trinity-large-preview:free`)
- Auth: `OPENROUTER_API_KEY` in `.env`

## Input
User provides via web form:
- **business_url** (required): URL of the client's business website (auto-researched by Research Agent)
- **service_description** (required): free-text description of the service being offered
- **constraints** (optional): timeline, budget caps, delivery constraints
- **budget_hint** (optional): numeric budget signal from the client
- **currency** (required, default USD): USD, EUR, CLP, GBP

**client_context** is auto-populated by the Research Agent (scrapes URL + LLM summarization).

## Agent Swarm

### Research Agent (runs first, before swarm)
| Agent | Input | Output | Role |
|-------|-------|--------|------|
| Research Agent | business_url | client_context string | Scrape website + LLM to build client profile |

Fallback: if scrape fails, uses LLM knowledge of the domain. If LLM fails, continues with minimal context.

### Specialist Agents (run in parallel via asyncio.gather)
| Agent | Input | Output | Perspective |
|-------|-------|--------|-------------|
| Cost Agent | DealInput | AgentProposal | Floor price from delivery costs + margin |
| Market Agent | DealInput | AgentProposal | Market-aligned range from benchmarks |
| Value Agent | DealInput | AgentProposal | Value-based price from client ROI |
| Risk Agent | DealInput | RiskAssessment | % adjustment for delivery risk |

### Decision Agents (sequential)
| Agent | Input | Output | Role |
|-------|-------|--------|------|
| Arbiter | DealInput + 3 proposals + risk | PricingResult | Synthesize final recommendation |
| Validator | DealInput + PricingResult | ValidationResult | Sanity-check before presenting |

### Future Agents
| Agent | Status | Role |
|-------|--------|------|
| Packaging Agent | Deferred | Recommend pricing structure (retainer, tiered, hybrid) |

## Output
- **price_floor**: minimum viable price
- **price_target**: recommended price
- **price_stretch**: aspirational price
- **suggested_structure**: pricing format recommendation
- **rationale**: why these numbers
- **assumptions**: what was assumed (stated, not hidden)
- **risk_factors**: identified risks
- **confidence**: 0-1 score
- **specialist_proposals**: individual agent outputs (auditable)
- **risk_assessment**: risk agent output
- **validation**: validator pass/fail with issues and suggestions

## Error Handling
- All agents retry once on JSON parse failure
- Resilient JSON parser handles: commas in numbers, truncated responses, markdown code blocks, trailing commas, single quotes
- Arbiter fills defaults for fields missing due to truncation
- Graceful error page shown on unrecoverable failures (error.html)

## Constraints
- All prices as ranges (floor/target/stretch), never single unexplained numbers
- Assumptions must be explicit, never hidden
- Risk adjustments must be visible, not silently baked in
- Reasoning artifacts preserved for auditability
- No pricing below viable delivery floor unless explicitly strategic
