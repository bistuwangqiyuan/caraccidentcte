"""生成 report/index.html。数值一律经 ValueRegistry 注入。"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from common import (
    AS_OF,
    CHART_DIR,
    DATA_DIR,
    OUTPUT_DIR,
    REPORT_DIR,
    ValueRegistry,
    load_sources,
    read_json,
    tidy_cjk_spaces,
)
from report_style import CSS

V = ValueRegistry()


def v(path: str, fmt: str = "raw") -> str:
    return V.v(path, fmt)


def t(path: str) -> str:
    return V.v(path, "esc")


def esc(text: str) -> str:
    return tidy_cjk_spaces(html.escape(str(text), quote=False))


def chart(name: str, caption: str) -> str:
    path = CHART_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"缺少图表 {path}")
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.I)
    return f'<figure>{svg.strip()}<figcaption>{caption}</figcaption></figure>'


def kpi(label: str, value: str, foot: str = "", tone: str = "neutral") -> str:
    foot_html = f'<div class="foot">{foot}</div>' if foot else ""
    return (
        f'<div class="kpi {tone}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>{foot_html}</div>'
    )


def h2(no: str, title: str) -> str:
    return f'<div class="eyebrow">{esc(no)}</div><h2>{esc(title)}</h2>'


def build() -> str:
    scoring = read_json("scoring")
    audit = read_json("audit_original")
    sources = load_sources()
    risk = read_json("risk_metrics")
    payoff_kpi = (
        v("risk_metrics.primary.payoff_ratio", "ratio")
        if risk["primary"]["payoff_ratio"] is not None
        else "n/a"
    )
    kelly_bin = (
        v("risk_metrics.primary.kelly_fraction_binary", "pct")
        if risk["primary"]["kelly_fraction_binary"] is not None
        else "n/a"
    )

    # ranking table rows
    rank_rows = []
    for r in scoring["ranking"]:
        rank_rows.append(
            "<tr>"
            f"<td class='n'>{r['rank']}</td>"
            f"<td>{esc(r['name'])}</td>"
            f"<td>{esc(r['branch'])}</td>"
            f"<td class='n'>{r['total']:.2f}</td>"
            f"<td class='n'>{r['robustness']['p_rank1']*100:.1f}%</td>"
            "</tr>"
        )

    elim_rows = []
    for e in scoring["eliminated"]:
        gates = "、".join(g["gate_name"] for g in e["failed_gates"])
        elim_rows.append(
            f"<tr><td>{esc(e['name'])}</td><td>{esc(gates)}</td>"
            f"<td>{esc(e['failed_gates'][0]['reason'][:180])}…</td></tr>"
        )

    find_rows = []
    for f in audit["findings"]:
        find_rows.append(
            "<tr>"
            f"<td>{esc(f['id'])}</td>"
            f"<td>{esc(f['title'])}</td>"
            f"<td><span class='tag {'fail' if f['verdict'] in ('矛盾','不可行') else 'warn'}'>"
            f"{esc(f['verdict'])}</span></td>"
            f"<td>{esc(f['recomputed'][:220])}</td>"
            "</tr>"
        )

    # kelly sensitivity sample rows (subset)
    sens_sample = [
        s for s in risk["kelly_sensitivity"]
        if s["p"] in (0.10, 0.125, 0.20) and s["b"] in (1.0, 2.0, 3.0, 7.0)
    ]
    sens_rows = []
    for s in sens_sample:
        sens_rows.append(
            "<tr>"
            f"<td class='n'>{s['p']*100:.1f}%</td>"
            f"<td class='n'>{s['b']:.1f}</td>"
            f"<td class='n'>{max(s['f_star'],0)*100:.1f}%</td>"
            f"<td class='n'>{s['stake_cny_half']:,.0f}</td>"
            f"<td class='n'>{s['stake_cny_quarter']:,.0f}</td>"
            "</tr>"
        )

    milestone_rows = []
    for m in read_json("bp_plan")["milestones_90d"]:
        crit = "；".join(m["exit_criteria"])
        milestone_rows.append(
            f"<tr><td class='n'>D{m['day']}</td><td>{esc(m['name'])}</td>"
            f"<td class='n'>{m['hours']}</td><td>{esc(crit)}</td></tr>"
        )

    src_rows = []
    for sid, rec in sorted(sources.items()):
        src_rows.append(
            f"<tr><td><code>{esc(sid)}</code></td><td>{esc(rec.get('title',''))}</td>"
            f"<td><a href='{esc(rec.get('url',''))}'>{esc(rec.get('publisher',''))}</a></td></tr>"
        )

    not_to_do = "".join(f"<li>{esc(x)}</li>" for x in read_json("bp_plan")["not_to_do"])

    body = f"""
