# Pricing Research Methods

## Table of Contents
- Van Westendorp Price Sensitivity Meter
- MaxDiff Analysis (Best-Worst Scaling)
- Willingness-to-Pay Surveys
- Usage-Value Correlation Analysis
- Price Increase Signals and Strategy

---

## Van Westendorp Price Sensitivity Meter

The Van Westendorp survey identifies the acceptable price range for your offering by asking four questions.

### The Four Questions

Ask each respondent:

1. "At what price would you consider [offering] to be so expensive that you would not consider buying it?" (Too expensive)
2. "At what price would you consider [offering] to be priced so low that you would question its quality?" (Too cheap)
3. "At what price would you consider [offering] to be starting to get expensive, but you still might consider it?" (Expensive / high side)
4. "At what price would you consider [offering] to be a bargain -- a great buy for the money?" (Cheap / good value)

### How to Analyze

1. Plot cumulative distributions for each question
2. Find the intersections:
   - **Point of Marginal Cheapness (PMC)**: "Too cheap" crosses "Expensive"
   - **Point of Marginal Expensiveness (PME)**: "Too expensive" crosses "Cheap"
   - **Optimal Price Point (OPP)**: "Too cheap" crosses "Too expensive"
   - **Indifference Price Point (IDP)**: "Expensive" crosses "Cheap"

The acceptable price range runs from PMC to PME. The optimal pricing zone sits between OPP and IDP.

### Sample Output

```
Price Sensitivity Analysis Results:

Point of Marginal Cheapness:     $29/mo
Optimal Price Point:             $49/mo
Indifference Price Point:        $59/mo
Point of Marginal Expensiveness: $79/mo

Recommended range: $49-59/mo
Current price: $39/mo (below optimal)
Opportunity: 25-50% price increase without significant demand impact
```

### Survey Tips
- Need 100-300 respondents for reliable data
- Segment by persona -- different buyer types have different WTP
- Use realistic product/service descriptions, not abstract framing
- Consider adding purchase intent questions for richer data
- For B2B services: frame around project value or monthly retainer, not hourly rates

### Adapting Van Westendorp for Services

For professional services, reframe the questions around the engagement:
- "At what total project cost would you not consider hiring a firm for this?"
- "At what cost would you question whether the firm could deliver quality work?"
- "At what cost would it feel expensive but you'd still consider it?"
- "At what cost would it feel like a great deal?"

---

## MaxDiff Analysis (Best-Worst Scaling)

MaxDiff identifies which features, deliverables, or service components buyers value most. This directly informs packaging and tiering decisions.

### How It Works

1. List 8-15 features or deliverables you could include
2. Show respondents sets of 4-5 items at a time
3. Ask: "Which is MOST important to you? Which is LEAST important?"
4. Repeat across multiple sets until all items have been compared
5. Statistical analysis produces importance scores

### Example Survey Question

```
Which deliverable is MOST important to you?
Which deliverable is LEAST important to you?

[ ] Monthly strategy report
[ ] Dedicated account manager
[ ] 24/7 support access
[ ] Custom integrations
[ ] Quarterly business reviews
```

### Using MaxDiff for Packaging

| Utility Score | Packaging Decision |
|---------------|-------------------|
| Top 20% | Include in all tiers (table stakes) |
| 20-50% | Use to differentiate tiers |
| 50-80% | Higher tiers only |
| Bottom 20% | Consider cutting or selling as add-on |

### For Services

Run MaxDiff on deliverables within a service offering:
- Which parts of the engagement do clients value most?
- Which extras (training, documentation, support) justify premium pricing?
- Which deliverables should be standard vs. add-on?

---

## Willingness-to-Pay Surveys

### Direct Method (simple but biased)
"How much would you pay for [offering]?"

Simple to run but respondents tend to understate WTP. Use as a rough floor estimate.

### Gabor-Granger Method (better)
"Would you buy [offering] at [$X]?" (Yes/No)

Vary the price across respondents to build a demand curve. Shows you how volume changes at different price points.

### Conjoint Analysis (most rigorous)
Show product/service bundles at different prices. Respondents choose their preferred option from sets. Statistical analysis reveals price sensitivity per feature or deliverable.

This is the gold standard but requires more setup and larger sample sizes.

### Quick WTP for Services

If you cannot run formal surveys, these questions in sales conversations give useful signals:

- "What would this engagement need to cost for it to be an easy yes?"
- "What budget have you set aside for solving this problem?"
- "What are you spending on this problem today?" (current cost of status quo)
- "If this project saves you $X per year, what would you invest to get that result?"

Watch for these signals:
- **No hesitation when you quote a price** = you are likely underpriced (Naomi Ionita)
- **"That's cheap!"** = definitely underpriced
- **Immediate yes without negotiation** = significant room to charge more
- **Pushback but they still close** = you are in the right zone

---

## Usage-Value Correlation Analysis

For SaaS and recurring services, connecting usage patterns to customer success reveals the right value metric and pricing thresholds.

### Step 1: Instrument usage data
Track how clients use your product or service:
- Feature usage frequency
- Volume metrics (users, records, API calls, hours consumed)
- Outcome metrics (revenue generated, time saved, issues resolved)

### Step 2: Correlate with customer success
- Which usage patterns predict retention and expansion?
- Which clients pay the most, and why?
- At what usage level do clients "get it"?

### Step 3: Identify value thresholds
- At what usage level should the client upgrade?
- What usage pattern justifies a price increase?
- Where does the free or entry tier stop delivering enough value?

### Example Analysis

```
Usage-Value Correlation:

Segment: High-LTV clients (>$50K annual)
Average monthly hours consumed: 80
Average integrations active: 6
Average team members using service: 12

Segment: Churned clients
Average monthly hours consumed: 15
Average integrations active: 1
Average team members using service: 2

Insight: Value correlates with depth of engagement (team adoption + integrations)
Recommendation: Price per team member, gate advanced integrations to higher tiers
```

---

## Price Increase Signals and Strategy

### When to Raise Prices

**Market signals:**
- Competitors have raised their prices
- New prospects do not flinch at your current price
- You hear "it's so cheap!" from clients or prospects

**Business signals:**
- Very high conversion rate (>40% on proposals)
- Very low churn (<3% monthly)
- Strong unit economics with room to capture more value

**Product/service signals:**
- You have added significant value since the last pricing update
- Your track record and reputation have strengthened
- You have moved into a more specialized or premium positioning

### Implementation Strategies

**1. Grandfather existing clients**: New price applies only to new clients. Simplest, lowest risk, fastest to execute.

**2. Delayed increase**: Announce the increase 3-6 months out. Gives existing clients time to budget. Signals confidence.

**3. Tied to value**: Raise the price but add new deliverables, features, or support levels. Frame as "more value at a new price point."

**4. Plan restructure**: Redesign the entire tier or package structure. Works when the current structure no longer fits your market or offering.

### Price Increase Rules of Thumb

- Revisit pricing at least every 6-12 months (Naomi Ionita)
- Losing 20-30% of deals on price is a healthy signal you are near the market ceiling (Naomi Ionita)
- Most pricing changes are reversible -- grandfather existing clients and move faster than you think (Eeke de Milliano)
- Never raise price without being able to articulate what additional value justifies it
- For B2B services: annual rate increases of 3-8% are standard and expected; larger increases need a value story
