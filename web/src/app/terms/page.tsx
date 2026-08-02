import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import { NOT_PROMISE } from "../../../content/compliance";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms",
};

export default function TermsPage() {
  return (
    <div className="prose">
      <h1>Terms of use</h1>
      <DisclaimerBanner />
      <h2>Service description</h2>
      <p>
        AfterCrash provides a self-serve checklist and PDF export to help you organise post-accident
        information. It is not a law firm, clinic, or insurance intermediary.
      </p>
      <h2>Prohibited expectations</h2>
      <ul>
        {NOT_PROMISE.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
      <h2>Payments</h2>
      <p>
        One-time fees unlock PDF export. Refunds for digital unlocks are considered only where
        required by applicable law or Stripe dispute outcomes.
      </p>
      <h2>No warranties</h2>
      <p>
        The tool is provided as-is. Checklist completeness depends on your inputs. Official
        requirements may differ by insurer and case.
      </p>
      <h2>Governing approach</h2>
      <p>
        Use this site in good faith. Do not misuse it to harass others or to pretend it is an
        official government or legal determination.
      </p>
    </div>
  );
}
