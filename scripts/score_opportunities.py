"""机会评分引擎。

流程：
  1. 校验每个候选的打分完整性（含打分理由与证据引用），不合规直接报错——
     这保证报告里的分数不可能是"随手写的"。
  2. 先执行三道 kill gate；未通过者不进入排名，但保留在报告中并说明淘汰依据。
  3. 计算加权总分。
  4. 稳健性检验一：对权重做 ±30% 均匀扰动 20,000 次，统计每个候选成为第一名的频率。
  5. 稳健性检验二：逐一剔除单个维度（leave-one-out），检查第一名是否改变。
"""

from __future__ import annotations

import numpy as np

from common import SEED, load_rubric_candidates_guard, write_json


def _validate(rubric: dict, candidates: list[dict]) -> None:
    crit_ids = [c["id"] for c in rubric["criteria"]]
    total_w = sum(c["weight"] for c in rubric["criteria"])
    if total_w != rubric["meta"]["weight_total"]:
        raise AssertionError(f"权重之和为 {total_w}，应为 {rubric['meta']['weight_total']}")

    gate_ids = {g["id"] for g in rubric["kill_gates"]}
    for cand in candidates:
        name = cand.get("name", "<未命名>")
        missing = [c for c in crit_ids if c not in cand.get("scores", {})]
        if missing:
            raise AssertionError(f"候选『{name}』缺少维度打分：{missing}")
        for cid, entry in cand["scores"].items():
            if cid not in crit_ids:
                raise AssertionError(f"候选『{name}』出现未定义维度 {cid}")
            score = entry.get("score")
            if not isinstance(score, int) or not 1 <= score <= 10:
                raise AssertionError(f"候选『{name}』维度 {cid} 的分数 {score} 非 1-10 整数")
            if not entry.get("rationale"):
                raise AssertionError(f"候选『{name}』维度 {cid} 缺少打分理由 rationale")
        for gid in gate_ids:
            if gid not in cand.get("gates", {}):
                raise AssertionError(f"候选『{name}』缺少 kill gate {gid} 的判定")
        # 需求与合规两个维度必须有证据引用，防止关键判断无据可依。
        #
        # 唯一的例外是「确实找不到证据」这种情形：某些候选之所以被淘汰，恰恰是因为
        # 一手需求证据不存在。此时强制要求引用会逼出两种坏结果——要么硬凑一个
        # 不相关的引用，要么把这个候选从池中删掉；两者都会让报告失真。
        # 因此允许显式声明 evidence_absent，但必须同时写明为何找不到，
        # 并由下面的规则强制这类候选的该维度评分不得高于 3 分——
        # 「查无证据」不能被当作「证据中性」处理。
        for cid in ("demand_evidence", "compliance_safety"):
            entry = cand["scores"][cid]
            if entry.get("evidence"):
                continue
            if not entry.get("evidence_absent"):
                raise AssertionError(
                    f"候选『{name}』维度 {cid} 必须给出 evidence（data/sources.jsonl 中的 id），"
                    f"或显式声明 evidence_absent 并说明为何查无证据"
                )
            if entry["score"] > 3:
                raise AssertionError(
                    f"候选『{name}』维度 {cid} 声明查无一手证据，但评分 {entry['score']} 高于上限 3"
                )


def _weighted(rubric: dict, cand: dict, weights: dict[str, float] | None = None) -> float:
    """加权总分，归一化到 0-10 分制。"""
    if weights is None:
        weights = {c["id"]: float(c["weight"]) for c in rubric["criteria"]}
    wsum = sum(weights.values())
    if wsum <= 0:
        return 0.0
    total = sum(weights[c["id"]] * cand["scores"][c["id"]]["score"] for c in rubric["criteria"])
    return total / wsum


