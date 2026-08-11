#!/usr/bin/env python3
"""NCINS-200 test runner.

Usage:
    python app.py
    python app.py --unit
    python app.py --integration
    python app.py --port 0          # random free port (default)
    python app.py --port 8080       # fixed port
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import webbrowser
import zipfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
ARTIFACTS_DIR = Path("/opt/cursor/artifacts")
# 0 = OS picks a random free port for the report server
DEFAULT_PORT = 0


def _ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def run_tests(marker: str | None) -> tuple[int, Path, Path]:
    """Run pytest and produce HTML + JUnit reports. Returns (exit_code, html, junit)."""
    _ensure_dirs()
    stamp = _timestamp()
    html_report = REPORTS_DIR / f"ncins200_report_{stamp}.html"
    junit_report = REPORTS_DIR / f"ncins200_junit_{stamp}.xml"
    latest_html = REPORTS_DIR / "latest.html"
    latest_junit = REPORTS_DIR / "latest.xml"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        f"--html={html_report}",
        "--self-contained-html",
        f"--junitxml={junit_report}",
    ]
    if marker:
        cmd.extend(["-m", marker])

    print("Запуск тестов:", flush=True)
    print(" ", " ".join(cmd), flush=True)
    print(flush=True)
    result = subprocess.run(cmd, cwd=ROOT)

    if html_report.exists():
        shutil.copyfile(html_report, latest_html)
    if junit_report.exists():
        shutil.copyfile(junit_report, latest_junit)

    return result.returncode, html_report if html_report.exists() else latest_html, junit_report


def build_download_bundle(html_report: Path, junit_report: Path, exit_code: int) -> Path:
    """Create zip with reports + summary and copy to artifacts."""
    _ensure_dirs()
    stamp = _timestamp()
    zip_name = f"ncins200_test_results_{stamp}.zip"
    zip_path = REPORTS_DIR / zip_name

    summary = {
        "task": "NCINS-200",
        "method": "POST /v1/ins-premium/calculate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pytest_exit_code": exit_code,
        "html_report": html_report.name if html_report.exists() else None,
        "junit_report": junit_report.name if junit_report.exists() else None,
        "how_to_run": "python app.py",
    }
    summary_path = REPORTS_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(summary_path, arcname="summary.json")
        if html_report.exists():
            archive.write(html_report, arcname=html_report.name)
        latest_html = REPORTS_DIR / "latest.html"
        if latest_html.exists():
            archive.write(latest_html, arcname="latest.html")
        if junit_report.exists():
            archive.write(junit_report, arcname=junit_report.name)
        latest_junit = REPORTS_DIR / "latest.xml"
        if latest_junit.exists():
            archive.write(latest_junit, arcname="latest.xml")

    artifact_zip = ARTIFACTS_DIR / zip_name
    shutil.copyfile(zip_path, artifact_zip)

    # Stable "latest" names for easy download
    for src, name in (
        (zip_path, "ncins200_test_results_latest.zip"),
        (REPORTS_DIR / "latest.html", "ncins200_report_latest.html"),
        (summary_path, "ncins200_summary_latest.json"),
    ):
        if src.exists():
            shutil.copyfile(src, ARTIFACTS_DIR / name)
            shutil.copyfile(src, REPORTS_DIR / name)

    return zip_path


def public_host(host: str) -> str:
    """0.0.0.0 is bind-only; show a clickable loopback URL instead."""
    return "127.0.0.1" if host in {"0.0.0.0", "::"} else host


def create_report_server(host: str, port: int) -> tuple[ThreadingHTTPServer, int]:
    """Bind report HTTP server. port<=0 selects a random free port."""
    requested = port if port and port > 0 else 0
    server = ThreadingHTTPServer((host, requested), QuietHandler)
    return server, int(server.server_address[1])


def write_index_page(zip_path: Path, html_report: Path, exit_code: int, host: str, port: int) -> Path:
    status = "OK" if exit_code == 0 else f"COMPLETED_WITH_CODE_{exit_code}"
    shown_host = public_host(host)
    download_url = f"http://{shown_host}:{port}/reports/{quote(zip_path.name)}"
    html_url = f"http://{shown_host}:{port}/reports/latest.html"
    index = REPORTS_DIR / "index.html"
    index.write_text(
        f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <title>NCINS-200 — отчёт тестов</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; margin: 40px; background: #f3f6f4; color: #14201a; }}
    .box {{ max-width: 720px; background: #fff; border: 1px solid #c9d5ce; padding: 28px 32px; }}
    h1 {{ margin-top: 0; font-size: 28px; }}
    a.btn {{ display: inline-block; margin: 8px 12px 8px 0; padding: 12px 18px; background: #0f5c45; color: #fff; text-decoration: none; }}
    a.btn.secondary {{ background: #2c3e36; }}
    code {{ background: #eef2ef; padding: 2px 6px; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>NCINS-200 — расчёт страховой премии</h1>
    <p>Статус прогона: <strong>{status}</strong></p>
    <p>Запуск: <code>python app.py</code></p>
    <p>
      <a class="btn" href="/reports/{quote(zip_path.name)}">Скачать ZIP с результатами</a>
      <a class="btn secondary" href="/reports/ncins200_test_results_latest.zip">Скачать latest.zip</a>
      <a class="btn secondary" href="/reports/latest.html">Открыть HTML-отчёт</a>
    </p>
    <p>Прямые ссылки:</p>
    <ul>
      <li><a href="{download_url}">{download_url}</a></li>
      <li><a href="{html_url}">{html_url}</a></li>
    </ul>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    # Convenience root index
    (ROOT / "index.html").write_text(
        '<meta http-equiv="refresh" content="0; url=/reports/index.html"/>',
        encoding="utf-8",
    )
    return index


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))


def serve(server: ThreadingHTTPServer, host: str, port: int, open_browser: bool) -> None:
    shown_host = public_host(host)
    download_latest = f"http://{shown_host}:{port}/reports/ncins200_test_results_latest.zip"
    page = f"http://{shown_host}:{port}/reports/index.html"
    print()
    print("=" * 64)
    print("Сервер отчётов запущен")
    print(f"Порт:                  {port}")
    print(f"Страница:              {page}")
    print(f"Ссылка на скачивание:  {download_latest}")
    print("=" * 64)
    print("Остановка: Ctrl+C")
    print()
    if open_browser:
        try:
            webbrowser.open(page)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NCINS-200: запуск проверок и выдача ссылки на скачивание отчёта")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", help="Только unit-тесты")
    group.add_argument("--integration", action="store_true", help="Только integration-тесты")
    group.add_argument("--all", action="store_true", help="Все тесты (по умолчанию)")
    parser.add_argument("--host", default="127.0.0.1", help="Host HTTP-сервера отчётов")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Порт HTTP-сервера отчётов (0 = случайный свободный порт, по умолчанию)",
    )
    parser.add_argument("--no-serve", action="store_true", help="Только прогнать тесты, не поднимать сервер")
    parser.add_argument("--no-browser", action="store_true", help="Не открывать браузер")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    marker = "unit" if args.unit else "integration" if args.integration else None

    exit_code, html_report, junit_report = run_tests(marker)
    zip_path = build_download_bundle(html_report, junit_report, exit_code)

    server: ThreadingHTTPServer | None = None
    if args.no_serve:
        # Still resolve a display port for links in index.html when not serving.
        port = args.port if args.port and args.port > 0 else 0
    else:
        server, port = create_report_server(args.host, args.port)

    write_index_page(zip_path, html_report, exit_code, args.host, port or 0)

    shown_host = public_host(args.host)
    if port:
        download_latest = f"http://{shown_host}:{port}/reports/ncins200_test_results_latest.zip"
    else:
        download_latest = str(ARTIFACTS_DIR / "ncins200_test_results_latest.zip")
    artifact_latest = ARTIFACTS_DIR / "ncins200_test_results_latest.zip"

    print()
    print("Готово.")
    print(f"ZIP отчёт:             {zip_path}")
    print(f"Артефакт:              {artifact_latest}")
    if port:
        print(f"Порт отчёта:           {port}")
        print(f"Ссылка на скачивание:  {download_latest}")
    else:
        print(f"Скачать отчёт:         {artifact_latest}")
    print()

    if port:
        (REPORTS_DIR / "server_port.txt").write_text(str(port), encoding="utf-8")
        (ARTIFACTS_DIR / "ncins200_report_server_url.txt").write_text(
            f"{download_latest}\n",
            encoding="utf-8",
        )

    if args.no_serve or server is None:
        return 0 if exit_code == 0 else exit_code

    serve(server, args.host, port, open_browser=not args.no_browser)
    return 0 if exit_code == 0 else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
