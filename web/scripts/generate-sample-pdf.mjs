import { jsPDF } from "jspdf";
import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const out = join(__dirname, "..", "fixtures", "sample-pack.pdf");

const doc = new jsPDF({ unit: "mm", format: "a4" });
doc.setFont("helvetica", "bold");
doc.setFontSize(18);
doc.text("AfterCrash — sample pack", 18, 24);
doc.setFont("helvetica", "normal");
doc.setFontSize(10);
const lines = doc.splitTextToSize(
  "This is a sample PDF fixture for documentation. Production exports include full disclaimers: not legal advice, not a determination of fault, not affiliated with SPF/LTA/Law Society.",
  174,
);
doc.text(lines, 18, 36);
doc.text("Evidence checklist (sample): [x] Wide shot  [x] Plates  [ ] Dashcam", 18, 60);
doc.text("FNOL prep (sample): [x] Policy number  [x] Date/time/location", 18, 70);
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, Buffer.from(doc.output("arraybuffer")));
console.log("wrote", out);