def main() -> dict:
    rubric, candidates, sources = load_rubric_candidates_guard()
    _validate(rubric, candidates)

    # ------------------------------------------------------------ kill gates
    gate_lookup = {g["id"]: g for g in rubric["kill_gates"]}
    survivors, eliminated = [], []
    for cand in candidates:
        failed = [
            {
                "gate": gid,
                "gate_name": gate_lookup[gid]["name"],
                "verdict": info.get("verdict"),
                "reason": info.get("reason", ""),
                "evidence": info.get("evidence", []),
            }
            for gid, info in cand["gates"].items()
            if info.get("verdict") == "fail"
        ]
        record = {
            "id": cand["id"],
            "name": cand["name"],
            "branch": cand.get("branch", ""),
            "one_liner": cand.get("one_liner", ""),
            "gates": cand["gates"],
            "failed_gates": failed,
        }
        (eliminated if failed else survivors).append({**record, "_cand": cand})

    # ------------------------------------------------------------ 基准加权分
    base_weights = {c["id"]: float(c["weight"]) for c in rubric["criteria"]}
    for s in survivors:
        cand = s["_cand"]
        s["total"] = _weighted(rubric, cand, base_weights)
        s["scores"] = {
            cid: {
                "score": e["score"],
                "rationale": e["rationale"],
                "evidence": e.get("evidence", []),
                "weight": base_weights[cid],
                "contribution": base_weights[cid] * e["score"] / sum(base_weights.values()),
            }
            for cid, e in cand["scores"].items()
        }
    survivors.sort(key=lambda x: x["total"], reverse=True)
    for i, s in enumerate(survivors, 1):
        s["rank"] = i

    # ------------------------------------------------------------ 稳健性一：权重扰动
    rng = np.random.default_rng(SEED)
    draws = int(rubric["meta"]["perturbation"]["draws"])
    mag = float(rubric["meta"]["perturbation"]["magnitude"])
    crit_ids = [c["id"] for c in rubric["criteria"]]
    w0 = np.array([base_weights[c] for c in crit_ids], dtype=float)
    score_matrix = np.array(
        [[s["_cand"]["scores"][c]["score"] for c in crit_ids] for s in survivors],
        dtype=float,
    )

    factors = rng.uniform(1 - mag, 1 + mag, size=(draws, len(crit_ids)))
    w_draws = w0[None, :] * factors
    w_draws /= w_draws.sum(axis=1, keepdims=True)
    totals = score_matrix @ w_draws.T          # (n_cand, draws)
    winners = np.argmax(totals, axis=0)
    win_counts = np.bincount(winners, minlength=len(survivors))
    ranks = (-totals).argsort(axis=0).argsort(axis=0) + 1   # 每次抽样中各候选的排名

    for i, s in enumerate(survivors):
        s["robustness"] = {
            "p_rank1": float(win_counts[i] / draws),
            "mean_rank": float(ranks[i].mean()),
            "p_top3": float((ranks[i] <= 3).mean()),
            "score_p05": float(np.percentile(totals[i], 5)),
            "score_p95": float(np.percentile(totals[i], 95)),
        }

    # ------------------------------------------------------------ 稳健性二：leave-one-out
    loo = []
    for drop in crit_ids:
        w = {k: v for k, v in base_weights.items() if k != drop}
        ranked = sorted(
            ((s["id"], _weighted_subset(rubric, s["_cand"], w)) for s in survivors),
            key=lambda kv: kv[1],
            reverse=True,
        )
        loo.append({
            "dropped_criterion": drop,
            "winner": ranked[0][0],
            "winner_total": ranked[0][1],
            "runner_up": ranked[1][0] if len(ranked) > 1 else None,
            "margin": ranked[0][1] - ranked[1][1] if len(ranked) > 1 else None,
        })
    loo_winner_ids = {r["winner"] for r in loo}

    # ------------------------------------------------------------ 输出
    top = survivors[0]
    for s in survivors:
        s.pop("_cand", None)
    for e in eliminated:
        e.pop("_cand", None)

    margin = survivors[0]["total"] - survivors[1]["total"] if len(survivors) > 1 else None

    # 第一名与第二名的逐维分差：报告里要逐行显示这个差值，
    # 与其在模板里现算（那样的数字无法被复算校验捕获），不如在此算好并入产物。
    score_gaps = (
        {
            cid: survivors[0]["scores"][cid]["score"] - survivors[1]["scores"][cid]["score"]
            for cid in crit_ids
        }
        if len(survivors) > 1
        else {}
    )

    # 第一名与第二名得分区间是否重叠：供报告陈述，避免手写「完全不重叠」
    w1 = survivors[0]["robustness"]
    w2 = survivors[1]["robustness"] if len(survivors) > 1 else None
    intervals_disjoint = (
        bool(w2 is not None and (w1["score_p95"] < w2["score_p05"] or w2["score_p95"] < w1["score_p05"]))
    )

    payload = {
        "rubric_version": rubric["meta"]["version"],
        "n_candidates": len(candidates),
        "n_eliminated": len(eliminated),
        "n_survivors": len(survivors),
        "n_criteria": len(rubric["criteria"]),
        "runner_up_id": survivors[1]["id"] if len(survivors) > 1 else None,
        "intervals_disjoint": intervals_disjoint,
        "intervals_disjoint_zh": (
            "两者的 5–95 分位区间完全不重叠"
            if intervals_disjoint
            else "两者的 5–95 分位区间存在重叠，须结合 P(保持第一) 一并解读"
        ),
        "criteria": [
            {"id": c["id"], "name": c["name"], "weight": c["weight"], "question": c["question"]}
            for c in rubric["criteria"]
        ],
        "kill_gates": rubric["kill_gates"],
        "eliminated": eliminated,
        "ranking": survivors,
        "score_gaps": score_gaps,
        "winner": {
            "id": top["id"],
            "name": top["name"],
            "total": top["total"],
            "margin_over_runner_up": margin,
            "p_rank1_under_weight_perturbation": top["robustness"]["p_rank1"],
        },
        "robustness": {
            "weight_perturbation": {
                "draws": draws,
                "magnitude": mag,
                "winner_p_rank1": top["robustness"]["p_rank1"],
                "all": {s["id"]: s["robustness"] for s in survivors},
            },
            "leave_one_out": loo,
            "leave_one_out_winner_stable": len(loo_winner_ids) == 1,
            "leave_one_out_winner_ids": sorted(loo_winner_ids),
        },
        "evidence_index": sorted({
            eid
            for s in survivors
            for e in s["scores"].values()
            for eid in e.get("evidence", [])
        }),
        "sources_available": sorted(sources.keys()),
        "n_sources_available": len(sources),
        "n_evidence_cited": len({
            eid
            for s in survivors
            for e in s["scores"].values()
            for eid in e.get("evidence", [])
        }),
    }
    return payload


