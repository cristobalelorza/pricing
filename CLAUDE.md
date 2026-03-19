# CLAUDE.md

## Project Mission
Build and maintain a reliable agent-based system that prices B2B services quickly, fairly, and defensibly.

The goal is not just to output a number.
The goal is to produce pricing recommendations that can withstand manual review, client pushback, and internal business scrutiny.

Primary outcomes:
- gather the minimum context needed to price a service well
- estimate a viable floor price based on cost, time, and delivery constraints
- benchmark market reality without blindly copying competitors
- estimate client value / ROI where possible
- adjust for delivery risk, complexity, urgency, and uncertainty
- recommend a final price structure and price range
- explain assumptions, trade-offs, and confidence clearly
- preserve reasoning artifacts so pricing can be reviewed and improved over time

## Project Scope
Current focus:
- B2B service pricing
- fast but defensible pricing recommendations
- fair pricing based on cost, market, value, and risk
- agent-swarm collaboration for pricing
- documentation-first workflow for non-trivial work
- reusable pricing logic across different service types

Out of scope until explicitly added:
- fully automated contract generation
- invoice creation or payment collection
- outbound sales automation
- production deployment before the pricing methodology is validated
- pretending to know missing inputs instead of surfacing uncertainty
- one-size-fits-all pricing formulas that ignore context

## Pricing Standard
A good pricing recommendation should be:
- profitable enough to deliver well
- competitive enough to be realistic
- aligned with the value created for the client
- adjusted for risk, urgency, and scope ambiguity
- explained clearly enough that a human can defend it

Fair pricing does not mean cheapest.
Fair pricing means justified, transparent, and viable for both sides.

## Default Swarm Strategy
Default collaboration model: **Parallel + Arbiter + Validator**

Why:
- specialists work independently first, which reduces anchoring
- parallel work is faster than long debate chains
- a final arbiter can synthesize trade-offs cleanly
- a validator can catch pricing that is too low, too high, or poorly justified

Default specialist roles:
- **Cost Agent**: estimates floor price from effort, costs, margin, and operational constraints
- **Market Agent**: checks comparable offers, category norms, and willingness-to-pay signals
- **Value Agent**: estimates business value / ROI / upside for the client
- **Risk Agent**: adjusts for uncertainty, delivery risk, scope ambiguity, urgency, and support burden
- **Packaging Agent** (optional): recommends structure such as setup fee, monthly retainer, tiering, or hybrid pricing

Decision roles:
- **Arbiter Agent**: compares specialist outputs and synthesizes a final recommendation
- **Validator Agent**: sanity-checks the final output before it is considered done

Default output format:
- floor price
- target price
- stretch price
- suggested pricing structure
- major assumptions
- risk factors
- confidence level
- short rationale

## When To Use Other Collaboration Modes
Use **Debate & Converge** only when:
- the offer is novel
- pricing is highly strategic or positioning-heavy
- trade-offs are unusually subjective
- the team needs to explore multiple commercial narratives, not just output a price

Use **Pipeline** only when:
- the pricing process is already stable and deterministic
- work is naturally sequential
- you want research -> analysis -> recommendation -> formatting

Do not default to debate for routine pricing work.
Do not default to pipeline when independent specialist judgment matters.

## Context Management
- Keep this file concise and durable.
- Prefer pointer-based references to project docs rather than repeating long instructions.
- At session start, review this file plus:
  - CLAUDE.md
  - handoff.md
  - tasks/todo.md
  - tasks/lessons.md
  - state.md
  - PLAN.md if it exists
- If context grows noisy or direction changes, stop and summarize into project docs before continuing.

- When the conversation gets long/heavy (many messages, big tool outputs, or quality dips):
  1. Stop and update/create handoff.md with:
     - current objective + exact next step
     - key recent decisions + short why
     - active constraints / gotchas
     - pricing methodology status
     - remaining high-priority items from todo.md
  2. Then either:
     - Preferred: /clear (or new chat) -> first message:
       "Read CLAUDE.md + handoff.md + todo.md + lessons.md. Current state: [one-sentence summary]. Continue."
     - Or: /compact focus on: pricing methodology, key decisions, constraints, next objective
  3. After /compact:
     next message must be:
     "Re-read CLAUDE.md + handoff.md (if exists) + todo.md + lessons.md now. Give one-paragraph state summary, then continue exactly where we left off."

- If reasoning gets shallow or key rules are forgotten, force a reset immediately.

## Session Continuity & Compaction Recovery
- Claude may lose important project rules after /compact or /clear.
- Prefer clean resets over overloaded sessions when quality feels off.
- At natural breakpoints (pricing methodology decision, swarm design complete, schema change, major refactor, or context >70–75%):
  1. Update state/handoff.md (or state/session-summary.md) with:
     - current objective & exact next step
     - key recent decisions + WHY
     - active constraints / gotchas
     - remaining high-priority TODOs
     - current swarm / methodology status
  2. Then either:
     - /clear and start fresh -> first message:
       "Read CLAUDE.md + handoff.md + todo.md + lessons.md. Current state: [1-sentence recap]. Continue."
     - Or /compact focus on: pricing methodology, key decisions, constraints, next objective
  3. Immediately after compaction:
     "Re-read CLAUDE.md + handoff.md now. Give 1-paragraph current state summary before proceeding."

