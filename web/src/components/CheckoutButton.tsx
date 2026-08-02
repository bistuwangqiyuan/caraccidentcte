"use client";

import { useState } from "react";
import { PRICE_SGD } from "../../content/compliance";

export function CheckoutButton() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/checkout", { method: "POST" });
      const data = (await res.json()) as { url?: string; error?: string; code?: string };
      if (!res.ok || !data.url) {
        setError(
          data.error ||
            (data.code === "NOT_CONFIGURED"
              ? "Stripe is not configured on this deployment yet."
              : "Could not start checkout."),
        );
        return;
      }
      window.location.href = data.url;
    } catch {
      setError("Network error starting checkout.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button className="btn" type="button" onClick={start} disabled={loading}>
        {loading ? "Redirecting…" : `Pay S$${PRICE_SGD} with Stripe`}
      </button>
      {error ? (
        <p className="lock-note" role="alert" style={{ marginTop: "1rem" }}>
          {error}
        </p>
      ) : null}
    </div>
  );
}
