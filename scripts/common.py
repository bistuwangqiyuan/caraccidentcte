"""共享工具：路径、JSON 读写、格式化、苹果风格图表主题。

所有脚本的数值输出统一写入 outputs/*.json，报告渲染只允许从这些 JSON 取数，
以保证「报告中每一个数字都可被第三方独立复算」。
"""

from __future__ import annotations

import html as _html
import inspect
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import yaml

# Windows 控制台默认 GBK，中文与数学符号（如 U+2212）会导致 UnicodeEncodeError。
# 文件 I/O 始终显式使用 UTF-8，这里只修正标准输出流。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = ROOT / "report"

for _d in (OUTPUT_DIR, CHART_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 报告基准日：所有「截至」表述统一引用此日期
AS_OF = "2026-08-02"

# 全局随机种子，保证蒙特卡洛结果可复现
SEED = 20260802

# ---------------------------------------------------------------- 苹果视觉风格

PALETTE = {
    "blue": "#0071E3",      # Apple system blue
    "indigo": "#5E5CE6",
    "teal": "#30B0C7",
    "green": "#34C759",
    "orange": "#FF9F0A",
    "red": "#FF3B30",
    "pink": "#FF375F",
    "gray": "#8E8E93",
    "gray2": "#C7C7CC",
    "gray3": "#E5E5EA",
    "ink": "#1D1D1F",       # Apple near-black
    "ink2": "#6E6E73",
    "paper": "#FFFFFF",
    "wash": "#F5F5F7",      # Apple light background
}

SERIES_COLORS = [
    PALETTE["blue"],
    PALETTE["orange"],
    PALETTE["teal"],
    PALETTE["indigo"],
    PALETTE["green"],
    PALETTE["pink"],
    PALETTE["gray"],
]

# 中文字体回退链：Windows 上优先微软雅黑，保证 PDF 无缺字
CJK_FONTS = [
    "Microsoft YaHei",
    "PingFang SC",
    "Noto Sans CJK SC",
    "SimHei",
    "DejaVu Sans",
]


def apply_chart_theme() -> None:
    """极简、无边框、细网格的苹果取向图表主题。"""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": CJK_FONTS,
        "axes.unicode_minus": False,
        "figure.facecolor": PALETTE["paper"],
        "axes.facecolor": PALETTE["paper"],
        "axes.edgecolor": PALETTE["gray3"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": PALETTE["gray3"],
        "grid.linewidth": 0.6,
        "grid.alpha": 0.9,
        "axes.labelcolor": PALETTE["ink2"],
        "axes.titlecolor": PALETTE["ink"],
        "axes.titlesize": 12,
        "axes.titleweight": "600",
        "axes.labelsize": 9.5,
        "xtick.color": PALETTE["ink2"],
        "ytick.color": PALETTE["ink2"],
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.08,
        "savefig.transparent": False,
        "svg.fonttype": "none",  # 保留文本为文本，PDF 中矢量可选
    })


def save_chart(fig: plt.Figure, name: str) -> Path:
    """保存为 SVG，供 HTML 内联，PDF 中保持矢量清晰。"""
    path = CHART_DIR / f"{name}.svg"
    fig.savefig(path, format="svg")
    plt.close(fig)
    return path


# ---------------------------------------------------------------- 读写

def write_json(name: str, payload: Any) -> Path:
    path = OUTPUT_DIR / f"{name}.json"
    payload = _add_provenance(payload, name)
    # allow_nan=False：Python 默认会把 inf/nan 写成 `Infinity`/`NaN`，
    # 这不是合法 JSON，任何严格解析器（含浏览器 JSON.parse）都会拒绝。
    # 与其产出一份"只有本项目自己读得懂"的产物，不如让写入直接失败。
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False,
                   allow_nan=False),
        encoding="utf-8",
    )
    return path


def _caller_script() -> str:
    """返回调用 write_json 的最外层脚本文件名（跳过 common.py 自身）。"""
    frame = inspect.currentframe()
    while frame is not None:
        filename = Path(frame.f_code.co_filename).name
        if filename != "common.py":
            return filename
        frame = frame.f_back
    return "common.py"


def _add_provenance(payload: Any, name: str) -> Any:
    if isinstance(payload, dict) and "_meta" not in payload:
        payload = {
            "_meta": {
                "artifact": name,
                # 取实际调用者的文件名，而非由产物名拼出来的猜测值：
                # scoring.json 是由 score_opportunities.py 生成的，
                # 写成 "scripts/scoring.py" 会指向一个不存在的文件，
                # 使复现说明失效——溯源字段错了比没有更糟。
                "generated_by": f"scripts/{_caller_script()}",
                "as_of": AS_OF,
                "generated_on": date.today().isoformat(),
                "seed": SEED,
            },
            **payload,
        }
    return payload


