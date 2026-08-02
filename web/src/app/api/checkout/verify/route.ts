import { NextRequest, NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { MAX_AGE_SEC, signUnlock, unlockCookieOptions } from "@/lib/unlock";
import { rateLimit } from "@/lib/rate-limit";

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
  if (!rateLimit(`verify:${ip}`, 30, 60_000)) {
    return NextResponse.json({ error: "Too many requests." }, { status: 429 });
  }

  const stripe = getStripe();
  if (!stripe || !process.env.UNLOCK_SECRET) {
    return NextResponse.json({ error: "Not configured", code: "NOT_CONFIGURED" }, { status: 503 });
  }

  let sessionId = "";
  try {
    const body = (await req.json()) as { session_id?: string };
    sessionId = body.session_id || "";
  } catch {
    return NextResponse.json({ error: "Invalid body" }, { status: 400 });
  }

  if (!sessionId.startsWith("cs_")) {
    return NextResponse.json({ error: "Invalid session" }, { status: 400 });
  }

  try {
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    if (session.payment_status !== "paid" && session.status !== "complete") {
      return NextResponse.json({ error: "Payment not completed", paid: false }, { status: 402 });
    }

    const exp = Math.floor(Date.now() / 1000) + MAX_AGE_SEC;
    const token = signUnlock(sessionId, exp);
    const res = NextResponse.json({ paid: true, sessionId });
    const opt = unlockCookieOptions(token);
    res.cookies.set(opt);
    return res;
  } catch (e) {
    const message = e instanceof Error ? e.message : "Verify failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
