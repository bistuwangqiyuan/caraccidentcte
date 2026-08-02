import Stripe from "stripe";
import { CURRENCY, PRICE_CENTS, PRICE_SGD } from "../../content/compliance";

export function getStripe(): Stripe | null {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) return null;
  return new Stripe(key);
}

export function siteUrl(): string {
  return (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
}

export { CURRENCY, PRICE_CENTS, PRICE_SGD };
