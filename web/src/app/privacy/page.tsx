import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy",
};

export default function PrivacyPage() {
  return (
    <div className="prose">
      <h1>Privacy</h1>
      <DisclaimerBanner />
      <h2>What we collect</h2>
      <p>
        In v1, your checklist answers and timeline stay in your browser session storage until you
        clear them. We do not operate a database of accident narratives. Payment is processed by
        Stripe; we receive payment confirmation identifiers needed to unlock export.
      </p>
      <h2>What we do not collect (v1)</h2>
      <p>We do not accept uploads of photos, videos, NRIC images, or medical scans.</p>
      <h2>Purpose limitation</h2>
      <p>
        Data is used only to provide the checklist tool and payment unlock. We do not sell personal
        data. For Singapore PDPA questions about your own insurer or lawyer, contact them directly.
      </p>
      <h2>Contact</h2>
      <p>
        For privacy requests related to this site, use the email associated with your Stripe receipt
        or the project maintainer contact published on the GitHub repository.
      </p>
    </div>
  );
}
