# Precio - Validation Checklist

## Per-Run Validation (Validator Agent)
- [x] Floor price is above breakeven
- [x] Rationale matches the recommended numbers
- [x] Assumptions are stated, not hidden
- [x] Risk adjustments are visible, not silently baked in
- [x] Pricing structure fits the service type
- [x] Confidence level reflects available information
- [x] Output format is consistent and reviewable

## Methodology Validation (Manual)
- [x] Run 3+ diverse test cases across service types
- [ ] Run 5+ diverse test cases (need 2 more)
- [ ] Compare agent output vs. human pricing judgment
- [x] Check that Cost Agent never recommends below delivery cost
- [x] Check that Market Agent uses reasonable benchmarks
- [ ] Check that Value Agent's ROI estimates are credible (needs more cases)
- [x] Check that Risk Agent adjustment percentages are proportional
- [x] Check that Arbiter weighs specialists appropriately
- [x] Check that Validator catches obvious errors

## Tests Run
| URL | Service | Floor | Target | Stretch | Validation | Date |
|-----|---------|-------|--------|---------|------------|------|
| google.com | Website redesign + SEO (3mo) | $47,500 | $81,250 | $102,500 | Passed | 2026-03-17 |
| shopify.com | Custom API integration | $75,000 | $147,000 | $206,000 | Passed | 2026-03-17 |
| stripe.com | Security audit (6wk, $50K hint) | $47,500 | $62,500 | $81,250 | Passed | 2026-03-17 |

## Test Cases Still Needed
- [ ] Training: "2-day AI workshop for a corporate team of 20"
- [ ] Design: "Brand identity redesign for a Series A startup"
- [ ] Small business: pricing for a local company (not enterprise)

## Known Gaps
- No Packaging Agent yet (deferred)
- No persistence of results
- No A/B comparison of prompts
- No automated regression tests for pricing quality
- Free model truncates long arbiter responses (mitigated by 4096 max_tokens + truncation repair)
