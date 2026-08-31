# China Tech X Operating KPI — Money-First v2.0

## 1. North Star

**Primary goal: generate repeatable cash revenue attributable to X operations.**

Followers, impressions, engagement, reply reach, profile visits, alert latency, and posting volume are leading indicators only. They never substitute for revenue validation.

The project has two monetization paths:

1. **Direct X-attributable business revenue — P0**: China Tech research/intelligence work, consulting, paid briefs, sponsorship/partnership, paid community/subscription or another customer payment whose source can be traced to X.
2. **X-native creator payout — P1/later**: Original Content Rewards and other X creator monetization products when eligibility is reached.

Direct business revenue is prioritized because a small high-value China Tech audience can produce revenue before the account reaches X-native payout scale.

## 2. Revenue Attribution

Revenue counts as `X-attributable` only when there is evidence that X initiated or materially caused the commercial relationship, for example:

- X DM/reply/profile interaction leads to a paid customer;
- buyer discovers the account/content on X and requests research, consulting, sponsorship, or another paid service;
- an X post/pinned CTA drives a buyer to the payment/contact path;
- X itself pays the creator through an official monetization program.

Existing customers or unrelated sales do not count merely because they follow the account.

Every commercial event is recorded as one of:

`OFFER_LIVE -> COMMERCIAL_INTENT -> QUALIFIED_CONVERSATION -> PROPOSAL_SENT -> PAID_CUSTOMER -> REPEAT_PURCHASE`

Separate event types exist for `SPONSOR_PAYMENT`, `X_NATIVE_PAYOUT`, and `LOST_DEAL`.

## 3. Initial Monetization Hypothesis

The first low-cost monetization hypothesis is **China Tech research / market-intelligence expertise** for an English-speaking audience.

The initial CTA should be low friction, e.g. a profile/pinned-post route for custom China Tech research, market intelligence, or an expert briefing. Do not build a paid product before a buyer conversation exists.

The exact offer, price, and buyer segment are experiment variables. Change at most one monetization variable between daily reviews.

## 4. Baseline

Day-0 directional baseline:

- followers: `4`;
- tracked posts: `15`;
- provisional tracked views: `396`;
- arithmetic average: `26.4 views/post`.

The old metrics are retained only to measure distribution lift. Money KPI is the authority.

## 5. Day 3 KPI — Monetization Path Exists

### Required operating evidence

- runtime success `>=95%`;
- delivered-alert latency after channel verification `<=15 min` median;
- at least `4` qualified alerts/opportunities;
- at least `2` published actions;
- at least `1` differentiated original post.

### Required money-funnel evidence

- at least `1` monetization offer/CTA is live and recorded as `OFFER_LIVE`.

### Decision

Day 3 passes only if there is both an operating content loop and a visible path for a buyer to start a commercial conversation.

No buyer interest is required in 72 hours, but **no offer path = failure** regardless of views.

## 6. Day 7 KPI — First Commercial Intent

Required:

- runtime success `>=97%`;
- median verified alert latency `<=10 min`;
- review-worth precision `>=60%`;
- at least `8` qualified alerts;
- at least `5` published actions;
- at least `2` original posts;
- at least `1` real commercial-intent signal;
- at least `1` qualified buyer conversation.

A like, follow, repost, or generic compliment is **not** commercial intent.

Examples that count: request for custom research, pricing question, consulting call request, sponsor inquiry, request for deeper paid analysis, or explicit willingness to discuss a paid solution.

## 7. Day 10 KPI — Qualified Pipeline

Required:

- at least `7` published actions;
- at least `3` original posts;
- at least `2` qualified buyer conversations;
- at least `1` concrete paid proposal / paid pilot offered.

If reach is growing but there is no qualified pipeline, the problem is buyer/offer fit or CTA—not infrastructure.

## 8. Day 15 KPI — First Cash

Required minimum:

- at least `10` published actions;
- at least `5` original posts;
- at least `3` qualified buyer conversations;
- at least `1` proposal;
- at least `1` paying customer;
- cumulative X-attributable cash revenue `>= ¥500`.

**Day 15 is the first hard money gate.**

If the account has good distribution but zero paid conversion, monetization has not been validated. Diagnose buyer segment, offer, proof/value, price, and CTA before scaling reach.

## 9. Day 30 KPI — Revenue Validation

### Target gate

- runtime success `>=98%`;
- review-worth precision `>=75%`;
- median operating time `<=30 min/day`;
- at least `20` published qualified actions;
- at least `8` original posts;
- at least `5` qualified buyer conversations;
- at least `3` proposals;
- at least `2` paying customers;
- cumulative X-attributable revenue `>= ¥2,000`.

### Stretch

- cumulative revenue `>= ¥5,000`;
- at least `3` paying customers;
- at least `1` repeat purchase.

### Minimum monetization validation

If Day 30 has at least one genuine payer and `>= ¥500`, the monetization hypothesis has weak-but-real proof even if the target gate is missed. It requires correction/iteration, not automatic abandonment.

### Failure interpretation

- strong impressions/follower growth + `¥0`: **distribution validated, monetization failed**;
- commercial conversations + no payment: **offer/conversion failure**;
- no commercial conversations: **buyer/CTA/audience failure**;
- no meaningful distribution: **content/target/distribution failure**.

Infrastructure is never the default explanation.

## 10. Beyond Day 30

These are project business targets, not external industry averages. Recalibrate after the first real paid conversions reveal actual deal size and conversion rate.

- **Day 60**: target X-attributable monthly revenue `>= ¥3,000`.
- **Day 90**: target monthly revenue `>= ¥5,000` with more than one paying customer or a repeat/recurring customer.
- **3–6 months commercial-success definition**: X-attributable revenue `>= ¥10,000/month` for **2 consecutive months**, while keeping the operating system economically sensible.

A smaller revenue level can still justify continuing if the trend and unit economics are improving; the canonical target is deliberately meaningful enough to distinguish a hobby metric from a business asset.

## 11. X-Native Monetization Track

Verified against X Help on 2026-08-31, Original Content Rewards currently requires, among other conditions:

- active eligible Premium subscription;
- at least `500 verified followers`;
- at least `500,000 Home Timeline impressions from verified users in the last 90 days`;
- reply impressions are excluded from that threshold;
- active original content;
- payout method / identity requirements after eligibility;
- minimum payout currently `$30`.

Therefore:

- replies are primarily **audience acquisition**;
- original posts are required to build **owned distribution and X-native monetizable impressions**;
- X-native payouts are tracked separately as `X_NATIVE_PAYOUT` and are not expected to be the fastest first-revenue path.

X Subscriptions has an even higher current application threshold in X's English help documentation (including 2,000 verified followers and 5M organic impressions over 3 months), so it is not a near-term Day-30 revenue assumption.

## 12. Daily Review Funnel

Every review walks the money funnel in this order:

```text
Signal -> Distribution -> Original Authority -> Offer Visible
       -> Commercial Intent -> Qualified Conversation
       -> Proposal -> Paid Customer -> Repeat Purchase -> Revenue
```

Identify the **first broken stage**.

Only after identifying that stage may the system recommend a correction. Change at most:

- one business/monetization variable;
- one instrumentation fix.

Do not simultaneously change sources, target accounts, voice, offer, price, CTA, and architecture.

## 13. Notification Evidence

A provider HTTP 200 / `code=0` means `API_ACCEPTED`, not human delivery.

A delivery channel counts for KPI only after the intended human explicitly confirms seeing a smoke message. Feishu `open_id` is application-scoped and may never be mixed with credentials from another application.

Misrouted messages are excluded from delivery counts and latency KPI.
