# Car Accident CTE · 商业机会挖掘与分析报告（重建）

从 Google Trends 种子词 `car accident cte` 出发，经合规红线闸门、锚定评分、自下而上单位经济与蒙特卡洛，产出可复算的中文 HTML / PDF。

硬约束：单人、每周 ≤20 小时、运营风险资本 ≤ US$2,000、月净烧 ≤ US$100、全 AI 无人运营、纯自有资金精益创业。

## 一键复现

```bash
pip install -r requirements.txt

python scripts/run_all.py
```

仅 HTML（跳过 PDF）：

```bash
python scripts/run_all.py --no-pdf
```

仅校验：

```bash
python scripts/verify_all.py
```

原稿口径速算：

```bash
python scripts/verify_bp_math.py
```

## 产物

| 路径 | 说明 |
|------|------|
| `report/index.html` | Apple 视觉风格报告 |
| `report/商业机会挖掘与分析报告.pdf` | Chrome/Playwright 导出 |
| `outputs/*.json` | 全部可复算中间结果 |
| `data/need_original.txt` | 原始种子 BP（审计绑定） |
| `need.txt` | 校准后摘要 |

## 流水线

1. `audit_original` — 复盘原稿矛盾  
2. `score_opportunities` — kill gate + 评分 + 稳健性  
3. `unit_economics` — 确定性单位经济  
4. `monte_carlo` — 40,000 路径 × 60 月  
5. `risk_metrics` — 胜率 / 盈亏比 / 风险调整年化 / 100 万 Kelly  
6. `bp_plan` — 90 天里程碑与 go/no-go  
7. `charts` + `build_report` + `export_pdf`  
8. `verify_all` — 独立复算与清单回放  

## 数字纪律

- 报告数值只能由 `outputs/*.json` 经 `ValueRegistry` 注入。  
- 无出处或不可复现的数据不进入结论硬前提；待测量参数在 `config/assumptions.yaml` 标明。  
- 明确不做：有偿过错认定、PI 和解代理、CTE 诊断。

## 第一名机会

以 `outputs/scoring.json` 的 `winner` 字段为准（由评分涌现，非标题预设）。当前硬约束下胜出的是**新加坡事故后证据包与保险 FNOL 清单**。