- Keep handoff.md concise. It is for transfer, not long-term history.
- Move session-specific clutter into lessons.md or handoff.md, not this file.

## Planning Mode Default
Enter planning mode for any non-trivial task, especially anything involving:
- pricing methodology changes
- agent role design
- arbiter or validator logic
- schema changes
- packaging strategy
- benchmark strategy
- ROI estimation logic
- risk adjustment logic
- multi-service generalization

If assumptions fail or the approach becomes messy, stop and re-plan.
Use planning for milestone definition and verification, not only implementation.
Write specs before building when ambiguity exists.
After planning a major phase, suggest updating handoff.md before implementation.

## Task Management
- Track multi-step work in tasks/todo.md.
- Use checkable items.
- Mark progress as work advances.
- Add a short review/result section when a task is completed.
- For meaningful repeated mistakes or corrections, update tasks/lessons.md.
- When completing a multi-session milestone, ensure handoff.md reflects the new state before ending work.

## Subagent Strategy
Use subagents only when separation or parallelism clearly helps.

Good uses:
- cost model analysis
- market benchmark research
- value / ROI estimation
- risk / complexity analysis
- offer packaging design
- validator review
- fixture/test generation
- documentation drafting for a completed design

Assign one focused task per subagent.
Do not use subagents unnecessarily for simple sequential work.

Default swarm rule:
- specialists should work independently first
- arbiter synthesizes second
- validator checks third

## Self-Improvement Loop
- When the user corrects an important mistake or a recurring pattern appears, capture it in tasks/lessons.md.
- Convert lessons into working rules that reduce repeat mistakes.
- Review relevant lessons at the start of future sessions.
- If Claude repeats a mistake after compaction / new session, capture it as a post-compaction recovery lesson.

## Verification Before Done
Never mark work complete without proving it works.

Minimum verification for pricing logic:
- check that the final price is not below the viable floor unless explicitly marked strategic
- check that the rationale matches the recommended number
- check that assumptions are stated, not hidden
- check that risk adjustments are visible and not silently baked in
- check that output format is consistent and reviewable
- run the smallest relevant tests and sanity checks
- explain what changed and how it was verified

Ask:
Would a strong staff-level engineer and a commercially literate operator both approve this output?

## Demand Elegance
- For non-trivial changes, pause and ask whether there is a simpler or cleaner solution.
- If a solution feels hacky, step back and prefer the elegant solution.
- For small obvious fixes, do not over-engineer.
- Minimize impact and preserve clarity.

## Autonomous Problem Solving
- When given a bug report or bad pricing result, investigate directly.
- Use logs, fixtures, tests, prompts, schemas, and decision traces.
- Minimize unnecessary back-and-forth.
- Find the root cause, not just the surface symptom.
- Fix broken reasoning or validation before adding more scope.

## Core Engineering Principles
- Simplicity first.
- Minimal-impact changes.
- Root-cause fixes over temporary patches.
- Preserve clarity over cleverness.
- Avoid speculative architecture.
- No unnecessary files or noisy scaffolding.
- Keep code and docs lean, concrete, and reviewable.

## Domain Rules for This Project
- Price recommendations must consider **cost, market, value, and risk**. Do not rely on only one lens.
- Never output a number without a rationale.
- Never hide uncertainty. Surface missing inputs, weak assumptions, and confidence explicitly.
- Never assume scope is fixed when the brief is ambiguous.
- Never recommend pricing below a viable delivery floor unless explicitly labeled as strategic.
- Separate:
  - raw client/service inputs
  - assumptions
  - specialist analyses
  - arbiter decision
  - validator checks
- Preserve reasoning artifacts for auditability and iteration.
- Prefer price ranges over fake precision.
- Prefer min / target / stretch over a single unexplained number.
- Packaging matters: recommend structure, not just amount, when it improves fairness or close-rate.
- Benchmarking should inform pricing, not dominate it.
- Value-based reasoning is stronger than competitor-copying when credible ROI exists.
- Keep the system general enough to reuse across service categories.
- Do not mix major methodology, agent-role, and output-schema changes in one step unless explicitly required.

## Definition of Done
A task is not done unless:
- the relevant docs are updated if behavior or scope changed
- the change was validated appropriately
- assumptions and limitations are stated
- tasks/todo.md reflects the completed work
- any important lesson has been captured in tasks/lessons.md

For pricing recommendations specifically, done means:
- the number or range is defensible
- the reasoning is understandable
- the structure is commercially usable
- the uncertainty is visible

## Key Project Docs
Use and maintain these files as the project grows:
- PLAN.md
- spec.md
- pricing-methodology.md
- data-model.md
- architecture.md
- state.md
- tasks/todo.md
- tasks/lessons.md
- validation.md
- handoff.md
- state/session-summary.md

Optional docs if needed:
- benchmark-notes.md
- packaging-rules.md
- prompt-contracts.md
- evaluator-rubric.md

## Project-Specific Rules
- Default to Parallel + Arbiter + Validator for pricing swarms.
- Prefer independent specialist judgment before synthesis.
- Do not let agents anchor on each other too early.
- Do not optimize for speed at the cost of nonsense pricing.
- Do not hide uncertainty in outputs.
- Do not build production automation before the methodology is validated.
- No emojis.