def read_json(name: str) -> Any:
    path = OUTPUT_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"缺少 {path}，请先运行 python scripts/run_all.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(name: str) -> Any:
    path = CONFIG_DIR / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_rubric_candidates_guard() -> tuple[dict, list[dict], dict[str, dict]]:
    """加载评分锚定表、候选池与证据库，并校验所有证据引用真实存在。

    任何指向不存在证据 id 的引用都会立即报错，防止出现"看起来有出处"的假引用。
    """
    rubric = load_yaml("rubric.yaml")
    candidates = load_yaml("candidates.yaml")["candidates"]
    sources = load_sources()

    dangling: list[str] = []
    for cand in candidates:
        for cid, entry in cand.get("scores", {}).items():
            for eid in entry.get("evidence", []) or []:
                if eid not in sources:
                    dangling.append(f"{cand['id']}.{cid} -> {eid}")
        for gid, info in cand.get("gates", {}).items():
            for eid in info.get("evidence", []) or []:
                if eid not in sources:
                    dangling.append(f"{cand['id']}.{gid} -> {eid}")
    if dangling:
        raise AssertionError(
            "候选池引用了 data/sources.jsonl 中不存在的证据 id：\n  - "
            + "\n  - ".join(dangling)
        )
    return rubric, candidates, sources


def load_sources() -> dict[str, dict]:
    """读取证据库，按 id 索引。"""
    path = DATA_DIR / "sources.jsonl"
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        out[rec["id"]] = rec
    return out


# ---------------------------------------------------------------- 格式化

def usd(x: float, decimals: int = 0) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    neg = x < 0
    s = f"${abs(x):,.{decimals}f}"
    return f"-{s}" if neg else s


def pct(x: float, decimals: int = 1) -> str:
    """x 为小数形式（0.153 -> 15.3%）。"""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x * 100:.{decimals}f}%"


def mult(x: float, decimals: int = 2) -> str:
    return f"{x:.{decimals}f}x"


def num(x: float, decimals: int = 1) -> str:
    return f"{x:,.{decimals}f}"


# YAML 的折叠标量（>）会把换行折成一个空格，于是中文标点后凭空多出空格；
# HTML 也会把源码换行折成空格。这类空格是纯排版噪声，注入 HTML 前必须清除，
# 而中英、中数之间的单空格是苹果中文排版惯例，必须保留。
_CJK_CLOSE_PUNCT = "，。、；：！？）】》」』”’…—"
_CJK_OPEN_PUNCT = "（【《「『“‘"
_CJK_CHAR = "\u3400-\u9fff"
_WS_RUN = re.compile(r"[ \t\r\n]+")
_IS_CJK = re.compile(f"[{_CJK_CHAR}{_CJK_CLOSE_PUNCT}{_CJK_OPEN_PUNCT}]")


def space_between(left: str, right: str) -> str:
    """判断一段空白该塌缩为空还是保留一个空格，规则只看两侧字符。"""
    if left and left in _CJK_CLOSE_PUNCT:
        return ""
    if left and right and _IS_CJK.match(left) and _IS_CJK.match(right):
        return ""
    if right and right in _CJK_OPEN_PUNCT:
        return ""
    return " "


def tidy_cjk_spaces(text: str) -> str:
    """整理字符串中的空白：塌缩所有空白串（含换行），并去掉首尾空白。

    用于从 YAML / JSON 注入报告的叙述文本。结果不含换行，因此后续对整份 HTML
    做的换行级整理不会再改动它——这是渲染回放能逐字命中的前提。
    """
    def repl(m: re.Match[str]) -> str:
        left = text[m.start() - 1] if m.start() > 0 else ""
        right = text[m.end()] if m.end() < len(text) else ""
        return space_between(left, right)

    return _WS_RUN.sub(repl, text).strip()