def _weighted_subset(rubric: dict, cand: dict, weights: dict[str, float]) -> float:
    wsum = sum(weights.values())
    total = sum(w * cand["scores"][cid]["score"] for cid, w in weights.items())
    return total / wsum


if __name__ == "__main__":
    result = main()
    path = write_json("scoring", result)
    print(f"已写出 {path}")
    print(f"\n候选 {result['n_candidates']} 个，淘汰 {result['n_eliminated']} 个，进入排名 {result['n_survivors']} 个")
    print(f"\n第一名：{result['winner']['name']}  总分 {result['winner']['total']:.3f}")
    print(f"权重扰动下保持第一的概率：{result['winner']['p_rank1_under_weight_perturbation']:.1%}")
    print(f"leave-one-out 第一名稳定：{result['robustness']['leave_one_out_winner_stable']}")
    print("\n排名：")
    for s in result["ranking"]:
        print(f"  {s['rank']}. {s['name']:<34s} {s['total']:.3f}  (P(第一)={s['robustness']['p_rank1']:.1%})")
    if result["eliminated"]:
        print("\n被 kill gate 淘汰：")
        for e in result["eliminated"]:
            gates = "、".join(g["gate_name"] for g in e["failed_gates"])
            print(f"  - {e['name']}｜未过：{gates}")
