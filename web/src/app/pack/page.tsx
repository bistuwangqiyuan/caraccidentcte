import { PackWizard } from "@/components/PackWizard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Build pack",
};

export default function PackPage() {
  return <PackWizard />;
}