class ValueRegistry:
    """报告数值注册表：报告中出现的每一个数字都必须经由此处取数。

    机制：
      - v("risk_metrics.primary.win_rate", "pct") 从 outputs/risk_metrics.json 取值并格式化；
      - 同时把 (JSON 路径, 原始值, 格式化结果) 记入清单，写出 outputs/render_manifest.json；
      - scripts/verify_all.py 随后独立重放：按路径重新取值、重新格式化、并断言
        该字符串确实出现在渲染后的 HTML 中。
    任何在模板里手写的数字都不会进入清单，会被 verify_all.py 的未登记数字扫描捕获。
    """

    FORMATTERS = {
        "raw": lambda x: str(x),
        "int": lambda x: f"{int(round(x)):,d}",
        "num": lambda x: num(x, 1),
        "num0": lambda x: num(x, 0),
        "num1": lambda x: num(x, 1),
        "num2": lambda x: num(x, 2),
        "usd": lambda x: usd(x, 0),
        "usd2": lambda x: usd(x, 2),
        "pct": lambda x: pct(x, 1),
        "pct0": lambda x: pct(x, 0),
        "pct2": lambda x: pct(x, 2),
        "mult": lambda x: mult(x, 2),
        "mult1": lambda x: mult(x, 1),
        "ratio": lambda x: f"{x:.2f} : 1",
        # esc：把 JSON 中的中文叙述注入 HTML（HTML 转义 + 清除 YAML 折叠留下的空格）。
        # 这类字符串内部常含数字（如"$28.80"、"6.1%"），它们同样必须来自
        # outputs/*.json 而不能在模板里手写，因此也要进注册表接受回放校验。
        "esc": lambda x: tidy_cjk_spaces(_html.escape(str(x), quote=False)),
    }

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self.manifest: list[dict] = []

    def _artifact(self, name: str) -> Any:
        if name not in self._cache:
            self._cache[name] = read_json(name)
        return self._cache[name]

    def resolve(self, path: str) -> Any:
        parts = path.split(".")
        node = self._artifact(parts[0])
        for p in parts[1:]:
            if isinstance(node, list):
                node = node[int(p)]
            else:
                if p not in node:
                    raise KeyError(f"数值路径不存在：{path}（在 {p} 处中断）")
                node = node[p]
        return node

    def v(self, path: str, fmt: str = "raw") -> str:
        if fmt not in self.FORMATTERS:
            raise ValueError(f"未知格式 {fmt}")
        raw = self.resolve(path)
        if fmt == "esc":
            # esc 只用于叙述文本。若误用于数值，会把 5.870000000000001 这类
            # 浮点原样印进报告，因此在此直接拒绝而不是让它悄悄通过。
            if not isinstance(raw, str):
                raise TypeError(f"格式 esc 只能用于字符串，{path} 的类型是 {type(raw).__name__}")
            text = self.FORMATTERS["esc"](raw)
        elif isinstance(raw, bool):
            text = "是" if raw else "否"
        elif raw is None:
            text = "n/a"
        elif isinstance(raw, str):
            text = tidy_cjk_spaces(raw)
        elif isinstance(raw, float) and math.isinf(raw):
            text = "∞"
        else:
            text = self.FORMATTERS[fmt](raw)
        self.manifest.append({
            "path": path,
            "fmt": fmt,
            "raw": raw if not (isinstance(raw, float) and math.isinf(raw)) else "Infinity",
            "rendered": text,
        })
        return text

    def write_manifest(self) -> Path:
        path = OUTPUT_DIR / "render_manifest.json"
        path.write_text(
            json.dumps(
                {
                    "count": len(self.manifest),
                    "as_of": AS_OF,
                    "entries": self.manifest,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path


def platform_fee(customers, tiers: list[dict]):
    """按已连接组织数返回平台档位月费，支持标量与 numpy 数组。

    Xero 按「连接数」而非「客户数」计费，而一个直客对应一个组织连接，
    因此客户数直接决定档位。这是阶梯成本而非平滑曲线，必须按档计。
    超出最高档时沿用最高档费用，并由调用方另行提示需商务议价。
    """
    ladder = sorted(tiers, key=lambda t: t["max_connections"])
    if not ladder:
        raise ValueError("platform_tiers 未定义任何档位")

    c = np.asarray(customers, dtype=float)
    fee = np.full(c.shape, float(ladder[-1]["monthly_usd"]))
    # 从高到低覆盖，最终每个元素落在其最小的满足档位上
    for t in reversed(ladder):
        fee = np.where(c <= t["max_connections"], float(t["monthly_usd"]), fee)
    return fee if fee.shape else float(fee)


def cagr(multiple: float, years: float) -> float:
    """由总倍数与年数求年化复合增长率。倍数 <= 0 时返回 -1（本金全损）。"""
    if multiple <= 0:
        return -1.0
    return multiple ** (1.0 / years) - 1.0


def kelly_binary(p: float, b: float) -> float:
    """二元赌局 Kelly 最优比例 f* = (p*b - q) / b = p - q/b。

    p: 获胜概率；b: 盈亏比（赢时净赔率，即每 1 单位风险赢 b 单位）。
    返回值可为负，表示该赌局不应参与。
    """
    if b <= 0:
        return float("-inf")
    q = 1.0 - p
    return (p * b - q) / b


def kelly_general(outcomes: list[tuple[float, float]]) -> float:
    """一般化 Kelly：给定 (概率, 净收益倍数) 列表，数值最大化 E[ln(1+f*r)]。

    净收益倍数 r = -1 表示投入部分全损。返回最优 f（限制在 [0, 1]）。
    """
    lo, hi = 0.0, 1.0

    def dlog(f: float) -> float:
        total = 0.0
        for p, r in outcomes:
            denom = 1.0 + f * r
            if denom <= 1e-12:
                return float("-inf")
            total += p * r / denom
        return total

    if dlog(0.0) <= 0:
        return 0.0
    if dlog(hi - 1e-9) > 0:
        return 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if dlog(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def certainty_equivalent_log(outcomes: list[tuple[float, float]]) -> float:
    """对数效用下的确定性等价倍数：exp(E[ln(M)])。

    outcomes 为 (概率, 期末倍数 M) 列表。M<=0 时对数效用为负无穷，
    这在数学上意味着全损不可接受；此处以 floor 处理并明确标注。
    """
    FLOOR = 1e-6
    total = 0.0
    for p, m in outcomes:
        total += p * math.log(max(m, FLOOR))
    return math.exp(total)
