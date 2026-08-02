"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { loadPack } from "@/lib/pack-storage";
import { downloadPackPdf } from "@/lib/pdf";

export function SuccessClient() {
  const params = useSearchParams();
  const sessionId = params.get("session_id") || "";
  const [status, setStatus] = useState<"loading" | "ok" | "err">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!sessionId) {
      setStatus("err");
      setMessage("Missing session_id.");
      return;
    }
    fetch("/api/checkout/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "Verification failed");
        setStatus("ok");
      })
      .catch((e: Error) => {
        setStatus("err");
        setMessage(e.message);
      });
  }, [sessionId]);

  const download = () => {
    downloadPackPdf(loadPack());
  };

  if (status === "loading") return <p className="muted">Confirming payment…</p>;
  if (status === "err") {
    return (
      <div>
        <p className="lock-note" role="alert">
          {message}
        </p>
        <Link className="btn secondary" href="/pricing">
          Back to pricing
        </Link>
      </div>
    );
  }

  return (
    <div>
      <p>Payment confirmed. Your pack is unlocked on this browser for 7 days.</p>
      <div className="cta-row">
        <button className="btn" type="button" onClick={download}>
          Download PDF now
        </button>
        <Link className="btn secondary" href="/pack">
          Review pack
        </Link>
      </div>
    </div>
  );
}
