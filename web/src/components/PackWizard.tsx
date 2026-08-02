"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  EVIDENCE_ITEMS,
  FNOL_ITEMS,
  SCENES,
  type PackState,
} from "../../content/checklist";
import {
  FREE_PREVIEW_EVIDENCE,
  FREE_PREVIEW_FNOL,
  PRICE_SGD,
} from "../../content/compliance";
import { loadPack, savePack } from "@/lib/pack-storage";
import { downloadPackPdf } from "@/lib/pdf";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";

const STEPS = ["Scene", "Evidence", "Timeline", "FNOL", "Export"] as const;

export function PackWizard() {
  const [step, setStep] = useState(0);
  const [pack, setPack] = useState<PackState | null>(null);
  const [unlocked, setUnlocked] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setPack(loadPack());
    fetch("/api/unlock")
      .then((r) => r.json())
      .then((d: { unlocked?: boolean }) => setUnlocked(Boolean(d.unlocked)))
      .catch(() => setUnlocked(false));
  }, []);

  useEffect(() => {
    if (pack) savePack(pack);
  }, [pack]);

  const evidenceVisible = useMemo(
    () => (unlocked ? EVIDENCE_ITEMS : EVIDENCE_ITEMS.slice(0, FREE_PREVIEW_EVIDENCE)),
    [unlocked],
  );
  const fnolVisible = useMemo(
    () => (unlocked ? FNOL_ITEMS : FNOL_ITEMS.slice(0, FREE_PREVIEW_FNOL)),
    [unlocked],
  );

  if (!pack) return <p className="muted">Loading…</p>;

  const toggle = (key: "evidenceChecked" | "fnolChecked", id: string) => {
    setPack((p) => {
      if (!p) return p;
      const set = new Set(p[key]);
      if (set.has(id)) set.delete(id);
      else set.add(id);
      return { ...p, [key]: Array.from(set) };
    });
  };

  const onExport = () => {
    if (!unlocked) return;
    setBusy(true);
    try {
      downloadPackPdf(pack);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: "2rem" }}>Build your pack</h1>
      <DisclaimerBanner />
      <div className="wizard-steps">
        {STEPS.map((s, i) => (
          <span key={s} className={i === step ? "on" : undefined}>
            {i + 1}. {s}
          </span>
        ))}
      </div>

      {step === 0 && (
        <div>
          <p className="muted">Select the closest match. This only filters checklist emphasis.</p>
          <div className="check-list">
            {SCENES.map((s) => (
              <label key={s.id} className="check-item">
                <input
                  type="radio"
                  name="scene"
                  checked={pack.scene === s.id}
                  onChange={() => setPack({ ...pack, scene: s.id })}
                />
                <span>
                  <strong>{s.label}</strong>
                  <p className="detail">{s.hint}</p>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {step === 1 && (
        <div>
          <p className="muted">Tick items you already have or will gather. No photo upload in v1.</p>
          {!unlocked && (
            <p className="lock-note">
              Free preview shows {FREE_PREVIEW_EVIDENCE} items. Unlock (S${PRICE_SGD}) reveals the full list and PDF export.
            </p>
          )}
          <div className="check-list">
            {evidenceVisible.map((item) => (
              <label key={item.id} className="check-item">
                <input
                  type="checkbox"
                  checked={pack.evidenceChecked.includes(item.id)}
                  onChange={() => toggle("evidenceChecked", item.id)}
                />
                <span>
                  <strong>{item.label}</strong>
                  <p className="detail">{item.detail}</p>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          <div className="field">
            <label htmlFor="when">When (date / time)</label>
            <input
              id="when"
              value={pack.when}
              onChange={(e) => setPack({ ...pack, when: e.target.value })}
              placeholder="e.g. 2026-08-02 around 18:30"
            />
          </div>
          <div className="field">
            <label htmlFor="where">Where</label>
            <input
              id="where"
              value={pack.where}
              onChange={(e) => setPack({ ...pack, where: e.target.value })}
              placeholder="Road name / nearby landmark"
            />
          </div>
          <div className="field">
            <label htmlFor="timeline">Factual timeline (your words)</label>
            <textarea
              id="timeline"
              rows={6}
              value={pack.timeline}
              onChange={(e) => setPack({ ...pack, timeline: e.target.value })}
              placeholder="Describe what you observed. Avoid legal conclusions about fault."
            />
          </div>
          <div className="field">
            <label htmlFor="notes">Optional notes</label>
            <textarea
              id="notes"
              rows={3}
              value={pack.notes}
              onChange={(e) => setPack({ ...pack, notes: e.target.value })}
            />
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          <p className="muted">
            FNOL = First Notice of Loss — information insurers commonly ask for. This is a preparation list, not a filing service.
          </p>
          {!unlocked && (
            <p className="lock-note">
              Free preview shows {FREE_PREVIEW_FNOL} FNOL items. Full list unlocks with PDF export.
            </p>
          )}
          <div className="check-list">
            {fnolVisible.map((item) => (
              <label key={item.id} className="check-item">
                <input
                  type="checkbox"
                  checked={pack.fnolChecked.includes(item.id)}
                  onChange={() => toggle("fnolChecked", item.id)}
                />
                <span>
                  <strong>{item.label}</strong>
                  <p className="detail">{item.detail}</p>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {step === 4 && (
        <div>
          <p>
            Scene: <strong>{SCENES.find((s) => s.id === pack.scene)?.label || "—"}</strong>
          </p>
          <p className="muted">
            Evidence ticked: {pack.evidenceChecked.length} · FNOL ticked: {pack.fnolChecked.length}
          </p>
          {unlocked ? (
            <>
              <p>Your pack is unlocked. Download the PDF now (kept in your browser).</p>
              <button className="btn" type="button" onClick={onExport} disabled={busy}>
                {busy ? "Preparing…" : "Download PDF"}
              </button>
            </>
          ) : (
            <>
              <p className="lock-note">
                Preview is free. To export the full checklist PDF, unlock for a one-time S${PRICE_SGD}.
              </p>
              <Link className="btn" href="/pricing">
                Go to pricing
              </Link>
            </>
          )}
        </div>
      )}

      <div className="cta-row" style={{ marginTop: "1.75rem" }}>
        <button
          className="btn secondary"
          type="button"
          disabled={step === 0}
          onClick={() => setStep((s) => Math.max(0, s - 1))}
        >
          Back
        </button>
        {step < STEPS.length - 1 ? (
          <button className="btn" type="button" onClick={() => setStep((s) => s + 1)}>
            Continue
          </button>
        ) : null}
      </div>
    </div>
  );
}