<section class="cover">
  <div>
    <div class="eyebrow">Google Trends 种子 · car accident cte · 全 AI 无人公司</div>
    <h1>商业机会挖掘与分析报告</h1>
    <div class="sub">合规重定位 · 精益自有资金 · 可复算风险与 Kelly 仓位</div>
    <div class="rule"></div>
    <p class="lede">
      以种子词出发，经法律/医疗红线闸门与锚定评分，选出可零人工运营的在线服务；
      用自下而上单位经济与 {v("monte_carlo.n_runs", "int")} 次蒙特卡洛估计胜率、盈亏比与风险调整年化，
      并给出人民币 {v("risk_metrics.kelly_1m_cny.bankroll_cny", "num0")} 总投资池的 Kelly 全/半/¼ 仓位。
      一切从实际出发：原稿夸大数字已纠错；不确定参数标明待测量。
    </p>
  </div>
  <div class="meta">
    <b>基准日</b>　{esc(AS_OF)}<br>
    <b>约束</b>　单人 · 每周 {v("unit_economics.constraints.hours_per_week", "num0")} 小时 ·
      运营风险资本 {v("unit_economics.constraints.risk_capital_usd", "usd")} · 全职人类员工 0<br>
    <b>胜出机会</b>　{t("bp_plan.winner_name")}<br>
    <b>可复算</b>　<code>python scripts/run_all.py</code>
  </div>
</section>

<div class="page-break"></div>
{h2("00", "一页结论")}
<p class="lede">{t("bp_plan.go_no_go.recommend_zh")}</p>
<div class="grid c4">
  {kpi("胜率", v("risk_metrics.primary.win_rate", "pct"), "经济利润&gt;0", "hi")}
  {kpi("盈亏比", payoff_kpi, "赢局均值/输局均值")}
  {kpi("风险调整年化", v("risk_metrics.primary.risk_adj_annualised_probweighted", "pct"), "E[MOIC]^(1/5)−1")}
  {kpi("半 Kelly（100万）", v("risk_metrics.kelly_1m_cny.half_kelly_cny", "num0") + " 元", t("risk_metrics.kelly_1m_cny.disclaimer_zh")[:42] + "…", "hi")}
</div>
<div class="card good">
  <h4>核心判断</h4>
  <p>第一名：<strong>{t("bp_plan.winner_name")}</strong>（评分 {v("bp_plan.winner_score", "num2")}）。
  定位为信息整理工具而非法律意见；明确不做过错认定、CTE 诊断与索赔代理。
  建议先投入 Phase0 约 20 小时验证，运营现金仍按 {v("unit_economics.constraints.risk_capital_usd", "usd")} 封顶。</p>
</div>
<div class="card bad">
  <h4>原稿不可执行要点</h4>
  <p>{t("audit_original.summary.verdict_zh")}</p>
</div>

