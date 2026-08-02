"""报告的 CSS：苹果 HIG 取向的排版系统 + A4 打印分页控制。

单独成文件而不是塞进 build_report.py，是为了让样式改动不必触碰内容逻辑。
设计取向：8pt 网格、大留白、1px 分隔线、单一强调色、克制的圆角与阴影。
打印侧的关键是 break-inside: avoid 与 @page，避免图表与表格被切成两半。
"""

CSS = """
:root {
  --ink:        #1D1D1F;
  --ink-2:      #424245;
  --ink-3:      #6E6E73;
  --line:       #D2D2D7;
  --line-soft:  #E8E8ED;
  --paper:      #FFFFFF;
  --paper-2:    #F5F5F7;
  --accent:     #0071E3;
  --accent-dim: #E8F1FD;
  --warn:       #C7500A;
  --warn-dim:   #FFF4E8;
  --bad:        #C4271B;
  --bad-dim:    #FDECEA;
  --good:       #1F7A3D;
  --good-dim:   #E9F7EE;
  --radius:     14px;
  --unit:       8px;
}

* { box-sizing: border-box; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI",
               "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  font-size: 10.5pt;
  line-height: 1.72;
  letter-spacing: 0.005em;
  font-feature-settings: "tnum" 1;
}

.page {
  max-width: 176mm;
  margin: 0 auto;
  padding: 0;
}

/* ---------------------------------------------------------------- 文字层级 */

h1, h2, h3, h4 {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI",
               "PingFang SC", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  letter-spacing: -0.012em;
  line-height: 1.3;
  margin: 0;
  break-after: avoid;
}

h1 { font-size: 26pt; font-weight: 700; }
h2 { font-size: 17pt; font-weight: 650; margin: calc(var(--unit) * 5) 0 calc(var(--unit) * 2); }
h3 { font-size: 12.5pt; font-weight: 650; margin: calc(var(--unit) * 3.5) 0 var(--unit); }
h4 { font-size: 10.8pt; font-weight: 650; margin: calc(var(--unit) * 2.5) 0 calc(var(--unit) * 0.5); }

/* 中英混排时 justify 会把行内空格拉得很宽，苹果中文站也用左对齐，故不 justify。
   line-break: strict 保证中文标点不出现在行首。 */
p { margin: 0 0 calc(var(--unit) * 1.5); text-align: left; line-break: strict; }

a { color: var(--accent); text-decoration: none; word-break: break-all; }

strong { font-weight: 650; }

.lede {
  font-size: 12pt;
  line-height: 1.68;
  color: var(--ink-2);
}

.muted { color: var(--ink-3); }
.small { font-size: 9pt; line-height: 1.6; }
.tiny  { font-size: 8pt;  line-height: 1.55; }
.mono  { font-family: "SF Mono", ui-monospace, Consolas, monospace; font-size: 9pt; }

/* 章节编号 */
.eyebrow {
  font-size: 8.5pt;
  font-weight: 650;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: calc(var(--unit) * 0.5);
}

/* ---------------------------------------------------------------- 封面 */

.cover {
  min-height: 232mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-top: calc(var(--unit) * 6);
}
.cover h1 { font-size: 34pt; line-height: 1.22; letter-spacing: -0.02em; }
.cover .sub { font-size: 14pt; color: var(--ink-2); margin-top: calc(var(--unit) * 2); font-weight: 400; }
.cover .rule { height: 3px; width: 56px; background: var(--accent); margin: calc(var(--unit) * 4) 0; border-radius: 2px; }
.cover .meta { font-size: 9.5pt; color: var(--ink-3); line-height: 2.0; }
.cover .meta b { color: var(--ink-2); font-weight: 600; }

/* ---------------------------------------------------------------- 卡片与网格 */

.card {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  padding: calc(var(--unit) * 2.5);
  margin: calc(var(--unit) * 2) 0;
  break-inside: avoid;
}
.card.tint  { background: var(--paper-2); border-color: transparent; }
.card.accent{ background: var(--accent-dim); border-color: transparent; }
.card.warn  { background: var(--warn-dim);   border-color: transparent; }
.card.bad   { background: var(--bad-dim);    border-color: transparent; }
.card.good  { background: var(--good-dim);   border-color: transparent; }
.card > :last-child { margin-bottom: 0; }
.card h4:first-child, .card h3:first-child { margin-top: 0; }

.grid { display: grid; gap: calc(var(--unit) * 1.5); margin: calc(var(--unit) * 2) 0; }
.grid.c2 { grid-template-columns: repeat(2, 1fr); }
.grid.c3 { grid-template-columns: repeat(3, 1fr); }
.grid.c4 { grid-template-columns: repeat(4, 1fr); }

/* 指标砖 */
.kpi {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  padding: calc(var(--unit) * 1.75);
  break-inside: avoid;
}
.kpi .label { font-size: 8.5pt; color: var(--ink-3); line-height: 1.4; }
.kpi .value {
  font-size: 19pt; font-weight: 650; letter-spacing: -0.02em;
  margin: calc(var(--unit) * 0.5) 0 0;
  font-variant-numeric: tabular-nums;
}
.kpi .foot { font-size: 8pt; color: var(--ink-3); line-height: 1.45; margin-top: calc(var(--unit) * 0.5); }
.kpi.pos .value { color: var(--good); }
.kpi.neg .value { color: var(--bad); }
.kpi.neutral .value { color: var(--ink); }
.kpi.hi { background: var(--accent-dim); border-color: transparent; }
.kpi.hi .value { color: var(--accent); }

/* ---------------------------------------------------------------- 表格 */

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin: calc(var(--unit) * 2) 0;
}
/* 表格允许跨页：整表 break-inside: avoid 会让超过一页高的表格把前一页整片留白。
   代价用两条规则补回来——表头在每页重复，单行不被切成两半。 */
thead { display: table-header-group; }
tr { break-inside: avoid; }
caption {
  caption-side: top;
  text-align: left;
  font-size: 9pt;
  font-weight: 650;
  color: var(--ink-2);
  padding-bottom: var(--unit);
}
th, td {
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid var(--line-soft);
}
thead th {
  border-bottom: 1px solid var(--line);
  font-weight: 650;
  color: var(--ink-2);
  font-size: 8.5pt;
  letter-spacing: 0.02em;
}
tbody tr:last-child td { border-bottom: none; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tr.total td { border-top: 1px solid var(--line); font-weight: 650; }
tr.dim td { color: var(--ink-3); }
/* .table-wrap 只是语义容器，默认允许跨页；确实短、被切开会显得凌乱的表格
   额外加 .keep 强制整块不跨页。 */
.table-wrap { break-inside: auto; }
.table-wrap.keep { break-inside: avoid; }

/* 判定标签 */
.tag {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 5px;
  font-size: 8pt;
  font-weight: 650;
  white-space: nowrap;
}
.tag.pass { background: var(--good-dim); color: var(--good); }
.tag.fail { background: var(--bad-dim);  color: var(--bad); }
.tag.warn { background: var(--warn-dim); color: var(--warn); }
.tag.info { background: var(--accent-dim); color: var(--accent); }
.tag.flat { background: var(--paper-2); color: var(--ink-3); }

/* ---------------------------------------------------------------- 图表 */

figure {
  margin: calc(var(--unit) * 2.5) 0;
  break-inside: avoid;
}
figure svg { width: 100%; height: auto; display: block; }
figcaption {
  font-size: 8.5pt;
  color: var(--ink-3);
  line-height: 1.6;
  margin-top: var(--unit);
  padding-left: 2px;
  border-left: 2px solid var(--line-soft);
  padding-left: 10px;
}

/* ---------------------------------------------------------------- 列表 */

ul, ol { margin: 0 0 calc(var(--unit) * 1.5); padding-left: 1.35em; }
li { margin-bottom: calc(var(--unit) * 0.65); }
li > ul, li > ol { margin-top: calc(var(--unit) * 0.65); }

dl.defs { margin: calc(var(--unit) * 1.5) 0; }
dl.defs dt { font-weight: 650; font-size: 9.5pt; margin-top: var(--unit); }
dl.defs dd { margin: 2px 0 0; padding-left: 0; color: var(--ink-2); font-size: 9.5pt; }

/* 公式 */
.formula {
  font-family: "SF Mono", ui-monospace, Consolas, monospace;
  font-size: 9pt;
  background: var(--paper-2);
  border-radius: 8px;
  padding: calc(var(--unit) * 1.25) calc(var(--unit) * 1.5);
  margin: var(--unit) 0 calc(var(--unit) * 1.5);
  line-height: 1.75;
  white-space: pre-wrap;
  break-inside: avoid;
}

/* 引注 */
.cite { font-size: 8pt; color: var(--ink-3); }
.cite code { font-family: "SF Mono", ui-monospace, Consolas, monospace; }

/* 分隔 */
hr.sep { border: 0; border-top: 1px solid var(--line-soft); margin: calc(var(--unit) * 4) 0; }

/* 目录 */
.toc { font-size: 9.5pt; }
/* 双栏让目录收在一页内；每个章节块不允许跨栏切断 */
.toc > ol { columns: 2; column-gap: calc(var(--unit) * 4); }
.toc ol { list-style: none; padding-left: 0; counter-reset: sec; }
.toc ol > li { counter-increment: sec; margin-bottom: calc(var(--unit) * 0.9); break-inside: avoid; }
.toc ol > li > span.no { color: var(--accent); font-weight: 650; margin-right: 8px; }
.toc ol ol { padding-left: 26px; margin-top: calc(var(--unit) * 0.6); }
.toc ol ol > li { color: var(--ink-3); font-size: 9pt; margin-bottom: 3px; }

/* ---------------------------------------------------------------- 打印 */

@page {
  size: A4;
  margin: 17mm 17mm 16mm 17mm;
}

.page-break { break-before: page; }
.avoid-break { break-inside: avoid; }

@media print {
  body { font-size: 9.8pt; }
  h1 { font-size: 23pt; }
  h2 { font-size: 15.5pt; }
  h3 { font-size: 11.6pt; }
  .cover { min-height: 228mm; }
  a { color: var(--ink); }
  figure svg { max-height: 92mm; }
  figure.tall svg { max-height: 120mm; }
}
"""
