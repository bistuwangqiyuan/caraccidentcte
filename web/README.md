# AfterCrash SG (Web)

Singapore post-accident **evidence & FNOL checklist** — Next.js app deployed on Vercel.

**Production:** https://aftercrash-sg.vercel.app

## What it does

- Guided checklist (scene → evidence → timeline → FNOL → export)
- Free partial preview; one-time **S$39** Stripe unlock for full PDF
- Client-side PDF (`jspdf`); no photo uploads in v1
- Hard compliance boundaries: not legal advice, not fault determination, not CTE diagnosis

## Local development

```bash
cd web
cp .env.example .env.local
# Fill STRIPE_* (test keys), UNLOCK_SECRET, NEXT_PUBLIC_SITE_URL=http://localhost:3000
npm install
npm run dev
```

Open http://localhost:3000

## Environment variables

| Variable | Required | Notes |
|----------|----------|--------|
| `STRIPE_SECRET_KEY` | For paid unlock | `sk_test_…` then swap to live |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Optional UI | Checkout redirects via server Session |
| `STRIPE_PRICE_ID` | Optional | Else Checkout uses SGD 3900 inline |
| `UNLOCK_SECRET` | Yes for verify | Long random HMAC secret |
| `NEXT_PUBLIC_SITE_URL` | Yes in prod | e.g. `https://aftercrash-sg.vercel.app` |

Without Stripe keys the site still serves the free wizard; Checkout returns `NOT_CONFIGURED`.

## Deploy

```bash
cd web
npx vercel link
npx vercel env add UNLOCK_SECRET production
npx vercel env add NEXT_PUBLIC_SITE_URL production
# optional Stripe:
npx vercel env add STRIPE_SECRET_KEY production
npx vercel --prod
```

Project root for Vercel is `web/` (this folder).

## Acceptance checks

- [ ] Home shows brand **AfterCrash** and “what we will not do”
- [ ] `/pack` completes all steps; unpaid users see limited checklist
- [ ] With Stripe Test Mode: Checkout → `/success` → PDF downloads with disclaimer footer
- [ ] `/faq` refuses fault % / legal advice / CTE diagnosis
- [ ] `/lawyers` only links Law Society public directory (no paid referral)

## Sample PDF

`fixtures/sample-pack.pdf` (regenerate: `node scripts/generate-sample-pdf.mjs`)

## Stop criteria (from BP)

If after Phase 2 validation there is no measurable funnel improvement, stop amplifying spend; do not escalate to large capital solely on hope.
