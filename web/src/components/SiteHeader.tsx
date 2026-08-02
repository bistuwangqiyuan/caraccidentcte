import Link from "next/link";
import { BRAND } from "../../content/compliance";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand">
        {BRAND.name}
      </Link>
      <nav>
        <Link href="/pack">Build pack</Link>
        <Link href="/pricing">Pricing</Link>
        <Link href="/faq">FAQ</Link>
        <Link href="/lawyers">Find a lawyer</Link>
      </nav>
    </header>
  );
}
