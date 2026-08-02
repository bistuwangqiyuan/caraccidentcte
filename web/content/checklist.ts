export type SceneId = "car_car" | "car_motorcycle" | "pedestrian" | "parking" | "other";

export const SCENES: { id: SceneId; label: string; hint: string }[] = [
  { id: "car_car", label: "Vehicle vs vehicle", hint: "Two or more cars/vans involved" },
  { id: "car_motorcycle", label: "Involving a motorcycle", hint: "Bike or pillion rider present" },
  { id: "pedestrian", label: "Pedestrian or cyclist", hint: "Person on foot or bicycle" },
  { id: "parking", label: "Parking / low-speed", hint: "Carpark scrape, reversing, etc." },
  { id: "other", label: "Other / unsure", hint: "Use a general checklist" },
];

export type ChecklistItem = { id: string; label: string; detail: string };

export const EVIDENCE_ITEMS: ChecklistItem[] = [
  { id: "e1", label: "Wide shot of the scene", detail: "Show road layout, lanes, and relative vehicle positions." },
  { id: "e2", label: "Close-ups of all vehicle damage", detail: "Each damaged panel; include paint transfer if visible." },
  { id: "e3", label: "Number plates of all vehicles", detail: "Clear, readable photos of every plate involved." },
  { id: "e4", label: "Road markings & traffic signs", detail: "Stop lines, arrows, signals, speed signs nearby." },
  { id: "e5", label: "Weather and lighting", detail: "Note rain, glare, night lighting; photo if useful." },
  { id: "e6", label: "Dashcam / camera footage", detail: "Export clip; note device time vs actual time." },
  { id: "e7", label: "Witness names & contacts", detail: "With their consent; do not pressure anyone." },
  { id: "e8", label: "Police report / case reference", detail: "If Traffic Police attended, keep the reference number." },
  { id: "e9", label: "Repair quotations", detail: "Keep written quotes from workshops (for your records)." },
  { id: "e10", label: "Medical notes (if injured)", detail: "Keep your own medical documents; do not share online unnecessarily." },
];

export const FNOL_ITEMS: ChecklistItem[] = [
  { id: "f1", label: "Policy number & insurer name", detail: "From your certificate of insurance or app." },
  { id: "f2", label: "Date, time, and location", detail: "Be as precise as you can (road name, nearby landmark)." },
  { id: "f3", label: "Vehicles & drivers involved", detail: "Plates, make/model if known; other parties’ contact if shared." },
  { id: "f4", label: "Brief factual description", detail: "What you observed — not legal conclusions about fault." },
  { id: "f5", label: "Injuries (if any)", detail: "Whether anyone reported injury; seek medical help as needed." },
  { id: "f6", label: "Police involvement", detail: "Whether a report was lodged and any reference number." },
  { id: "f7", label: "Photos / videos inventory", detail: "List what you captured (filenames or short labels)." },
  { id: "f8", label: "Third-party insurer details", detail: "If the other party shared them — optional." },
];

export type PackState = {
  scene: SceneId | "";
  evidenceChecked: string[];
  fnolChecked: string[];
  when: string;
  where: string;
  timeline: string;
  notes: string;
  email: string;
};

export const emptyPack = (): PackState => ({
  scene: "",
  evidenceChecked: [],
  fnolChecked: [],
  when: "",
  where: "",
  timeline: "",
  notes: "",
  email: "",
});
