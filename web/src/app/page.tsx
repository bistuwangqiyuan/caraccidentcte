import Link from "next/link";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import { BRAND, NOT_PROMISE, PRICE_SGD } from "../../content/compliance";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <p className="muted" style={{ letterSpacing: "0.12em", textTransform: "uppercase", fontSize: "0.75rem" }}>
          Singapore · self-serve tool
        </p>
        <h1>{BRAND.name}</h1>
        <p className="lede">{BRAND.promise}</p>
        <div className="cta-row">
          <Link className="btn" href="/pack">
            Start your pack
          </Link>
          <Link className="btn secondary" href="/pricing">
            S${PRICE_SGD} unlock
          </Link>
        </div>
      </section>

      <DisclaimerBanner />

      <section className="section">
        <h2>What this is</h2>
        <p className="muted">
          After a road incident, people often lose track of photos, facts, and insurer paperwork.
          AfterCrash walks you through a practical checklist and exports a PDF you can keep or share
          with <em>your</em> insurer or <em>your own</em> lawyer.
        </p>
      </section>

      <section className="section">
        <h2>What we will not do</h2>
        <ul className="not-list">
          {NOT_PROMISE.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="section">
        <h2>How it works</h2>
        <ol>
          <li>Choose your situation and tick what you have gathered.</li>
          <li>Write a short factual timeline in your own words.</li>
          <li>Preview freely; unlock full PDF export for a one-time S${PRICE_SGD}.</li>
        </ol>
        <div className="cta-row">
          <Link className="btn" href="/pack">
            Build pack
          </Link>
          <Link className="btn secondary" href="/faq">
            Read FAQ
          </Link>
        </div>
      </section>
    </>
  );
}
