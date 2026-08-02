"""由评分胜出者 + 假设集推导可执行精益 BP 量化段落。"""

from __future__ import annotations

from common import load_yaml, read_json


def main() -> dict:
    bp = load_yaml("bp.yaml")
    scoring = read_json("scoring")
    ue = read_json("unit_economics")
    risk = read_json("risk_metrics")
    cfg = load_yaml("assumptions.yaml")

    winner = scoring["winner"]
    if winner["id"] != bp["meta"].get("winner_id_expected"):
        # 不失败：以评分为准，标注预期不一致
        note = (
            f"评分胜出为 {winner['id']}，与 bp.yaml 预期 "
            f"{bp['meta'].get('winner_id_expected')} 不同；以下叙述绑定实际胜出者。"
        )
    else:
        note = "评分胜出与预期定位一致。"

    base = ue["scenarios"]["base"]
    primary = risk["primary"]
    kelly = risk["kelly_1m_cny"]

    go = (
        primary["win_rate"] >= 0.08
        and (primary["payoff_ratio"] or 0) >= 1.0
        and primary["kelly_fraction_numeric"] > 0
    )

    return {
        "winner_id": winner["id"],
        "winner_name": winner["name"],
        "winner_score": winner["total"],
        "alignment_note_zh": note,
        "positioning": bp["positioning"],
        "zero_human_stack": bp["zero_human_stack"],
        "milestones_90d": bp["milestones_90d"],
        "kill_criteria": bp["kill_criteria"],
        "goodwill": bp["goodwill"],
        "economics_snapshot": {
            "price_one_time_usd": base["price_one_time_usd"],
            "base_orders_year": base["orders_per_year"],
            "base_annual_profit_usd": base["annual_profit_usd"],
            "contribution_margin": base["contribution_margin"],
            "risk_capital_usd": cfg["capital"]["risk_capital_usd"],
            "hours_per_week": cfg["operating"]["hours_per_week"],
        },
        "risk_snapshot": {
            "win_rate": primary["win_rate"],
            "payoff_ratio": primary["payoff_ratio"],
            "aggregate_moic": primary["aggregate_moic"],
            "risk_adj_annualised_probweighted": primary["risk_adj_annualised_probweighted"],
            "risk_adj_annualised_ev_zero": primary["risk_adj_annualised_ev_zero"],
            "risk_adj_annualised_ev_breakeven": primary["risk_adj_annualised_ev_breakeven"],
            "kelly_full_cny": kelly["full_kelly_cny"],
            "kelly_half_cny": kelly["half_kelly_cny"],
            "kelly_quarter_cny": kelly["quarter_kelly_cny"],
            "f_star": kelly["f_star_numeric"],
        },
        "go_no_go": {
            "recommend_phase0": True,
            "recommend_full_build": bool(go),
            "recommend_zh": (
                "建议启动 Phase0（约 20 小时）做合规文案与原型验证；"
                + (
                    "量化指标支持进入 Phase1 MVP，但仍以实测转化替换待测量参数。"
                    if go
                    else "主口径胜率/盈亏比偏弱，Phase0 后若漏斗无改善应停损，勿加码到 100 万。"
                )
            ),
        },
        "not_to_do": bp["positioning"]["not_promise"],
    }


if __name__ == "__main__":
    from common import write_json
    write_json("bp_plan", main())
    print("wrote outputs/bp_plan.json")
