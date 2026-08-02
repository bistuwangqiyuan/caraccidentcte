"""胜率、盈亏比、风险调整年化、Kelly（含 100 万人民币理论仓位）。"""

from __future__ import annotations

import numpy as np

from common import OUTPUT_DIR, cagr, kelly_binary, load_yaml

YEARS = 5.0


def kelly_growth_rate(returns: np.ndarray, f: float) -> float:
    x = 1.0 + f * returns
    if np.any(x <= 1e-12):
        return -np.inf
    return float(np.mean(np.log(x)))


def optimal_kelly_fraction(returns: np.ndarray) -> tuple[float, float]:
    worst = float(returns.min())
    f_max = 0.999 if worst >= 0 else min(0.999, 0.999 / abs(worst))
    if f_max <= 1e-6:
        return 0.0, 0.0
    grid = np.linspace(1e-6, f_max, 2000)
    vals = np.array([kelly_growth_rate(returns, f) for f in grid])
    if np.all(~np.isfinite(vals)):
        return 0.0, 0.0
    best = int(np.nanargmax(vals))
    lo = grid[max(best - 1, 0)]
    hi = grid[min(best + 1, len(grid) - 1)]
    fine = np.linspace(lo, hi, 500)
    fvals = np.array([kelly_growth_rate(returns, f) for f in fine])
    bi = int(np.nanargmax(fvals))
    f_star = float(fine[bi])
    g_star = float(fvals[bi])
    if f_star <= 1e-5 or g_star <= 0:
        return 0.0, max(g_star, 0.0)
    return f_star, g_star


