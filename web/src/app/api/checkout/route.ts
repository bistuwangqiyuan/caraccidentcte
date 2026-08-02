import { NextRequest, NextResponse } from "next/server";
import { getStripe, siteUrl, CURRENCY, PRICE_CENTS, PRICE_SGD } from "@/lib/stripe";
import { rateLimit } from "@/lib/rate-limit";

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  if (!rateLimit(`checkout:${ip}`, 15, 60_000)) {
    return NextResponse.json({ error: "Too many requests. Try again shortly." }, { status: 429 });
  }

  const stripe = getStripe();
  if (!stripe || !process.env.UNLOCK_SECRET) {
    return NextResponse.json(
      {
        error:
          "Payments are not configured yet. Set STRIPE_SECRET_KEY and UNLOCK_SECRET in the environment.",
        code: "NOT_CONFIGURED",
      },
      { status: 503 },
    );
  }

  const base = siteUrl();
  const priceId = process.env.STRIPE_PRICE_ID;

  try {
    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      success_url: `${base}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${base}/pricing?cancelled=1`,
      line_items: priceId
        ? [{ price: priceId, quantity: 1 }]
        : [
            {
              quantity: 1,
              price_data: {
                currency: CURRENCY,
                unit_amount: PRICE_CENTS,
                product_data: {
                  name: "AfterCrash SG Evidence Pack",
                  description: `One-time unlock to export your full evidence & FNOL checklist PDF (S$${PRICE_SGD}). Not legal advice.`,
                },
              },
            },
          ],
      metadata: { product: "aftercrash_sg_pack" },
    });

    return NextResponse.json({ url: session.url, id: session.id });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Checkout failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
