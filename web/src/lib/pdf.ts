import { jsPDF } from "jspdf";
import {
  DISCLAIMER_EN,
  DISCLAIMER_ZH,
  FOOTER_LINE,
  BRAND,
} from "../../content/compliance";
import {
  EVIDENCE_ITEMS,
  FNOL_ITEMS,
  SCENES,
  type PackState,
} from "../../content/checklist";

export function buildPackPdf(pack: PackState): jsPDF {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const margin = 18;
  let y = 22;
  const pageW = doc.internal.pageSize.getWidth();
  const maxW = pageW - margin * 2;

  const ensure = (need: number) => {
    if (y + need > 280) {
      doc.addPage();
      y = 22;
    }
  };

  const h1 = (t: string) => {
    ensure(14);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text(t, margin, y);
    y += 10;
  };

  const h2 = (t: string) => {
    ensure(12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text(t, margin, y);
    y += 7;
  };

  const para = (t: string, size = 10) => {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(size);
    const lines = doc.splitTextToSize(t, maxW) as string[];
    for (const line of lines) {
      ensure(6);
      doc.text(line, margin, y);
      y += 5;
    }
    y += 2;
  };

  // Cover / disclaimer
  h1(BRAND.name);
  para(BRAND.tagline, 11);
  y += 2;
  h2("Important disclaimer");
  para(DISCLAIMER_EN, 9);
  para(DISCLAIMER_ZH, 9);
  para(FOOTER_LINE, 8);

  doc.addPage();
  y = 22;

  h1("Your evidence & FNOL pack");
  const sceneLabel = SCENES.find((s) => s.id === pack.scene)?.label || "Not specified";
  para(`Scene type: ${sceneLabel}`);
  para(`When: ${pack.when || "—"}`);
  para(`Where: ${pack.where || "—"}`);

  h2("Timeline / factual notes (your words)");
  para(pack.timeline || "(empty)");
  if (pack.notes) {
    h2("Additional notes");
    para(pack.notes);
  }

  h2("Evidence checklist");
  for (const item of EVIDENCE_ITEMS) {
    const mark = pack.evidenceChecked.includes(item.id) ? "[x]" : "[ ]";
    para(`${mark} ${item.label} — ${item.detail}`, 9);
  }

  h2("FNOL preparation checklist");
  for (const item of FNOL_ITEMS) {
    const mark = pack.fnolChecked.includes(item.id) ? "[x]" : "[ ]";
    para(`${mark} ${item.label} — ${item.detail}`, 9);
  }

  y += 4;
  h2("Reminder");
  para(
    "This PDF is for your own organisation and to help you prepare information for your insurer or your own lawyer. It is not a police report, not an insurance decision, and not legal advice.",
    9,
  );

  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(110);
    doc.text(FOOTER_LINE, margin, 290, { maxWidth: maxW });
    doc.text(`Page ${i}/${pages}`, pageW - margin - 20, 290);
    doc.setTextColor(0);
  }

  return doc;
}

export function downloadPackPdf(pack: PackState, filename = "aftercrash-sg-pack.pdf") {
  const doc = buildPackPdf(pack);
  doc.save(filename);
}
