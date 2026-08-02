"""自下而上单位经济（一次性证据包 + 可选年订）。"""

from __future__ import annotations

from common import load_yaml

WEEKS_PER_MONTH = 52.0 / 12.0
MONTHS = 12


def _finite(x: float, cap: float = 1e9) -> float:
    if x != x or x == float("inf") or x == float("-inf"):
        return cap
    return float(min(max(x, -cap), cap))


def scenario(cfg: dict, name: str, sc: dict) -> dict:
    price = float(cfg["pricing"]["one_time_usd"])
    annual_usd = float(cfg["pricing"]["annual_plan_usd"])
    attach = float(sc["annual_attach"])
    # 每付费用户期望收入（首年）：一次费 + 附青年订摊销
    revenue_per_buyer = price + attach * annual_usd

    costs = cfg["costs"]
    var = (
        price * float(costs["stripe_percent"])
        + float(costs["stripe_fixed_usd"])
        + float(costs["llm_usd_per_order"])
        + float(costs["storage_usd_per_order"])
        + float(costs["email_usd_per_order"])
        + attach * (annual_usd * float(costs["stripe_percent"]) + float(costs["stripe_fixed_usd"]))
    )
    contribution = revenue_per_buyer - var
    cm = contribution / revenue_per_buyer if revenue_per_buyer else 0.0

    visitors = float(sc["monthly_visitors"])
    v2p = float(sc["visitor_to_paid"])
    orders_month = visitors * v2p
    orders_year = orders_month * MONTHS

    fixed = float(costs["fixed_monthly_usd"])
    monthly_profit = orders_month * contribution - fixed
    annual_profit = monthly_profit * MONTHS

    ops = cfg["operating"]
    hours_month = float(ops["hours_per_week"]) * WEEKS_PER_MONTH
    maint_cap = hours_month * float(ops["maintenance_cap_share"])
    maint_per = float(ops["maintenance_hours_per_order"])
    max_orders_month = (
        (maint_cap - float(ops["maintenance_hours_base"])) / maint_per
        if maint_per > 0
        else float("inf")
    )
    max_orders_month = max(0.0, max_orders_month)

    shadow = float(cfg["opportunity_cost"]["shadow_hourly_usd"])
    # 内容获客：1 小时 → units × seo 访问年金
    funnel = cfg["funnel"]
    units = float(funnel["content_units_per_hour"])
    seo = float(sc.get("seo_mode", (funnel["seo_visitors_per_content_unit"]["mode"])))
    decay = float(funnel["content_monthly_decay"])
    horizon = int(cfg["simulation"]["months"])
    annuity = (1.0 - (1.0 - decay) ** horizon) / decay if decay > 0 else float(horizon)
    visitors_per_hour_life = units * seo * annuity
    buyers_per_hour = visitors_per_hour_life * v2p
    hours_per_buyer = 1.0 / buyers_per_hour if buyers_per_hour > 0 else float("inf")
    cac_time = hours_per_buyer * shadow
    ltv = contribution  # 一次性为主；年订已计入首年收入
    ltv_cac = ltv / cac_time if cac_time > 0 and cac_time < 1e8 else float("inf")

    cash = float(cfg["capital"]["risk_capital_usd"])
    runway_months = cash / fixed if fixed > 0 else float("inf")

    sg_acc = float(cfg["market"]["sg_fatal_injury_accidents_2024"])
    penetration = orders_year / sg_acc if sg_acc else None

    return {
        "name": name,
        "label": sc["label"],
        "price_one_time_usd": price,
        "revenue_per_buyer_usd": revenue_per_buyer,
        "variable_cost_per_buyer_usd": var,
        "contribution_usd": contribution,
        "contribution_margin": cm,
        "monthly_visitors": visitors,
        "visitor_to_paid": v2p,
        "orders_per_month": orders_month,
        "orders_per_year": orders_year,
        "monthly_profit_usd": monthly_profit,
        "annual_profit_usd": annual_profit,
        "capacity_orders_per_month": _finite(max_orders_month),
        "capacity_binding": orders_month > max_orders_month,
        "hours_per_buyer": _finite(hours_per_buyer),
        "cac_time_usd": _finite(cac_time),
        "ltv_usd": ltv,
        "ltv_cac_time": _finite(ltv_cac, 1e6),
        "runway_months_zero_revenue": _finite(runway_months),
        "implied_penetration_vs_spf_accidents": penetration,
        "fixed_monthly_usd": fixed,
        "shadow_hourly_usd": shadow,
        "notes_zh": (
            "渗透率对照 SPF 致命+受伤事故池；财产损失事故未计入分母，故渗透率为上偏估计。"
            if penetration is not None
            else ""
        ),
    }


def main() -> dict:
    cfg = load_yaml("assumptions.yaml")
    # 为三情景补 seo mode
    seo_mode = float(cfg["funnel"]["seo_visitors_per_content_unit"]["mode"])
    out_sc = {}
    for key, sc in cfg["scenarios"].items():
        sc = {**sc, "seo_mode": seo_mode}
        out_sc[key] = scenario(cfg, key, sc)

    base = out_sc["base"]
    return {
        "product": "AfterCrash SG Evidence Pack",
        "model": "one_time_plus_optional_annual",
        "spf_fatal_injury_accidents_2024": cfg["market"]["sg_fatal_injury_accidents_2024"],
        "scenarios": out_sc,
        "constraints": {
            "risk_capital_usd": cfg["capital"]["risk_capital_usd"],
            "hours_per_week": cfg["operating"]["hours_per_week"],
            "monthly_burn_cap_usd": cfg["capital"]["monthly_burn_cap_usd"],
        },
        "headline": {
            "base_orders_year": base["orders_per_year"],
            "base_annual_profit_usd": base["annual_profit_usd"],
            "base_contribution_margin": base["contribution_margin"],
            "base_ltv_cac_time": base["ltv_cac_time"],
            "base_penetration": base["implied_penetration_vs_spf_accidents"],
            "capacity_orders_month": base["capacity_orders_per_month"],
        },
        "disclaimer_zh": (
            "访客量与转化率为待测量三角分布中枢的确定性切片，不是承诺；"
            "结论以蒙特卡洛分布为准。"
        ),
    }


if __name__ == "__main__":
    from common import write_json
    write_json("unit_economics", main())
    print("wrote outputs/unit_economics.json")
