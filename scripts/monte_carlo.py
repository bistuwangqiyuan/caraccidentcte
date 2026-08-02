"""单人微型工具站月度蒙特卡洛（一次性证据包）。

不标定成功率；参数自三角/对数正态抽样，结果涌现。
"""

from __future__ import annotations

import numpy as np

from common import OUTPUT_DIR, SEED, load_yaml

WEEKS_PER_MONTH = 52.0 / 12.0


def draw_tri(rng, spec, n):
    return rng.triangular(spec["low"], spec["mode"], spec["high"], size=n)


def simulate(cfg: dict, n_runs: int, months: int, rng: np.random.Generator) -> dict:
    funnel = cfg["funnel"]
    ops = cfg["operating"]
    costs = cfg["costs"]
    pricing = cfg["pricing"]
    beh = cfg["behaviour"]
    exitc = cfg["exit"]
    cap = cfg["capital"]

    v2p = draw_tri(rng, funnel["visitor_to_paid"], n_runs)
    seo = draw_tri(rng, funnel["seo_visitors_per_content_unit"], n_runs)
    base_visitors = draw_tri(rng, funnel["monthly_organic_visitors"], n_runs)
    attach = rng.uniform(0.04, 0.22, size=n_runs)
    exit_mult = draw_tri(rng, exitc["multiple_of_annual_profit"], n_runs)

    price = float(pricing["one_time_usd"])
    annual_price = float(pricing["annual_plan_usd"])
    stripe_pct = float(costs["stripe_percent"])
    stripe_fix = float(costs["stripe_fixed_usd"])
    llm = float(costs["llm_usd_per_order"])
    storage = float(costs["storage_usd_per_order"])
    email = float(costs["email_usd_per_order"])
    fixed = float(costs["fixed_monthly_usd"])

    hours_month = float(ops["hours_per_week"]) * WEEKS_PER_MONTH
    build_hours = float(ops["mvp_build_hours"])
    maint_base = float(ops["maintenance_hours_base"])
    maint_per = float(ops["maintenance_hours_per_order"])
    maint_cap_share = float(ops["maintenance_cap_share"])
    units_per_hour = float(funnel["content_units_per_hour"])
    decay = float(funnel["content_monthly_decay"])
    niche_cap = float(funnel["content_niche_capacity"])
    content_share = float(funnel["content_share_of_growth_hours"])
    abandon_n = int(beh["abandon_zero_revenue_months"])
    life_hz = float(beh["life_event_monthly_hazard"])

    cash0 = float(cap["risk_capital_usd"])

    # 状态
    cash = np.full(n_runs, cash0)
    content_stock = np.zeros(n_runs)
    hours_total = np.zeros(n_runs)
    revenue_total = np.zeros(n_runs)
    orders_total = np.zeros(n_runs)
    months_active = np.zeros(n_runs, dtype=int)
    zero_streak = np.zeros(n_runs, dtype=int)
    alive = np.ones(n_runs, dtype=bool)
    built = np.zeros(n_runs, dtype=bool)
    build_left = np.full(n_runs, build_hours)
    monthly_profit_last12 = np.zeros((n_runs, 12))

    # 预抽生活事件
    life_event = rng.random((n_runs, months)) < life_hz

    for m in range(months):
        if not alive.any():
            break

        # 工时分配
        h = np.where(alive, hours_month, 0.0)
        hours_total += h

        # 先完成构建
        still_building = alive & (~built)
        invest_build = np.minimum(build_left, h)
        build_left = np.where(still_building, build_left - invest_build, build_left)
        h_left = h - np.where(still_building, invest_build, 0.0)
        newly = still_building & (build_left <= 1e-9)
        built |= newly

        # 维护（与上月订单规模相关：用指数平滑代理 —— 用累计订单/活跃月）
        avg_orders = np.where(months_active > 0, orders_total / np.maximum(months_active, 1), 0.0)
        maint_need = maint_base + maint_per * avg_orders
        maint_budget = hours_month * maint_cap_share
        overload = np.maximum(0.0, maint_need / np.maximum(maint_budget, 1e-9) - 1.0)
        maint_hours = np.minimum(h_left, np.minimum(maint_need, maint_budget))
        h_left = h_left - maint_hours

        # 增长：内容
        growth_hours = np.where(built & alive, h_left * content_share, 0.0)
        # 边际生产率随存量下降：(C/(C+S))^2
        marginal = (niche_cap / (niche_cap + content_stock + 1e-9)) ** 2
        new_units = growth_hours * units_per_hour * marginal
        content_stock = content_stock * (1.0 - decay) + new_units

        # 流量
        seo_visitors = content_stock * seo
        visitors = np.where(built & alive, base_visitors + seo_visitors, 0.0)
        # 过载降低转化
        eff_v2p = v2p / (1.0 + overload)
        orders = visitors * eff_v2p
        # 产能硬顶
        max_orders = np.maximum(0.0, (maint_budget - maint_base) / max(maint_per, 1e-9))
        orders = np.minimum(orders, max_orders)

        rev_per = price + attach * annual_price
        var_per = (
            price * stripe_pct + stripe_fix + llm + storage + email
            + attach * (annual_price * stripe_pct + stripe_fix)
        )
        revenue = orders * rev_per
        contribution = orders * (rev_per - var_per)
        profit = contribution - fixed

        cash = np.where(alive, cash + profit, cash)
        revenue_total = np.where(alive, revenue_total + revenue, revenue_total)
        orders_total = np.where(alive, orders_total + orders, orders_total)
        months_active = np.where(alive, months_active + 1, months_active)

        # 滚动 12 个月利润
        monthly_profit_last12[:, m % 12] = np.where(alive, profit, monthly_profit_last12[:, m % 12])

        zero_streak = np.where(alive & (revenue <= 1e-9), zero_streak + 1, 0)

        # 终止条件
        abandon = alive & built & (zero_streak >= abandon_n)
        bankrupt = alive & (cash < 0)
        life = alive & life_event[:, m]
        stop = abandon | bankrupt | life
        alive = alive & (~stop)

    # 期末残值：近 12 月利润和（若为负则 0）× 倍数
    recent_annual = monthly_profit_last12.sum(axis=1)
    recent_annual = np.maximum(recent_annual, 0.0)
    terminal = recent_annual * exit_mult
    # 仍存活才计残值
    # months_active==months 近似存活到期末
    survived = months_active >= months
    terminal = np.where(survived, terminal, terminal * 0.3)  # 中途退出仍可能有小残值
    total_return = np.maximum(cash, 0.0) + terminal
    # 现金可为正但已放弃：cash 已含累计利润

    # 若从未建成
    never_built = ~built
    total_return = np.where(never_built, np.maximum(cash, 0.0), total_return)

    np.savez_compressed(
        OUTPUT_DIR / "mc_raw.npz",
        total_return=total_return,
        hours_total=hours_total,
        orders_total=orders_total,
        revenue_total=revenue_total,
        months_active=months_active.astype(float),
        cash=cash,
        terminal=terminal,
        survived=survived.astype(float),
        v2p=v2p,
        final_mrr=recent_annual / 12.0,
    )

    def pctile(x, ps):
        return {f"p{int(p)}": float(np.percentile(x, p)) for p in ps}

    return {
        "n_runs": n_runs,
        "months": months,
        "seed": int(cfg["simulation"]["seed"]),
        "summary": {
            "mean_total_return_usd": float(total_return.mean()),
            "median_total_return_usd": float(np.median(total_return)),
            "mean_hours": float(hours_total.mean()),
            "mean_orders": float(orders_total.mean()),
            "mean_revenue_usd": float(revenue_total.mean()),
            "p_survive_to_end": float(survived.mean()),
            "p_never_built": float(never_built.mean()),
            "p_total_return_zero": float((total_return <= 1.0).mean()),
            **{f"total_return_{k}": v for k, v in pctile(total_return, [5, 25, 50, 75, 95]).items()},
            **{f"orders_{k}": v for k, v in pctile(orders_total, [50, 90]).items()},
        },
        "external_check_zh": (
            "本模型不标定到固定胜率。若涌现胜率显著高于公开独立开发者『多数产品收入接近零』"
            "的常识，应检查流量中枢是否过乐观——报告在风险章节给出影子时薪敏感性。"
        ),
    }


def main() -> dict:
    cfg = load_yaml("assumptions.yaml")
    n = int(cfg["simulation"]["n_runs"])
    months = int(cfg["simulation"]["months"])
    rng = np.random.default_rng(int(cfg["simulation"]["seed"]))
    return simulate(cfg, n, months, rng)


if __name__ == "__main__":
    from common import write_json
    write_json("monte_carlo", main())
    print("wrote outputs/monte_carlo.json and mc_raw.npz")
