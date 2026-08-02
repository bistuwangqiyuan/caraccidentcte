import type { Metadata } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { BRAND, FOOTER_LINE } from "../../content/compliance";

export const metadata: Metadata = {
  title: {
    default: `${BRAND.name} · Singapore post-accident checklist`,
    template: `%s · ${BRAND.name}`,
  },
  description: BRAND.promise,
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <SiteHeader />
          <main>{children}</main>
          <SiteFooter />
        </div>
        <span className="sr-only">{FOOTER_LINE}</span>
      </body>
    </html>
  );
}