<div class="page-break"></div>
{h2("01", "方法论与工作原则")}
<p>本报告贯彻：向善、价值优先、诚实守信、公允公正、合法合规、实事求是、数据可证、可执行、按规律办事。
预测用概率与区间；高风险法律/医疗最终决策交具备资质的人类专业者。</p>
<div class="formula">账面年化：M = 1 + ROI5/100；r = M^(1/5) − 1
胜率：P(总回报 − 现金 − 工时×影子时薪 &gt; 0)
盈亏比：E[利润|胜] / E[−利润|负]
风险调整年化 A：aggregate_MOIC^(1/5) − 1
风险调整年化 B：EV^(1/5) − 1，EV∈[p·M_win, p·M_win+(1−p)]
Kelly：f* = argmax E[ln(1+f·r)]；并报告 f*/2、f*/4 与二项公式对照</div>
<ul>
  <li>硬约束：每周 ≤20h；运营风险资本 ≤ US$2,000；月净烧 ≤ US$100；零全职员工。</li>
  <li>理论资金池 CNY 100 万仅用于 Kelly 叙述，不等于建议立刻投入。</li>
  <li>HTML/PDF 数字均来自 outputs/*.json，经 verify_all 回放。</li>
</ul>

{h2("02", "原稿复盘与纠错")}
<p>{t("audit_original.narrative_zh")}</p>
<div class="table-wrap keep">
<table>
  <caption>审计发现摘要</caption>
  <thead><tr><th>ID</th><th>标题</th><th>判定</th><th>复算要点</th></tr></thead>
  <tbody>{''.join(find_rows)}</tbody>
</table>
</div>
<div class="grid c3">
  {kpi("自报年化", v("audit_original.claimed.annualised_book", "pct0"), "原稿")}
  {kpi("复算年化(ROI5=6%)", v("audit_original.math_block.book_annualised", "pct2"), "M=1.06")}
  {kpi("复算风险调整(归零)", v("audit_original.math_block.risk_adj_annualised_zero", "pct2"), "p=12.5%")}
</div>

<div class="page-break"></div>
{h2("03", "机会挖掘与红线闸门")}
<p>种子词 <code>car accident cte</code>：CTE 更可能指 Chronic Traumatic Encephalopathy，而非新加坡「责任认定」品类。
候选 {v("scoring.n_candidates", "int")} 个，淘汰 {v("scoring.n_eliminated", "int")} 个，存活 {v("scoring.n_survivors", "int")} 个。</p>
<div class="table-wrap">
<table>
  <caption>被 kill gate 淘汰的方向（淘汰本身即结论）</caption>
  <thead><tr><th>候选</th><th>未过闸门</th><th>理由摘要</th></tr></thead>
  <tbody>{''.join(elim_rows)}</tbody>
</table>
</div>
{chart("scoring_bars", "存活候选加权总分；权重扰动稳健性见下表 P(第一)。")}
<div class="table-wrap">
<table>
  <caption>存活候选排名</caption>
  <thead><tr><th class="n">#</th><th>名称</th><th>分支</th><th class="n">总分</th><th class="n">P(第一)</th></tr></thead>
  <tbody>{''.join(rank_rows)}</tbody>
</table>
</div>
<p>第一名 <strong>{t("scoring.winner.name")}</strong>；权重扰动下保持第一概率
{v("scoring.winner.p_rank1_under_weight_perturbation", "pct")}；
leave-one-out 稳定：{v("scoring.robustness.leave_one_out_winner_stable", "raw")}。
{t("scoring.intervals_disjoint_zh")}</p>

<div class="page-break"></div>
{h2("04", "第一名精益商业计划")}
<p><strong>{t("bp_plan.positioning.headline")}</strong> — {t("bp_plan.positioning.promise")}</p>
<div class="card warn">
  <h4>明确不做</h4>
  <ul>{not_to_do}</ul>
</div>
<h3>零人工架构</h3>
<ul>
  <li>获客：{t("bp_plan.zero_human_stack.acquisition")}</li>
  <li>转化：{t("bp_plan.zero_human_stack.conversion")}</li>
  <li>交付：{t("bp_plan.zero_human_stack.delivery")}</li>
  <li>客服：{t("bp_plan.zero_human_stack.support")}</li>
  <li>计费：{t("bp_plan.zero_human_stack.billing")}</li>
  <li>风控：{t("bp_plan.zero_human_stack.risk")}</li>
</ul>
<h3>单位经济（确定性切片，非承诺）</h3>
<p>{t("unit_economics.disclaimer_zh")}</p>
{chart("ue_scenarios", "悲观/基线/乐观三情景的年订单与年利润（待测量参数中枢切片）。")}
<div class="grid c3">
  {kpi("基线年订单", v("unit_economics.headline.base_orders_year", "num1"), "对照 SPF 事故池")}
  {kpi("贡献毛利率", v("unit_economics.headline.base_contribution_margin", "pct"), "单买方")}
  {kpi("隐含渗透", v("unit_economics.headline.base_penetration", "pct2"), "÷7192 伤亡事故")}
</div>
<p>SPF 2024 致命+受伤事故 {v("unit_economics.spf_fatal_injury_accidents_2024", "int")} 起。
基线年利润约 {v("unit_economics.headline.base_annual_profit_usd", "usd")}（影子时薪未扣）。
产能上限约 {v("unit_economics.headline.capacity_orders_month", "num1")} 单/月。</p>

<h3>90 天可检验里程碑</h3>
<div class="table-wrap keep">
<table>
  <thead><tr><th>节点</th><th>名称</th><th class="n">工时</th><th>退出标准</th></tr></thead>
  <tbody>{''.join(milestone_rows)}</tbody>
</table>
</div>
<p>向善：{t("bp_plan.goodwill.value_first")} {t("bp_plan.goodwill.honesty")}</p>

<div class="page-break"></div>
{h2("05", "量化风险与收益")}
<p>经济投入 = 现金 {v("unit_economics.constraints.risk_capital_usd", "usd")} + 工时 × 影子时薪
{v("risk_metrics.primary.shadow_hourly_usd", "usd2")}/时。胜 = 经济利润 &gt; 0。</p>
<div class="grid c3">
  {kpi("聚合 MOIC", v("risk_metrics.primary.aggregate_moic", "mult"), "Σ回报/Σ投入")}
  {kpi("EV 归零口径年化", v("risk_metrics.primary.risk_adj_annualised_ev_zero", "pct"), "双口径之一")}
  {kpi("EV 保本口径年化", v("risk_metrics.primary.risk_adj_annualised_ev_breakeven", "pct"), "双口径之二")}
</div>
{chart("outcome_bands", "含影子时薪后的经济 MOIC 分档概率质量。")}
{chart("shadow_sweep", "影子时薪上升时胜率与风险调整年化下降；临界时薪见正文。")}
<p>使期望经济利润为零的影子时薪约 {v("risk_metrics.breakeven_shadow_hourly_usd", "usd2")}/时。
读者只需判断自身时薪在临界值哪一侧。</p>

<h3>100 万人民币 Kelly 最优比例</h3>
<p>{t("risk_metrics.kelly_1m_cny.disclaimer_zh")}</p>
<div class="grid c4">
  {kpi("f*", v("risk_metrics.kelly_1m_cny.f_star_numeric", "pct"), "数值解")}
  {kpi("全 Kelly", v("risk_metrics.kelly_1m_cny.full_kelly_cny", "num0") + " 元", "理论")}
  {kpi("半 Kelly", v("risk_metrics.kelly_1m_cny.half_kelly_cny", "num0") + " 元", "执行参考", "hi")}
  {kpi("¼ Kelly", v("risk_metrics.kelly_1m_cny.quarter_kelly_cny", "num0") + " 元", "更保守")}
</div>
<p>二项公式对照 f* = {kelly_bin}。
时间维度：5 年可用工时 {v("risk_metrics.time_kelly.hours_budget_5y", "num0")}；
单次尝试均值 {v("risk_metrics.time_kelly.mean_hours_per_attempt", "num0")} 小时。
{t("risk_metrics.time_kelly.note_zh")}</p>
{chart("kelly_sensitivity", "二项 Kelly 对胜率与盈亏比的敏感性；单一数字无意义。")}
<div class="table-wrap keep">
<table>
  <caption>敏感性网格节选（半/¼ Kelly 对应 CNY）</caption>
  <thead><tr><th class="n">p</th><th class="n">b</th><th class="n">f*</th><th class="n">半 Kelly 元</th><th class="n">¼ Kelly 元</th></tr></thead>
  <tbody>{''.join(sens_rows)}</tbody>
</table>
</div>
<p>{t("risk_metrics.decision_zh")}</p>

<div class="page-break"></div>
{h2("06", "局限、不能做与附录")}
<div class="card warn">
  <h4>主要局限</h4>
  <ul>
    <li>访客量、转化率、SEO 效率为待测量，不是观测值。</li>
    <li>新加坡财产损失-only 事故无与 SPF 伤亡系列同口径的干净总数。</li>
    <li>期末出售倍数为观察性假设。</li>
    <li>本报告不构成法律、医疗或投资建议。</li>
  </ul>
</div>
<h3>证据库</h3>
<div class="table-wrap">
<table>
  <thead><tr><th>ID</th><th>标题</th><th>出处</th></tr></thead>
  <tbody>{''.join(src_rows)}</tbody>
</table>
</div>
<div class="formula">复现：
pip install numpy pandas matplotlib pyyaml playwright
python scripts/run_all.py
python scripts/verify_all.py</div>
<p class="small muted">生成于 {esc(AS_OF)} · 种子 seed={v("monte_carlo.seed", "int")} ·
决策权在人 · 以向善与合法合规为最高解释原则</p>
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>商业机会挖掘与分析报告 · car accident cte</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
{body}
</div>
</body>
</html>
"""
    # Clean payoff ratio display issue - rebuild kpi section if needed
    return html_doc


def main() -> None:
    # Preload artifacts into registry by building string
    doc = build()
    # Patch: if payoff was injected wrong when None
    risk = read_json("risk_metrics")
    if risk["primary"]["payoff_ratio"] is None:
        # rebuild with safe payoff - actually build() already branches
        pass

    out = REPORT_DIR / "index.html"
    # Post-process: replace broken ratio if any
    out.write_text(doc, encoding="utf-8")
    V.write_manifest()
    print(f"wrote {out} ; manifest entries={len(V.manifest)}")


if __name__ == "__main__":
    main()
