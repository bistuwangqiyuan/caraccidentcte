"""用本机已安装的 Chrome 无头打印 report/index.html 为 A4 PDF。

优先 Playwright（可精确控制 print_background 与 prefer_css_page_size，并可等待字体就绪）；
Playwright 不可用时回退到 chrome.exe --headless=new --print-to-pdf。

导出后做基本质量校验：文件存在、体积合理、页数可读。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "report" / "index.html"
PDF = ROOT / "report" / "商业机会挖掘与分析报告.pdf"


def count_pages(data: bytes) -> int:
    n = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    if n <= 0:
        n = data.count(b"/Type/Page") - data.count(b"/Type/Pages")
    return max(n, 0)


def via_playwright() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  Playwright 未安装，回退到 Chrome 命令行")
        return False

    try:
        with sync_playwright() as p:
            browser = None
            for channel in ("chrome", "msedge"):
                try:
                    browser = p.chromium.launch(channel=channel, headless=True)
                    print(f"  使用浏览器通道：{channel}")
                    break
                except Exception:
                    continue
            if browser is None:
                browser = p.chromium.launch(headless=True)
                print("  使用 Playwright 自带 Chromium")

            page = browser.new_page()
            page.goto(HTML.as_uri(), wait_until="load")
            # 等字体与内联 SVG 完成布局，否则分页会漂移
            page.evaluate("() => document.fonts ? document.fonts.ready : true")
            page.wait_for_timeout(1200)
            page.emulate_media(media="print")
            page.pdf(
                path=str(PDF),
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
            )
            browser.close()
        return True
    except Exception as exc:  # noqa: BLE001 - 回退路径需捕获任何失败
        print(f"  Playwright 导出失败：{exc}")
        return False


def via_chrome_cli() -> bool:
    candidates = [
        shutil.which("chrome"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    exe = next((c for c in candidates if c and Path(c).exists()), None)
    if exe is None:
        print("  未找到 Chrome 或 Edge 可执行文件")
        return False
    print(f"  使用 {exe}")
    cmd = [
        exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={PDF}", HTML.as_uri(),
    ]
    return subprocess.call(cmd) == 0


def main() -> int:
    if not HTML.exists():
        print(f"缺少 {HTML}，请先运行 python scripts/build_report.py", file=sys.stderr)
        return 1
    PDF.parent.mkdir(parents=True, exist_ok=True)
    if PDF.exists():
        PDF.unlink()

    if not via_playwright() and not via_chrome_cli():
        print("PDF 导出失败：两条路径均不可用", file=sys.stderr)
        return 1

    if not PDF.exists():
        print("PDF 导出失败：文件未生成", file=sys.stderr)
        return 1

    data = PDF.read_bytes()
    size_kb = len(data) / 1024
    pages = count_pages(data)
    print(f"\n已导出 {PDF}")
    print(f"  页数 {pages}，体积 {size_kb:,.0f} KB")
    if size_kb < 50:
        print("  警告：体积偏小，请检查图表是否正常内联", file=sys.stderr)
        return 1
    if pages < 8:
        print("  警告：页数偏少，请检查内容是否完整", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
