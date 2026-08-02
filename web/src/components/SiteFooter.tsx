import Link from "next/link";
import { FOOTER_LINE } from "../../content/compliance";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <p className="footer-line">{FOOTER_LINE}</p>
      <div className="footer-links">
        <Link href="/privacy">Privacy</Link>
        <Link href="/terms">Terms</Link>
        <Link href="/faq">FAQ</Link>
      </div>
    </footer>
  );
}
