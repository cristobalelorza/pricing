# Pricing Recommendation: Custom Online Ordering System for Local Bakery Chain

## Short Answer

You should price this project in the range of **$45,000 to $75,000**, depending on scope complexity. Their $25K budget is significantly below market rate for what they are describing. Here is how to think through it and how to handle the conversation.

---

## Understanding What They Are Actually Asking For

A "custom online ordering system with delivery tracking" for a 5-location bakery chain is not a simple project. Break down what this really involves:

**Core online ordering system:**
- Menu management (likely different menus or availability per location)
- Shopping cart and checkout flow
- Payment processing integration (Stripe, Square, etc.)
- Order confirmation and notifications (email/SMS)
- Customer accounts and order history
- Location selection and routing orders to the correct store

**Delivery tracking:**
- Real-time or near-real-time delivery status updates
- Driver assignment or integration with a delivery service
- Estimated delivery time calculations
- Customer-facing tracking page
- Potentially a driver-facing app or interface

**Multi-location complexity:**
- 5 locations means location-based inventory/availability
- Potentially different delivery zones per location
- Consolidated reporting across locations
- Possibly different hours, menus, or pricing per location

**Admin/back-office:**
- Dashboard for store managers to view and manage orders
- Menu and pricing management interface
- Basic reporting (sales, popular items, delivery times)
- Order status management workflow

**Infrastructure:**
- Hosting and deployment
- SSL, security, PCI compliance considerations for payments
- Mobile-responsive design (or native app)
- Performance under load during peak ordering times

This is a substantial full-stack application, not a basic website.

---

## Cost-Based Analysis (Your Floor Price)

Estimate the hours honestly:

| Component | Estimated Hours |
|---|---|
| Discovery, requirements, and design | 30-50 |
| Database design and backend API | 60-80 |
| Customer-facing ordering frontend | 80-120 |
| Payment integration | 20-30 |
| Delivery tracking system | 40-70 |
| Admin dashboard | 50-70 |
| Multi-location logic | 20-40 |
| Notifications (email/SMS) | 15-25 |
| Testing and QA | 40-60 |
| Deployment and launch support | 15-25 |
| **Total** | **370-570 hours** |

At a freelance rate of $100-150/hour (reasonable for a competent full-stack developer doing custom application work), the cost-based floor is:

- Low end: 370 hours x $100 = **$37,000**
- Mid range: 470 hours x $125 = **$58,750**
- High end: 570 hours x $150 = **$85,500**

At $25,000, you would be working for roughly $45-65/hour, which is below market for this level of work and responsibility.

---

## Market-Based Analysis

For context on what comparable work costs:

- **Off-the-shelf solutions** (Square Online, Toast, ChowNow) run $100-500/month per location but come with significant limitations and ongoing fees. Over 3 years, a 5-location chain would spend $18,000-$90,000 on platform fees alone, plus they would not own the system.
- **Custom ordering systems** from agencies typically cost $50,000-$150,000+ depending on complexity.
- **Freelance-built custom systems** of this scope commonly land in the $40,000-$80,000 range.
- The delivery tracking component alone, if done well, can add $15,000-$30,000 to a project.

Their $25K budget is closer to what you would expect for a basic brochure website with a simple order form, not a multi-location ordering platform with delivery tracking.

---

## Value-Based Analysis

This is where your case for higher pricing gets strongest. Consider what this system is worth to them:

- **$3M annual revenue across 5 locations.** If online ordering captures even 10-15% of revenue, that is $300,000-$450,000 per year flowing through this system.
- **Reduced reliance on third-party platforms.** If they currently use DoorDash, UberEats, or Grubhub, those platforms take 15-30% commission. Bringing orders in-house on their own system could save them $45,000-$135,000 per year in commission fees alone.
- **Customer data ownership.** Having direct customer relationships and order data enables marketing, loyalty programs, and repeat business that third-party platforms do not provide.
- **Operational efficiency.** A well-built system reduces phone orders, order errors, and manual coordination across locations.

A system that saves or generates $100K+ per year is easily worth $50,000-$75,000 as a one-time build cost. The ROI payback period would be under one year.

---

## Risk and Complexity Adjustments

Several factors push the price up from a baseline estimate:

- **Multi-location complexity** adds real architectural and UX challenges. This is not 1 store x 5.
- **Delivery tracking** is a feature category with many hidden edge cases (failed deliveries, driver no-shows, wrong addresses, real-time updates).
- **Payment processing** carries compliance and liability considerations.
- **You are a solo freelancer.** If you get sick, go on vacation, or hit a technical wall, there is no team to absorb the impact. Your price needs to account for this risk.
- **Ongoing maintenance** will be needed. Bugs, payment API changes, menu updates, new feature requests. If you do not price this in, you will end up doing free work for months after launch.
- **Scope creep is almost certain** with a project of this size. "Can we also add loyalty points?" "Can customers schedule orders for later?" "We need catering orders too." Budget for this or define scope very tightly.

