import { CheckoutButton } from "@/components/CheckoutButton";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import { PRICE_SGD } from "../../../content/compliance";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing",
};

export default async function PricingPage({
  searchParams,
}: {
  searchParams: Promise<{ cancelled?: string }>;
}) {
  const sp = await searchParams;
  return (
    <div className="prose">
      <h1>Pricing</h1>
      <p className="price">S${PRICE_SGD}</p>
      <p className="muted">One-time unlock · full PDF export · no subscription in v1</p>
      {sp.cancelled ? <p className="lock-note">Checkout cancelled. You can try again anytime.</p> : null}
      <DisclaimerBanner />
      <ul>
        <li>Full evidence + FNOL checklist in your PDF</li>
        <li>Your timeline and notes included</li>
        <li>Clear disclaimers on every page of the export</li>
        <li>No photo storage on our servers (v1)</li>
      </ul>
      <CheckoutButton />
      <p className="muted" style={{ marginTop: "1.5rem" }}>
        Payments via Stripe. Use test cards when the deployment is in Test Mode.
      </p>
    </div>
  );
}
