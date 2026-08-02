"""独立复算关键指标 + 回放 render_manifest + 基本 PDF 检查。"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from common import OUTPUT_DIR, REPORT_DIR, ROOT, ValueRegistry, cagr, kelly_binary, load_yaml, read_json

YEARS = 5.0
EPS = 1e-9


def approx(a, b, tol=1e-6, rel=1e-6) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) and math.isnan(b):
            return True
        diff = abs(float(a) - float(b))
        scale = max(abs(float(a)), abs(float(b)), 1.0)
        return diff <= tol or diff / scale <= rel
    return a == b


def check_audit() -> list[str]:
    errs = []
    audit = read_json("audit_original")
    m = audit["math_block"]
    M = 1 + audit["claimed"]["roi5_small"]
    ann = cagr(M, YEARS)
    if not approx(ann, m["book_annualised"]):
        errs.append(f"audit book_annualised {m['book_annualised']} != {ann}")
    p = audit["claimed"]["win_rate_mid"]
    ev0 = p * M
    ev1 = p * M + (1 - p)
    if not approx(ev0, m["ev_loss_to_zero"]):
        errs.append("audit ev_zero mismatch")
    if not approx(ev1, m["ev_loss_to_breakeven"]):
        errs.append("audit ev_be mismatch")
    return errs


def check_risk() -> list[str]:
    errs = []
    cfg = load_yaml("assumptions.yaml")
    raw = np.load(OUTPUT_DIR / "mc_raw.npz")
    total_return = raw["total_return"]
    hours = raw["hours_total"]
    cash = float(cfg["capital"]["risk_capital_usd"])
    rate = float(cfg["opportunity_cost"]["shadow_hourly_usd"])
    stake = cash + hours * rate
    pi = total_return - stake
    win = pi > 0
    p_win = float(win.mean())
    risk = read_json("risk_metrics")
    if not approx(p_win, risk["primary"]["win_rate"], tol=1e-4, rel=1e-4):
        errs.append(f"win_rate {risk['primary']['win_rate']} != recomputed {p_win}")
    agg = float(total_return.sum() / stake.sum())
    if not approx(agg, risk["primary"]["aggregate_moic"], tol=1e-4, rel=1e-4):
        errs.append("aggregate_moic mismatch")
    ra = cagr(max(agg, 1e-12), YEARS)
    if not approx(ra, risk["primary"]["risk_adj_annualised_probweighted"], tol=1e-4, rel=1e-4):
        errs.append("risk_adj mismatch")

    # Kelly bankroll identity
    k = risk["kelly_1m_cny"]
    if not approx(k["full_kelly_cny"], k["bankroll_cny"] * k["f_star_numeric"]):
        errs.append("full kelly cny identity")
    if not approx(k["half_kelly_cny"], k["full_kelly_cny"] / 2):
        errs.append("half kelly identity")

    # binary kelly sample: at p=0.20, b=3 → f*=(0.6-0.8)/3 < 0; at p=0.40, b=3 → positive
    f_pos = kelly_binary(0.40, 3.0)
    f_zero = kelly_binary(0.125, 7.0)  # bp=q → 0
    if f_pos <= 0:
        errs.append(f"unexpected non-positive kelly on demo point: {f_pos}")
    if not approx(f_zero, 0.0, tol=1e-9):
        errs.append(f"kelly at breakeven odds should be ~0, got {f_zero}")
    return errs


def check_scoring_winner() -> list[str]:
    errs = []
    scoring = read_json("scoring")
    bp = read_json("bp_plan")
    if scoring["winner"]["id"] != bp["winner_id"]:
        errs.append("bp_plan winner_id != scoring winner")
    if scoring["n_eliminated"] < 1:
        errs.append("expected at least one kill-gate elimination")
    # evidence-fnol-sg should survive; liability should be eliminated
    elim_ids = {e["id"] for e in scoring["eliminated"]}
    if "liability-ai-legal" not in elim_ids:
        errs.append("liability-ai-legal should be eliminated")
    if "cte-diagnosis" not in elim_ids:
        errs.append("cte-diagnosis should be eliminated")
    return errs


def check_manifest() -> list[str]:
    errs = []
    man_path = OUTPUT_DIR / "render_manifest.json"
    html_path = REPORT_DIR / "index.html"
    if not man_path.exists():
        return ["missing render_manifest.json"]
    if not html_path.exists():
        return ["missing report/index.html"]
    man = json.loads(man_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    reg = ValueRegistry()
    for e in man["entries"]:
        path, fmt, rendered = e["path"], e["fmt"], e["rendered"]
        try:
            again = reg.v(path, fmt)
        except Exception as exc:  # noqa: BLE001
            errs.append(f"replay fail {path}: {exc}")
            continue
        if again != rendered:
            errs.append(f"replay mismatch {path}: {rendered!r} vs {again!r}")
        if rendered and rendered not in html and rendered != "n/a":
            # bool 是/否 and some footnotes may be truncated in HTML — only flag numbers-like
            if any(ch.isdigit() for ch in rendered):
                errs.append(f"rendered value not in HTML: {path} -> {rendered!r}")
    return errs


def check_pdf() -> list[str]:
    errs = []
    pdf = REPORT_DIR / "商业机会挖掘与分析报告.pdf"
    if not pdf.exists():
        return ["PDF missing (run without --no-pdf)"]
    data = pdf.read_bytes()
    if len(data) < 50_000:
        errs.append(f"PDF too small: {len(data)} bytes")
    pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    if pages < 6:
        errs.append(f"PDF pages too few: {pages}")
    return errs


def main() -> int:
    errors: list[str] = []
    for name, fn in [
        ("audit", check_audit),
        ("risk", check_risk),
        ("scoring", check_scoring_winner),
        ("manifest", check_manifest),
        ("pdf", check_pdf),
    ]:
        e = fn()
        if e:
            print(f"[FAIL] {name}:")
            for x in e:
                print(f"  - {x}")
            errors.extend(e)
        else:
            print(f"[OK] {name}")
    if errors:
        print(f"\n{len(errors)} errors")
        return 1
    print("\nverify_all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