---

## Recommended Pricing Approach

### Option A: Fixed Project Price (Recommended)

Present a tiered proposal:

**Tier 1 - Core System ($45,000-$55,000):**
- Online ordering for all 5 locations
- Payment processing
- Basic order status updates (not real-time tracking)
- Admin dashboard for order management
- Customer notifications
- Mobile-responsive web app

**Tier 2 - Full System with Delivery Tracking ($60,000-$75,000):**
- Everything in Tier 1
- Real-time delivery tracking
- Driver management interface
- Delivery zone configuration per location
- Advanced reporting dashboard
- SMS notifications for delivery updates

**Tier 3 - Premium ($80,000+):**
- Everything in Tier 2
- Native mobile app (iOS and Android)
- Customer loyalty/rewards program
- Advanced analytics
- API integrations with their POS system

Tiering lets them choose based on budget while anchoring the conversation at realistic numbers. If they truly cannot go above $25K, Tier 1 shows them what that budget can (and cannot) buy -- and the answer is a significantly reduced scope.

### Option B: Phased Approach

If they are committed to the $25K budget right now but have more to spend over time:

- **Phase 1 ($25,000):** Core ordering system for 1-2 locations, basic order management, payment processing. No delivery tracking. This gets them live and generating revenue.
- **Phase 2 ($20,000-$30,000):** Roll out to all 5 locations, add delivery tracking, build admin dashboard.
- **Phase 3 ($15,000-$20,000):** Advanced features, reporting, optimizations based on real usage data.

This gives them a path that fits their current budget while establishing the true cost of the full vision.

### Include Ongoing Maintenance

Regardless of approach, quote a monthly maintenance and support retainer:

- **$1,500-$3,000/month** for hosting, monitoring, bug fixes, minor updates, and priority support.
- This protects you from unpaid post-launch work and gives them reliability.
- Over a year, this adds $18,000-$36,000 in recurring revenue for you.

---

## How to Handle the Conversation

**Do not just counter with a higher number.** Instead:

1. **Ask detailed questions first.** "Let me make sure I understand the full scope before we talk numbers." Walk through every feature they expect. Most clients underestimate what they are asking for because they have not thought through the details.

2. **Show them the scope breakdown.** When you present your proposal, include the component list. Let them see that this is not one thing -- it is dozens of interconnected features.

3. **Reference their business numbers.** "With $3M in revenue and 5 locations, online ordering could drive $300K+ in annual sales through this system. I want to build something that handles that volume reliably."

4. **Compare to alternatives.** "A platform like Toast or ChowNow would cost you $X per month across 5 locations, and you would not own the system or the data. A custom build costs more upfront but pays for itself within a year."

5. **Be honest about the $25K figure.** "I appreciate you sharing your budget. I want to be transparent: $25K would cover a basic version of what you described, but not the full system with delivery tracking across 5 locations. Let me show you what different investment levels would get you."

6. **Offer the phased approach as a bridge.** If they cannot move on budget, phasing lets you start the relationship without underpricing yourself.

---

## What to Watch Out For

- **Do not agree to $25K for the full scope.** You will lose money, resent the project, and deliver something you are not proud of.
- **Get a detailed scope document signed** before starting work. Ambiguity in a $50K+ project leads to disputes.
- **Require a deposit.** 30-50% upfront is standard for freelance projects of this size.
- **Define what is out of scope** explicitly. Native apps, POS integration, third-party delivery service integration, etc. -- if it is not listed, it is not included.
- **Set a change request process.** New features or scope changes beyond the agreement get quoted separately.
- **Do not underprice to win the deal.** A bakery chain doing $3M in revenue can afford to pay fairly for custom software. If they truly cannot go above $25K, they should be using an off-the-shelf platform, not commissioning custom development.

---

## Summary

| | Price |
|---|---|
| Their stated budget | $25,000 |
| Your cost-based floor | $37,000-$55,000 |
| Market rate for comparable work | $50,000-$80,000 |
| Value-justified price | $50,000-$75,000 |
| **Recommended target price** | **$55,000-$65,000** |
| Stretch price (full premium scope) | $75,000-$85,000 |

The $25K budget is roughly half of what this project should cost at minimum. You are right to think you can charge more -- you should charge more, because delivering this well at $25K would mean working below a sustainable rate on a project with real complexity and real business impact.

Present a professional proposal with tiered options, lead with scope and value, and let them choose the investment level that matches what they actually need.
