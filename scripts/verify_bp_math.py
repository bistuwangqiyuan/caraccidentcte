"""原稿口径的确定性复算（对应 data/need_original.txt 文末【复算校准】）。

用法：python scripts/verify_bp_math.py
写出：outputs/bp_math_check.json
"""

from __future__ import annotations

from common import cagr, write_json

ROI5_PCT = 6.0
P_MID = 0.125
YEARS = 5.0
SELF = {
    "annualised": 0.90,
    "moic": 1.5,
    "risk_adj": 0.20,
}


def main() -> dict:
    M = 1 + ROI5_PCT / 100.0
    ann = cagr(M, YEARS)
    ev0 = P_MID * M
    ev1 = P_MID * M + (1 - P_MID)
    ra0 = cagr(ev0, YEARS) if ev0 > 0 else -1.0
    ra1 = cagr(ev1, YEARS)
    return {
        "inputs": {"roi5_pct": ROI5_PCT, "p_mid": P_MID, "years": YEARS},
        "M": M,
        "book_annualised": ann,
        "ev_loss_to_zero": ev0,
        "ev_loss_to_breakeven": ev1,
        "risk_adj_zero": ra0,
        "risk_adj_breakeven": ra1,
        "self_reported": SELF,
        "consistent_with_self": {
            "annualised": abs(ann - SELF["annualised"]) < 1e-3,
            "moic_in_ev_band": ev0 - 1e-9 <= SELF["moic"] <= ev1 + 1e-9,
            "risk_adj_in_band": ra0 - 1e-9 <= SELF["risk_adj"] <= ra1 + 1e-9,
        },
        "note_zh": "自报与复算不一致时以复算为准；完整项目请跑 scripts/run_all.py。",
    }


if __name__ == "__main__":
    r = main()
    write_json("bp_math_check", r)
    print(r)
