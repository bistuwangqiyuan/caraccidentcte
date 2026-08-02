import { FAQ } from "../../../content/faq";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FAQ",
};

export default function FaqPage() {
  return (
    <div className="prose">
      <h1>FAQ</h1>
      <DisclaimerBanner />
      <div className="faq">
        {FAQ.map((item) => (
          <details key={item.q}>
            <summary>{item.q}</summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}
