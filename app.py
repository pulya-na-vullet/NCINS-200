#!/usr/bin/env python3
"""NCINS — тесты POST /v1/sign/create-operation + упаковка ZIP.

Usage:
    python app.py                 # API-тесты + ZIP артефакт
    python app.py --unit          # только unit
    python app.py --all           # unit + api
    python app.py --zip-only      # только собрать архив
    python app.py -v
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
DIST_DIR = ROOT / "dist"
ARTIFACTS_DIR = Path("/opt/cursor/artifacts")
CHECKLIST = ROOT / "CHECKLIST.md"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
JUNIT_XML = REPORTS_DIR / "junit.xml"
TEXT_REPORT = REPORTS_DIR / "report.txt"

# При python app.py всегда выставляем UMP TEST credentials
DEFAULT_ENV_VALUES = {
    "ENV": "test",
    "KEYCLOAK_CLIENT_ID": "nib-corp-ncins",
    "KEYCLOAK_CLIENT_SECRET": "wcpWehuLXKRWwMYE17EXvg9ShCQ7Rovc",
    "KEYCLOAK_TOKEN_URL": (
        "https://idp-api-test.alfaintra.net/auth/realms/ump/protocol/openid-connect/token"
    ),
    "KEYCLOAK_VERIFY_SSL": "0",
    "FETCH_KEYCLOAK_TOKEN": "1",
    "API_VERIFY_SSL": "0",
}

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
EXCLUDE_FILE_NAMES = {".env", "index.html"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pdf"}


class _PrintHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            print(self.format(record), flush=True)
        except Exception:
            pass


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(REPORTS_DIR / "run.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    console = _PrintHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    return logging.getLogger("ncins.sign")


def ensure_env_file(log: logging.Logger) -> Path:
    """Создать/обновить .env: cp .env.example .env + UMP TEST credentials."""
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
            log.info("Создан .env из .env.example")
        else:
            ENV_FILE.write_text("", encoding="utf-8")
            log.info("Создан пустой .env (.env.example не найден)")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    updated: dict[str, str] = {}
    new_lines: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key in DEFAULT_ENV_VALUES:
            new_value = DEFAULT_ENV_VALUES[key]
            if value.strip() != new_value:
                updated[key] = new_value
            new_lines.append(f"{key}={new_value}")
            seen.add(key)
            os.environ[key] = new_value
        else:
            new_lines.append(line)
            os.environ.setdefault(key, value.strip())

    for key, value in DEFAULT_ENV_VALUES.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")
            updated[key] = value
        os.environ[key] = value

    ENV_FILE.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    if updated:
        log.info("Обновлены ключи в .env: %s", ", ".join(sorted(updated)))
    else:
        log.info(".env уже содержит нужные UMP TEST credentials")

    log.info(
        "Keycloak: ENV=%s client_id=%s token_url=%s",
        os.environ.get("ENV"),
        os.environ.get("KEYCLOAK_CLIENT_ID"),
        os.environ.get("KEYCLOAK_TOKEN_URL"),
    )
    return ENV_FILE


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="NCINS: run create-operation tests and build ZIP artifact"
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--api", action="store_true", default=True, help="API-тесты метода (по умолчанию)")
    g.add_argument("--unit", action="store_true", help="Только unit-тесты без сети")
    g.add_argument("--all", action="store_true", help="unit + api")
    g.add_argument("--zip-only", action="store_true", help="Только собрать ZIP, без pytest")
    p.add_argument("-v", "--verbose", action="store_true", help="Подробный лог")
    p.add_argument(
        "--skip-if-offline",
        action="store_true",
        help="Пропускать API-тесты, если gateway недоступен",
    )
    p.add_argument("--no-zip", action="store_true", help="Не собирать ZIP")
    return p.parse_args()


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
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_name = f"ncins_sign_create_operation_tests_{stamp}.zip"
    zip_path = DIST_DIR / zip_name
    latest = DIST_DIR / "ncins_sign_create_operation_tests_latest.zip"
    root_prefix = "ncins-sign-create-operation-tests"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or _should_skip(path):
                continue
            arcname = f"{root_prefix}/{path.relative_to(ROOT).as_posix()}"
            archive.write(path, arcname=arcname)

        archive.writestr(
            f"{root_prefix}/HOW_TO_RUN.txt",
            (
                "NCINS — POST /v1/sign/create-operation\n"
                "=====================================\n\n"
                "1) pip install -r requirements.txt\n"
                "2) cp .env.example .env\n"
                "3) python app.py --unit          # без VPN\n"
                "4) python app.py                 # API-тесты (нужен корп VPN)\n"
                "5) python app.py --zip-only      # только архив\n"
            ),
        )

    shutil.copyfile(zip_path, latest)
    shutil.copyfile(zip_path, ARTIFACTS_DIR / zip_name)
    shutil.copyfile(latest, ARTIFACTS_DIR / "ncins_sign_create_operation_tests_latest.zip")

    meta = {
        "method": "POST /v1/sign/create-operation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_zip": zip_name,
        "how_to_run": [
            "pip install -r requirements.txt",
            "cp .env.example .env",
            "python app.py",
        ],
    }
    (DIST_DIR / "project_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.copyfile(
        DIST_DIR / "project_meta.json",
        ARTIFACTS_DIR / "ncins_sign_create_operation_meta.json",
    )
    return latest


class ReportPlugin:
    def __init__(self, log: logging.Logger):
        self.log = log
        self.rows: list[tuple[str, str, str]] = []

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and not (report.when == "setup" and report.failed):
            return
        if report.skipped:
            outcome = "SKIPPED"
            reason = str(report.longrepr) if report.longrepr else ""
        elif report.failed:
            outcome = "FAILED"
            reason = str(report.longrepr) if report.longrepr else ""
        elif report.passed and report.when == "call":
            outcome = "PASSED"
            reason = ""
        else:
            return

        short = report.nodeid.split("::")[-1]
        reason = self._short_reason(reason)
        self.rows.append((short, outcome, reason))
        level = {
            "PASSED": logging.INFO,
            "FAILED": logging.ERROR,
            "SKIPPED": logging.WARNING,
        }[outcome]
        self.log.log(level, "[%s] %s", outcome, short)
        if reason and outcome != "PASSED":
            self.log.log(level, "  └─ %s", reason[:300])

    @staticmethod
    def _short_reason(reason: str) -> str:
        text = (reason or "").strip()
        if not text:
            return ""
        lower = text.lower()
        if "nameresolutionerror" in lower or "failed to resolve" in lower or "name resolution" in lower:
            return "Нет доступа к corp-gateway-test (DNS/VPN). Нужен корп VPN."
        if "connectionerror" in lower or "connect timeout" in lower or "timed out" in lower:
            return "Нет соединения с gateway (сеть/VPN/timeout)."
        for line in reversed(text.splitlines()):
            s = line.strip()
            if s.startswith("E ") or "Error" in s or "assert" in s:
                return s[:400]
        return text.splitlines()[0][:400]

    def write_text_report(self, exit_code: int) -> Path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        checklist = CHECKLIST.read_text(encoding="utf-8") if CHECKLIST.exists() else ""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "NCINS — отчёт прогона метода POST /v1/sign/create-operation",
            f"Время: {now}",
            f"Exit code: {exit_code}",
            "Команда: python app.py",
            "",
            "=" * 72,
            "ЧЕК-ЛИСТ ПРОВЕРОК",
            "=" * 72,
            "",
            checklist.strip(),
            "",
            "=" * 72,
            "РЕЗУЛЬТАТЫ ПРОГОНА",
            "=" * 72,
            "",
        ]
        if not self.rows:
            lines.append("Тесты не запускались / результатов нет.")
        for i, (name, outcome, reason) in enumerate(self.rows, 1):
            lines.append(f"{i}. [{outcome}] {name}")
            if reason and outcome != "PASSED":
                for rl in reason.strip().splitlines()[:8]:
                    lines.append(f"    {rl}")
            lines.append("")

        passed = sum(1 for _, o, _ in self.rows if o == "PASSED")
        failed = sum(1 for _, o, _ in self.rows if o == "FAILED")
        skipped = sum(1 for _, o, _ in self.rows if o == "SKIPPED")
        lines.extend(
            [
                "-" * 72,
                f"Итого: PASSED={passed} FAILED={failed} SKIPPED={skipped} TOTAL={len(self.rows)}",
                "-" * 72,
                "",
            ]
        )
        text = "\n".join(lines)
        TEXT_REPORT.write_text(text, encoding="utf-8")
        (ARTIFACTS_DIR / "ncins_sign_create_operation_report.txt").write_text(text, encoding="utf-8")
        return TEXT_REPORT


def main() -> int:
    args = parse_args()
    log = setup_logging(args.verbose)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Всегда: cp .env.example .env (если нет) + прописать UMP TEST credentials
    ensure_env_file(log)

    exit_code = 0
    plugin = ReportPlugin(log)

    if not args.zip_only:
        if args.unit:
            marker = "unit"
            log.info("Режим: unit (без вызова API)")
        elif args.all:
            marker = "unit or integration"
            log.info("Режим: unit + api")
        else:
            marker = "integration"
            log.info("Режим: API-метод create-operation через requests + pytest")

        if args.skip_if_offline:
            os.environ["SKIP_IF_OFFLINE"] = "1"
            log.info("SKIP_IF_OFFLINE=1 — при недоступном gateway тесты будут skipped")
        else:
            os.environ.pop("SKIP_IF_OFFLINE", None)
            os.environ["FORCE_INTEGRATION"] = "1"
            log.info("FORCE_INTEGRATION=1 — API-тесты не пропускаются из-за offline")

        log.info("Чек-лист: %s", CHECKLIST)
        log.info("Старт pytest...")

        pytest_args = [
            "-v",
            "--tb=short",
            "-m",
            marker,
            f"--junitxml={JUNIT_XML}",
            str(ROOT / "tests"),
        ]
        if args.verbose:
            pytest_args.append("-vv")

        exit_code = pytest.main(pytest_args, plugins=[plugin])
        report_path = plugin.write_text_report(exit_code)
        log.info("Текстовый отчёт: %s", report_path)
        log.info("JUnit XML: %s", JUNIT_XML)

    zip_path = None
    if not args.no_zip:
        zip_path = build_project_zip()
        log.info("ZIP проекта: %s", zip_path)
        log.info("Артефакт ZIP: %s", ARTIFACTS_DIR / "ncins_sign_create_operation_tests_latest.zip")

    log.info("Готово. exit_code=%s", exit_code)
    if zip_path:
        print(f"\nАрхив для задачи: {zip_path}", flush=True)
        print(
            f"Артефакт: {ARTIFACTS_DIR / 'ncins_sign_create_operation_tests_latest.zip'}",
            flush=True,
        )
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
