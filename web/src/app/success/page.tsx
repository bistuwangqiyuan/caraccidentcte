import { Suspense } from "react";
import { SuccessClient } from "@/components/SuccessClient";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Payment success",
  robots: { index: false, follow: false },
};

export default function SuccessPage() {
  return (
    <div className="prose">
      <h1>Thank you</h1>
      <DisclaimerBanner />
      <Suspense fallback={<p className="muted">Loading…</p>}>
        <SuccessClient />
      </Suspense>
    </div>
  );
}