def main() -> dict:
    cfg = load_yaml("assumptions.yaml")
    raw = np.load(OUTPUT_DIR / "mc_raw.npz")
    total_return = raw["total_return"]
    hours = raw["hours_total"]

    shadow = float(cfg["opportunity_cost"]["shadow_hourly_usd"])
    shadow_low = float(cfg["opportunity_cost"]["shadow_hourly_low"])
    shadow_high = float(cfg["opportunity_cost"]["shadow_hourly_high"])
    cash_stake = float(cfg["capital"]["risk_capital_usd"])
    bankroll_cny = float(cfg["capital"]["theoretical_bankroll_cny"])
    cny_usd = float(cfg["meta"]["fx"]["cny_usd"])
    bankroll_usd = bankroll_cny * cny_usd

    def metrics_at_rate(rate: float) -> dict:
        stake = cash_stake + hours * rate
        pi = total_return - stake
        moic = total_return / stake
        r = pi / stake
        win = pi > 0
        p_win = float(win.mean())
        avg_win = float(pi[win].mean()) if win.any() else 0.0
        avg_loss = float((-pi[~win]).mean()) if (~win).any() else 0.0
        payoff = float(avg_win / avg_loss) if avg_loss > 0 else None
        aggregate_moic = float(total_return.sum() / stake.sum())
        mean_per_run_moic = float(moic.mean())
        ra_prob = cagr(max(aggregate_moic, 1e-12), YEARS)
        f_star, g_star = optimal_kelly_fraction(r)
        f_bin = (
            float((p_win * payoff - (1 - p_win)) / payoff)
            if payoff and payoff > 0
            else None
        )
        # EV 区间（二值近似，用 aggregate_moic 作为赢局倍数代理需谨慎）
        # 更干净：用胜率与「赢时平均 MOIC / 输时平均 MOIC」
        moic_win = float(moic[win].mean()) if win.any() else 0.0
        moic_loss = float(moic[~win].mean()) if (~win).any() else 0.0
        # 亏损归零口径：输局期末倍数记 0
        ev_zero = p_win * moic_win
        ev_be = p_win * moic_win + (1 - p_win) * 1.0  # 保本：输局记 1.0 不合理若已亏；改用
        # 上界：输局按实际平均 moic_loss（若>0）与 1.0 取 max 的保守「不差于保本」叙事
        # 按计划：EV=[p×M, p×M+(1-p)] 其中 M 为赢局倍数、输局 0 或 1
        M = moic_win if moic_win > 0 else aggregate_moic
        ev_loss_zero = p_win * M
        ev_loss_breakeven = p_win * M + (1 - p_win) * 1.0
        ra_zero = cagr(max(ev_loss_zero, 1e-12), YEARS)
        ra_be = cagr(max(ev_loss_breakeven, 1e-12), YEARS)

        return {
            "shadow_hourly_usd": rate,
            "mean_stake_usd": float(stake.mean()),
            "win_rate": p_win,
            "avg_win_usd": avg_win,
            "avg_loss_usd": avg_loss,
            "payoff_ratio": payoff,
            "aggregate_moic": aggregate_moic,
            "mean_per_run_moic": mean_per_run_moic,
            "median_moic": float(np.median(moic)),
            "moic_p05": float(np.percentile(moic, 5)),
            "moic_p95": float(np.percentile(moic, 95)),
            "mean_moic_if_win": moic_win,
            "mean_moic_if_loss": moic_loss,
            "ev_loss_to_zero": ev_loss_zero,
            "ev_loss_to_breakeven": ev_loss_breakeven,
            "risk_adj_annualised_probweighted": ra_prob,
            "risk_adj_annualised_ev_zero": ra_zero,
            "risk_adj_annualised_ev_breakeven": ra_be,
            "kelly_fraction_numeric": f_star,
            "kelly_growth_rate_log": g_star,
            "kelly_annualised_growth": float(np.exp(g_star) - 1.0) if g_star > 0 else 0.0,
            "kelly_fraction_binary": f_bin,
            "fractional_kelly_half": f_star / 2,
            "fractional_kelly_quarter": f_star / 4,
            "expected_return_usd": float(total_return.mean()),
            "p_total_loss": float((total_return <= 0).mean()),
        }

    primary = metrics_at_rate(shadow)
    low = metrics_at_rate(shadow_low)
    high = metrics_at_rate(shadow_high)

    # 100 万 CNY Kelly 仓位
    f_full = primary["kelly_fraction_numeric"]
    f_bin = primary["kelly_fraction_binary"] or 0.0
    # 敏感性网格
    p_grid = [0.05, 0.08, 0.10, 0.125, 0.15, 0.20, 0.30]
    b_grid = [0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    sens = []
    for p in p_grid:
        for b in b_grid:
            f = kelly_binary(p, b)
            sens.append({
                "p": p,
                "b": b,
                "f_star": f,
                "stake_cny_full": bankroll_cny * max(f, 0.0),
                "stake_cny_half": bankroll_cny * max(f, 0.0) / 2,
                "stake_cny_quarter": bankroll_cny * max(f, 0.0) / 4,
            })

    kelly_capital = {
        "bankroll_cny": bankroll_cny,
        "bankroll_usd": bankroll_usd,
        "fx_cny_usd": cny_usd,
        "f_star_numeric": f_full,
        "f_star_binary": f_bin,
        "full_kelly_cny": bankroll_cny * f_full,
        "half_kelly_cny": bankroll_cny * f_full / 2,
        "quarter_kelly_cny": bankroll_cny * f_full / 4,
        "full_kelly_usd": bankroll_usd * f_full,
        "half_kelly_usd": bankroll_usd * f_full / 2,
        "quarter_kelly_usd": bankroll_usd * f_full / 4,
        "operational_risk_capital_usd": cash_stake,
        "disclaimer_zh": (
            "理论 Kelly 回答的是『若这是可重复边缘赌注且 p、b 已知，应占资金池多大』；"
            "不等于建议把 100 万立刻投入本项目。精益执行仍受 US$2,000 运营风险资本约束。"
            "p 为估计值，须连同敏感性网格阅读。"
        ),
    }

    # 时间 Kelly：5 年可用工时 vs 单次尝试工时
    hours_budget = float(cfg["operating"]["hours_per_week"]) * 52 * YEARS
    mean_hours = float(hours.mean())
    time_f = (mean_hours / hours_budget) if hours_budget > 0 else None
    # 用与资本相同的 f* 解释「应把多大比例时间预算押在单一想法」
    time_kelly = {
        "hours_budget_5y": hours_budget,
        "mean_hours_per_attempt": mean_hours,
        "naive_attempt_fraction_of_budget": time_f,
        "recommended_ideas_at_half_kelly": (
            float(1.0 / (primary["fractional_kelly_half"])) if primary["fractional_kelly_half"] > 1e-6 else None
        ),
        "phase0_hours_committed": 20.0,
        "note_zh": "分阶段：Phase0 仅承诺约 20 小时验证，保留放弃期权。",
    }

    mean_hours = float(hours.mean())
    breakeven_rate = (float(total_return.mean()) - cash_stake) / mean_hours if mean_hours else 0.0
    sweep_rates = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 80.0]
    shadow_sweep = []
    for r in sweep_rates:
        m = metrics_at_rate(r)
        shadow_sweep.append({
            "shadow_hourly_usd": r,
            "win_rate": m["win_rate"],
            "aggregate_moic": m["aggregate_moic"],
            "payoff_ratio": m["payoff_ratio"],
            "kelly_fraction": m["kelly_fraction_numeric"],
            "risk_adjusted_annualised": m["risk_adj_annualised_probweighted"],
        })

    stake_base = cash_stake + hours * shadow
    moic_realised = total_return / stake_base
    band_edges = [-1e99, 0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 1e99]
    band_labels = [
        "负回报（<0x）",
        "近乎全损（0–0.1x）",
        "重大亏损（0.1–0.5x）",
        "小幅亏损（0.5–1x）",
        "小胜（1–2x）",
        "良好（2–5x）",
        "优异（≥5x）",
    ]
    bands = []
    for i, label in enumerate(band_labels):
        mask = (moic_realised > band_edges[i]) & (moic_realised <= band_edges[i + 1])
        # first band uses >= for -inf
        if i == 0:
            mask = moic_realised <= band_edges[1]
        bands.append({"label": label, "probability": float(mask.mean())})

    # 原稿对照
    original = {
        "self_annualised": 0.90,
        "self_win_rate_mid": 0.125,
        "self_payoff": 7.0,
        "self_moic": 1.5,
        "self_risk_adj": 0.20,
        "recomputed_book_annualised_roi5_6pct": cagr(1.06, YEARS),
    }

    return {
        "years": YEARS,
        "primary": primary,
        "shadow_low": low,
        "shadow_high": high,
        "breakeven_shadow_hourly_usd": breakeven_rate,
        "shadow_sweep": shadow_sweep,
        "outcome_bands": bands,
        "kelly_1m_cny": kelly_capital,
        "kelly_sensitivity": sens,
        "time_kelly": time_kelly,
        "original_contrast": original,
        "decision_zh": (
            "以主口径影子时薪下的胜率、盈亏比与半 Kelly 为决策参考；"
            "若半 Kelly 对应金额仍高于精益风险资本，执行层仍按 US$2,000 封顶分阶段投入。"
        ),
    }


if __name__ == "__main__":
    from common import write_json
    write_json("risk_metrics", main())
    print("wrote outputs/risk_metrics.json")
