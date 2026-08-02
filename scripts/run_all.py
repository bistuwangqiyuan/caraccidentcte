"""一键复现全部数字与报告。"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = [
    ("audit_original", "复算原稿自报指标", "audit_original"),
    ("score_opportunities", "候选筛查与评分", "scoring"),
    ("unit_economics", "单位经济模型", "unit_economics"),
    ("monte_carlo", "蒙特卡洛模拟", "monte_carlo"),
    ("risk_metrics", "风险与收益指标", "risk_metrics"),
    ("bp_plan", "商业计划的量化推导", "bp_plan"),
    ("charts", "生成图表", None),
    ("build_report", "渲染 HTML 报告", None),
]


def run_step(module_name: str, label: str, artifact: str | None) -> float:
    t0 = time.perf_counter()
    print(f"\n{'=' * 78}\n> {label}  (scripts/{module_name}.py)\n{'=' * 78}", flush=True)
    mod = importlib.import_module(module_name)
    result = mod.main()
    if artifact is not None and isinstance(result, dict):
        from common import write_json
        write_json(artifact, result)
    dt = time.perf_counter() - t0
    print(f"  done {dt:.1f}s", flush=True)
    return dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    t_start = time.perf_counter()
    for module_name, label, artifact in STEPS:
        run_step(module_name, label, artifact)

    if not args.no_pdf:
        print(f"\n{'=' * 78}\n> export PDF  (scripts/export_pdf.py)\n{'=' * 78}", flush=True)
        rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "export_pdf.py")])
        if rc != 0:
            print("PDF 导出失败", file=sys.stderr)
            return rc

    if not args.no_verify:
        print(f"\n{'=' * 78}\n> verify_all  (scripts/verify_all.py)\n{'=' * 78}", flush=True)
        rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "verify_all.py")])
        if rc != 0:
            return rc

    print(f"\n全流程完成，总耗时 {time.perf_counter() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
