"""复盘并复算 need.txt 原稿自报指标（与源文件字面绑定）。"""

from __future__ import annotations

from common import ROOT, cagr, kelly_binary, mult, num, pct, usd

# 原稿归档：rewritten need.txt 指向报告后，审计仍绑定原始种子文本
NEED = ROOT / "data" / "need_original.txt"

LITERALS = {
    "annualised_90": "年化约90%",
    "win_rate": "约10%-15%",
    "payoff_ratio": "约7:1",
    "risk_adj": "约20%",
    "moic": "约1.5x",
    "roi_ladder_large": "种子轮第1-5年账面ROI分别为120%、240%、360%、480%、600%",
    "roi_y5_small": "第5年 6%",
    "tam": "潜在市场规模约20亿美元",
    "accidents_2m": "每年约有200万起交通事故",
    "som_users": "目标客户为10万车主与20家保险公司",
    "y1_rev_table": "$500,000",
    "assumptions": "假设CAC为$20，转化率10%，ARPU为$250，毛利率70%",
    "seed": "假设种子轮投资金额为$500,000",
    "verify_script": "scripts/verify_bp_math.py",
    "errata": "【复算校准】",
}

CLAIMED = {
    "annualised_book": 0.90,
    "win_rate_low": 0.10,
    "win_rate_high": 0.15,
    "win_rate_mid": 0.125,
    "payoff_ratio": 7.0,
    "moic": 1.5,
    "risk_adjusted_annualised": 0.20,
    "roi5_large": 6.00,   # 600%
    "roi5_small": 0.06,   # 6%
    "seed_usd": 500_000.0,
    "y1_revenue_table_usd": 500_000.0,
    "som_text_usd": 5_000_000.0,  # 「首年收入约500万美元」
    "cac_usd": 20.0,
    "conversion_rate": 0.10,
    "arpu_usd": 250.0,
    "gross_margin": 0.70,
    "y1_users": 100_000.0,
    "sg_accidents_official": 7192.0,
}

YEARS = 5.0


def verify_source_bindings() -> dict:
    text = NEED.read_text(encoding="utf-8")
    results = {}
    missing = []
    for key, literal in LITERALS.items():
        found = literal in text
        results[key] = {"literal": literal, "found": found}
        if not found:
            missing.append(literal)
    if missing:
        raise AssertionError(
            "need.txt 中未找到以下被审计的原文片段，源文件可能已变更：\n  - "
            + "\n  - ".join(missing)
        )
    return results


def finding(fid, title, claimed, recomputed, verdict, formula, note) -> dict:
    return {
        "id": fid,
        "title": title,
        "claimed": claimed,
        "recomputed": recomputed,
        "verdict": verdict,
        "formula": formula,
        "note": note,
    }


