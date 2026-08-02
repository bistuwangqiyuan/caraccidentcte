import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Find a lawyer",
};

export default function LawyersPage() {
  return (
    <div className="prose">
      <h1>Find a practising lawyer</h1>
      <DisclaimerBanner />
      <p>
        AfterCrash does not recommend, rank, or take fees for lawyer referrals. For Singapore legal
        advice, use the Law Society’s public directory and verify a practising certificate yourself.
      </p>
      <p>
        <a
          href="https://www.lawsociety.org.sg/for-public/find-a-lawyer/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Law Society of Singapore — Find a Lawyer
        </a>
      </p>
      <p className="muted">
        We do not share contingency fees, do not send your case details to lawyers, and do not claim
        endorsement by the Law Society.
      </p>
    </div>
  );
}
