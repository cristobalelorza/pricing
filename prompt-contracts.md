# Precio - Prompt Contracts

Formal input/output specifications for each agent in the pricing swarm.

## Research Agent

**Input**: `business_url` (string)
**Output**: Plain text client profile (150-300 words)
**Fallback**: If scrape fails, uses LLM knowledge. If LLM fails, returns minimal context string.

| Field | Type | Required |
|-------|------|----------|
| output | str | yes |

**Guarantees**:
- Always returns a string (never None)
- Max ~300 words
- States when inferring vs having direct evidence

---

## Cost Agent

**Input**: DealInput (full deal context)
**Output**: AgentProposal

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| price_floor | float | yes | > 0 |
| price_target | float | yes | >= price_floor |
| price_stretch | float | yes | >= price_target |
| reasoning | str | yes | non-empty |
| assumptions | list[str] | yes | at least 1 |
| confidence | float | yes | 0.0-1.0 |

**Guarantees**:
- Floor is based on actual cost estimation (labor + materials + overhead + margin)
- Target includes 25-35% margin
- Stretch includes 40%+ margin
- Assumptions include at least: roles/hours, margin percentage, timeline

---

## Market Agent

**Input**: DealInput (full deal context)
**Output**: AgentProposal

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| price_floor | float | yes | > 0 |
| price_target | float | yes | >= price_floor |
| price_stretch | float | yes | >= price_target |
| reasoning | str | yes | non-empty |
| assumptions | list[str] | yes | at least 1 |
| confidence | float | yes | 0.0-1.0 |

**Guarantees**:
- Prices based on market benchmarks, not internal costs
- Reasoning references comparable services or industry rates
- Does not blindly copy a single competitor

---

## Value Agent

**Input**: DealInput (full deal context)
**Output**: AgentProposal

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| price_floor | float | yes | > 0 |
| price_target | float | yes | >= price_floor |
| price_stretch | float | yes | >= price_target |
| reasoning | str | yes | non-empty |
| assumptions | list[str] | yes | at least 1 |
| confidence | float | yes | 0.0-1.0 |

**Guarantees**:
- Attempts to quantify ROI or business impact
- Floor captures 5-10% of estimated value
- Target captures 15-20%
- Stretch captures 25-30%
- States confidence honestly (lower when ROI is hard to estimate)

---

## Risk Agent

**Input**: DealInput (full deal context)
**Output**: RiskAssessment

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| risk_factors | list[str] | yes | at least 1 |
| risk_adjustment_pct | float | yes | 0-50 |
| reasoning | str | yes | non-empty |
| confidence | float | yes | 0.0-1.0 |

**Guarantees**:
- 0-10% for low risk, 10-25% moderate, 25-50% high
- Each risk factor is specific (not generic)
- Reasoning connects factors to adjustment percentage

---

## Packaging Agent

**Input**: DealInput (full deal context)
**Output**: PackagingRecommendation

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| recommended_structure | str | yes | non-empty |
| components | list[str] | yes | at least 1 |
| reasoning | str | yes | non-empty |
| alternatives | list[str] | yes | at least 1 |
| confidence | float | yes | 0.0-1.0 |

**Guarantees**:
- Recommends a specific structure (not generic "it depends")
- Components describe what each part covers
- At least 1 alternative with reasoning for rejection
- Structure matches service type (not retainer for a one-off project)

---

## Arbiter Agent

**Input**: DealInput + 3 AgentProposals + RiskAssessment + PackagingRecommendation
**Output**: PricingResult (partial -- without validation)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| price_floor | float | yes | >= Cost Agent floor (unless strategic) |
| price_target | float | yes | >= price_floor |
| price_stretch | float | yes | >= price_target |
| confidence | float | yes | 0.0-1.0 |
| suggested_structure | str | yes | non-empty |
| risk_factors | list[str] | yes | at least 1 |
| assumptions | list[str] | yes | at least 1 |
| rationale | str | yes | non-empty, explains synthesis |

**Guarantees**:
- Never below Cost Agent floor without explicit strategic flag
- Risk adjustment is applied and visible
- Uses Packaging Agent recommendation for structure
- Rationale explains how specialist inputs were weighted

---

## Validator Agent

**Input**: DealInput + PricingResult
**Output**: ValidationResult

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| is_valid | bool | yes | |
| issues | list[str] | no | |
| suggestions | list[str] | no | |
| summary | str | yes | non-empty |

**Guarantees**:
- Checks: floor > breakeven, rationale matches numbers, assumptions stated, risk visible, structure fits service, confidence appropriate
- is_valid=false if any critical issue found
- Summary is one paragraph