def main() -> dict:
    bindings = verify_source_bindings()
    c = CLAIMED
    findings: list[dict] = []

    ratio = c["roi5_large"] / c["roi5_small"]
    findings.append(finding(
        "F1",
        "同一文件对第5年账面 ROI 给出两套相差 100 倍的数字",
        "执行摘要：ROI 阶梯至 600%；文末指标区：第5年 6%",
        f"两处第5年数值之比 = {num(ratio, 0)} 倍",
        "矛盾",
        "600% ÷ 6% = 100",
        "两套数字不可能同时为真。后续年化/MOIC/风险调整年化建立在未定义输入上。",
    ))

    ann_large = cagr(1 + c["roi5_large"], YEARS)
    ann_small = cagr(1 + c["roi5_small"], YEARS)
    implied_m_90 = (1 + c["annualised_book"]) ** YEARS
    findings.append(finding(
        "F2",
        "自报账面年化 90% 与两套 ROI 阶梯均不相容",
        f"年化（账面）{pct(c['annualised_book'], 0)}",
        f"若 ROI5=600%（期末 7.00x）→ 年化 {pct(ann_large)}；"
        f"若 ROI5=6%（期末 1.06x）→ 年化 {pct(ann_small)}",
        "矛盾",
        "年化 = M^(1/5) - 1；反解 M = 1.90^5",
        f"支撑 90% 年化需要期末倍数 {mult(implied_m_90)}，原文未给出该量级。",
    ))

    findings.append(finding(
        "F3",
        "SOM 文字『首年约500万美元』与财务表 Y1 $500,000 相差 10 倍",
        f"SOM 叙述约 {usd(c['som_text_usd'])}；财务表 Y1 {usd(c['y1_revenue_table_usd'])}",
        f"比值 = {num(c['som_text_usd'] / c['y1_revenue_table_usd'], 0)} 倍",
        "矛盾",
        "同一『首年收入』不得有两套量纲",
        "量纲错误使下游 EBITDA 与回报叙述失去锚点。",
    ))

    implied_rev = c["y1_users"] * c["arpu_usd"]
    findings.append(finding(
        "F4",
        "『10万车主 × ARPU $250』与财务表/SPF 事故量级均不相容",
        f"10万车主、ARPU $250 → 隐含营收 {usd(implied_rev)}；表内 Y1 {usd(c['y1_revenue_table_usd'])}",
        f"SPF 2024 致命+受伤事故仅约 {num(c['sg_accidents_official'], 0)} 起；"
        f"10万付费车主意味着渗透远超官方伤亡事故池",
        "不可行",
        "Revenue ≈ Users × ARPU；SOM ⊆ 官方事故量级",
        "即使用财产损失事故放大，原稿也未给出可核对来源。",
    ))

    p = c["win_rate_mid"]
    b = c["payoff_ratio"]
    # 亏损归零：赢时 M=1.06（若用小 ROI），输时 0 → EV = p*M
    m_small = 1 + c["roi5_small"]
    ev_zero = p * m_small
    ev_breakeven = p * m_small + (1 - p) * 1.0
    ra_zero = cagr(ev_zero, YEARS)
    ra_be = cagr(ev_breakeven, YEARS)
    findings.append(finding(
        "F5",
        "自报 MOIC 1.5x / 风险调整年化 20% 与胜率及 ROI5=6% 复算不符",
        f"MOIC {mult(c['moic'])}；风险调整年化 {pct(c['risk_adjusted_annualised'], 0)}；胜率中值 {pct(p)}",
        f"EV∈[{mult(ev_zero)}, {mult(ev_breakeven)}]；"
        f"风险调整年化∈[{pct(ra_zero)}, {pct(ra_be)}]",
        "矛盾",
        "EV=[p·M, p·M+(1-p)]；风险调整年化=EV^(1/5)-1",
        "原文末尾【复算校准】已部分指出；本审计确认应以复算口径为准。",
    ))

    f_kelly = kelly_binary(p, b)
    findings.append(finding(
        "F6",
        "若直接采用自报胜率与盈亏比，Kelly 全仓含义需单独审视",
        f"p={pct(p)}，b={b:.0f}:1",
        f"二项 Kelly f* = (bp−q)/b = {pct(f_kelly)}；"
        f"对 100 万资金池全 Kelly 约 {usd(1_000_000 * f_kelly / 7.14)} 量级需按币种换算",
        "口径提示",
        "f* = (b·p − q)/b",
        "自报 b=7 与内部财务矛盾并存时，Kelly 数字会放大错误前提；重建报告改用蒙特卡洛分布。",
    ))

    findings.append(finding(
        "F7",
        "『AI 法律责任认定』零人工收费模式触达新加坡法律执业红线",
        "选定机会为责任认定法律支持 SaaS，NLP 生成法律建议",
        "Legal Profession Act s32/s33：无执业证不得执业；有偿 PI 和解尤其危险",
        "不可行",
        "合规闸门优先于商业想象",
        "重建方向改为证据包/FNOL 清单等信息不具法律意见属性的工具。",
    ))

    # 规范复算块（对应原稿 verify_bp_math 口径）
    math_block = {
        "roi5_pct_used": c["roi5_small"] * 100,
        "M": m_small,
        "book_annualised": ann_small,
        "win_rate_mid": p,
        "ev_loss_to_zero": ev_zero,
        "ev_loss_to_breakeven": ev_breakeven,
        "risk_adj_annualised_zero": ra_zero,
        "risk_adj_annualised_breakeven": ra_be,
        "self_annualised": c["annualised_book"],
        "self_moic": c["moic"],
        "self_risk_adj": c["risk_adjusted_annualised"],
        "kelly_binary_on_self_reported": f_kelly,
    }

    summary = {
        "n_findings": len(findings),
        "n_contradictions": sum(1 for f in findings if f["verdict"] == "矛盾"),
        "n_infeasible": sum(1 for f in findings if f["verdict"] == "不可行"),
        "verdict_zh": "原稿不可作为可执行 BP；须合规重定位并自下而上重算。",
        "recommended_roi5_for_errata": c["roi5_small"],
        "recommended_book_annualised": ann_small,
    }

    return {
        "bindings": bindings,
        "claimed": c,
        "findings": findings,
        "math_block": math_block,
        "summary": summary,
        "narrative_zh": (
            "对 need.txt 的七项审计显示：ROI 阶梯自相矛盾、年化 90% 无支撑、"
            "营收量纲冲突、SOM 超越 SPF 事故池、回报指标与复算不符，"
            "且主叙事触达法律执业红线。重建必须更换产品边界并重算。"
        ),
    }


if __name__ == "__main__":
    from common import write_json
    write_json("audit_original", main())
    print("wrote outputs/audit_original.json")
