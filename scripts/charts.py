"""生成报告用 SVG 图表。"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from common import OUTPUT_DIR, PALETTE, SERIES_COLORS, apply_chart_theme, read_json, save_chart


def chart_scoring() -> None:
    scoring = read_json("scoring")
    names = [r["name"][:18] for r in scoring["ranking"]]
    totals = [r["total"] for r in scoring["ranking"]]
    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = np.arange(len(names))[::-1]
    ax.barh(y, totals[::-1], color=PALETTE["blue"], height=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(names[::-1])
    ax.set_xlabel("加权总分（0–10）")
    ax.set_xlim(0, 10)
    ax.set_title("存活候选加权得分")
    save_chart(fig, "scoring_bars")


def chart_outcome_bands() -> None:
    risk = read_json("risk_metrics")
    labels = [b["label"] for b in risk["outcome_bands"]]
    probs = [b["probability"] * 100 for b in risk["outcome_bands"]]
    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.bar(range(len(labels)), probs, color=PALETTE["teal"])
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("概率（%）")
    ax.set_title("经济 MOIC 结果分档（含影子时薪）")
    save_chart(fig, "outcome_bands")


def chart_shadow_sweep() -> None:
    risk = read_json("risk_metrics")
    xs = [r["shadow_hourly_usd"] for r in risk["shadow_sweep"]]
    wr = [r["win_rate"] * 100 for r in risk["shadow_sweep"]]
    ra = [r["risk_adjusted_annualised"] * 100 for r in risk["shadow_sweep"]]
    apply_chart_theme()
    fig, ax1 = plt.subplots(figsize=(7.2, 3.4))
    ax1.plot(xs, wr, color=PALETTE["blue"], label="胜率")
    ax1.set_xlabel("影子时薪（USD/小时）")
    ax1.set_ylabel("胜率（%）", color=PALETTE["blue"])
    ax2 = ax1.twinx()
    ax2.plot(xs, ra, color=PALETTE["orange"], label="风险调整年化")
    ax2.set_ylabel("风险调整年化（%）", color=PALETTE["orange"])
    ax1.set_title("影子时薪敏感性")
    save_chart(fig, "shadow_sweep")


def chart_kelly_heat() -> None:
    risk = read_json("risk_metrics")
    sens = risk["kelly_sensitivity"]
    ps = sorted({s["p"] for s in sens})
    bs = sorted({s["b"] for s in sens})
    grid = np.zeros((len(ps), len(bs)))
    for s in sens:
        i = ps.index(s["p"])
        j = bs.index(s["b"])
        grid[i, j] = max(s["f_star"], 0.0) * 100
    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    im = ax.imshow(grid, aspect="auto", cmap="Blues", origin="lower")
    ax.set_xticks(range(len(bs)))
    ax.set_xticklabels([f"{b:g}" for b in bs])
    ax.set_yticks(range(len(ps)))
    ax.set_yticklabels([f"{p*100:.0f}%" for p in ps])
    ax.set_xlabel("盈亏比 b")
    ax.set_ylabel("胜率 p")
    ax.set_title("二项 Kelly f*（%）敏感性")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_chart(fig, "kelly_sensitivity")


def chart_ue_scenarios() -> None:
    ue = read_json("unit_economics")
    labels = []
    profits = []
    orders = []
    for key in ("pessimistic", "base", "optimistic"):
        sc = ue["scenarios"][key]
        labels.append(sc["label"])
        profits.append(sc["annual_profit_usd"])
        orders.append(sc["orders_per_year"])
    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w / 2, orders, w, label="年订单", color=PALETTE["blue"])
    ax2 = ax.twinx()
    ax2.bar(x + w / 2, profits, w, label="年利润 USD", color=PALETTE["orange"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("年订单数")
    ax2.set_ylabel("年利润（USD）")
    ax.set_title("单位经济三情景（确定性切片）")
    save_chart(fig, "ue_scenarios")


def main() -> None:
    chart_scoring()
    chart_outcome_bands()
    chart_shadow_sweep()
    chart_kelly_heat()
    chart_ue_scenarios()
    print(f"charts written to {OUTPUT_DIR / 'charts'}")


if __name__ == "__main__":
    main()
