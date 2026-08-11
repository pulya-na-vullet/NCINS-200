#!/usr/bin/env python3
"""NCINS-200 — упаковка проекта и локальная ссылка на скачивание.

Usage:
    python app.py
    python app.py --test --unit
    python app.py --port 0
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
DIST_DIR = ROOT / "dist"
ARTIFACTS_DIR = Path("/opt/cursor/artifacts")
DEFAULT_PORT = 0

# What not to put into the project archive
EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "reports",
    "dist",
    ".idea",
    ".vscode",
    "node_modules",
}
EXCLUDE_FILE_NAMES = {
    ".env",
    "index.html",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

GITHUB_BRANCH_ZIP = (
    "https://github.com/pulya-na-vullet/NCINS-200/archive/refs/heads/"
    "cursor/ncins-200-ins-premium-tests-0f4d.zip"
)
GITHUB_MAIN_ZIP = "https://github.com/pulya-na-vullet/NCINS-200/archive/refs/heads/main.zip"


def _ensure_dirs() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def public_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::"} else host


def _should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDE_DIR_NAMES for part in rel_parts):
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def build_project_zip() -> Path:
    """Pack the whole runnable project (with app.py) into a ZIP."""
    _ensure_dirs()
    stamp = _timestamp()
    zip_name = f"NCINS-200_project_{stamp}.zip"
    zip_path = DIST_DIR / zip_name
    latest = DIST_DIR / "NCINS-200_project_latest.zip"
    root_prefix = "NCINS-200"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or _should_skip(path):
                continue
            arcname = f"{root_prefix}/{path.relative_to(ROOT).as_posix()}"
            archive.write(path, arcname=arcname)

        readme_run = (
            "NCINS-200\n"
            "=========\n\n"
            "1) pip install -r requirements.txt\n"
            "2) cp .env.example .env   # укажите BASE_URL и A-* headers из корп-сети\n"
            "3) python app.py          # соберёт ZIP проекта и поднимет ссылку на скачивание\n"
            "4) python app.py --test --unit\n"
            "5) python app.py --test --integration   # нужен корп VPN / доступ к gateway\n"
        )
        archive.writestr(f"{root_prefix}/HOW_TO_RUN.txt", readme_run)

    shutil.copyfile(zip_path, latest)
    shutil.copyfile(zip_path, ARTIFACTS_DIR / zip_name)
    shutil.copyfile(latest, ARTIFACTS_DIR / "NCINS-200_project_latest.zip")

    meta = {
        "task": "NCINS-200",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_zip": zip_name,
        "how_to_run": ["pip install -r requirements.txt", "python app.py"],
        "github_branch_zip": GITHUB_BRANCH_ZIP,
        "note": "Integration API tests require corporate VPN / internal gateway access.",
    }
    (DIST_DIR / "project_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copyfile(DIST_DIR / "project_meta.json", ARTIFACTS_DIR / "NCINS-200_project_meta.json")
    return latest


def run_tests(marker: str | None) -> int:
    cmd = [sys.executable, "-m", "pytest", "-v"]
    if marker:
        cmd.extend(["-m", marker])
    print("Запуск тестов:", flush=True)
    print(" ", " ".join(cmd), flush=True)
    print(flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))


def create_server(host: str, port: int) -> tuple[ThreadingHTTPServer, int]:
    requested = port if port and port > 0 else 0
    server = ThreadingHTTPServer((host, requested), QuietHandler)
    return server, int(server.server_address[1])


def write_index_page(project_zip: Path, host: str, port: int) -> Path:
    shown = public_host(host)
    local_url = f"http://{shown}:{port}/dist/{quote(project_zip.name)}"
    index = DIST_DIR / "index.html"
    index.write_text(
        f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <title>NCINS-200 — скачать проект</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; margin: 40px; background: linear-gradient(160deg,#e7f0ea,#f7f3ec); color: #14201a; }}
    .box {{ max-width: 760px; background: rgba(255,255,255,.92); border: 1px solid #c9d5ce; padding: 28px 32px; }}
    h1 {{ margin-top: 0; }}
    a.btn {{ display: inline-block; margin: 8px 12px 8px 0; padding: 12px 18px; background: #0f5c45; color: #fff; text-decoration: none; }}
    a.btn.secondary {{ background: #2c3e36; }}
    code {{ background: #eef2ef; padding: 2px 6px; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>NCINS-200 — весь проект</h1>
    <p>В архиве есть <code>app.py</code>, тесты, клиент API и <code>requirements.txt</code>.</p>
    <p>После распаковки:</p>
    <pre>pip install -r requirements.txt
cp .env.example .env
python app.py</pre>
    <p>
      <a class="btn" href="/dist/{quote(project_zip.name)}">Скачать проект (ZIP)</a>
      <a class="btn secondary" href="{GITHUB_BRANCH_ZIP}">Скачать с GitHub</a>
    </p>
    <p>Локальная ссылка: <a href="{local_url}">{local_url}</a></p>
    <p>GitHub: <a href="{GITHUB_BRANCH_ZIP}">{GITHUB_BRANCH_ZIP}</a></p>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    (ROOT / "index.html").write_text(
        '<meta http-equiv="refresh" content="0; url=/dist/index.html"/>',
        encoding="utf-8",
    )
    return index


def serve(server: ThreadingHTTPServer, host: str, port: int, open_browser: bool) -> None:
    shown = public_host(host)
    download = f"http://{shown}:{port}/dist/NCINS-200_project_latest.zip"
    page = f"http://{shown}:{port}/dist/index.html"
    print()
    print("=" * 64)
    print("Сервер скачивания проекта запущен")
    print(f"Порт:                       {port}")
    print(f"Страница:                   {page}")
    print(f"Скачать проект:             {download}")
    print(f"Скачать с GitHub:           {GITHUB_BRANCH_ZIP}")
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
    parser = argparse.ArgumentParser(
        description="NCINS-200: упаковать проект и выдать ссылку на скачивание"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host HTTP-сервера")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Порт (0 = случайный свободный)",
    )
    parser.add_argument("--no-serve", action="store_true", help="Только собрать ZIP, без HTTP")
    parser.add_argument("--no-browser", action="store_true", help="Не открывать браузер")
    parser.add_argument("--test", action="store_true", help="Дополнительно прогнать pytest")
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="С --test: только unit")
    test_group.add_argument("--integration", action="store_true", help="С --test: только integration (нужен VPN)")
    test_group.add_argument("--all-tests", action="store_true", help="С --test: все тесты")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    project_zip = build_project_zip()
    print(f"Проект упакован: {project_zip}", flush=True)

    exit_code = 0
    if args.test:
        marker = None
        if args.unit:
            marker = "unit"
        elif args.integration:
            marker = "integration"
        exit_code = run_tests(marker)

    server: ThreadingHTTPServer | None = None
    port = 0
    if not args.no_serve:
        server, port = create_server(args.host, args.port)
        write_index_page(project_zip, args.host, port)
    else:
        write_index_page(project_zip, args.host, 0)

    shown = public_host(args.host)
    local_download = (
        f"http://{shown}:{port}/dist/NCINS-200_project_latest.zip" if port else str(project_zip)
    )

    print()
    print("Готово.")
    print(f"ZIP проекта:               {project_zip}")
    print(f"Артефакт:                  {ARTIFACTS_DIR / 'NCINS-200_project_latest.zip'}")
    print(f"Скачать проект (локально): {local_download}")
    print(f"Скачать проект (GitHub):   {GITHUB_BRANCH_ZIP}")
    print()

    (DIST_DIR / "download_url.txt").write_text(
        f"{local_download}\n{GITHUB_BRANCH_ZIP}\n",
        encoding="utf-8",
    )
    (ARTIFACTS_DIR / "NCINS-200_download_url.txt").write_text(
        f"{local_download}\n{GITHUB_BRANCH_ZIP}\n",
        encoding="utf-8",
    )
    if port:
        (DIST_DIR / "server_port.txt").write_text(str(port), encoding="utf-8")

    if args.no_serve or server is None:
        return exit_code

    serve(server, args.host, port, open_browser=not args.no_browser)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
