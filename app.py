#!/usr/bin/env python3
"""NCINS-200 — прогон метода расчёта страховой премии через requests + pytest.

Usage:
    python app.py
    python app.py --unit
    python app.py -v
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
ARTIFACTS_DIR = Path("/opt/cursor/artifacts")
CHECKLIST = ROOT / "CHECKLIST.md"
JUNIT_XML = REPORTS_DIR / "junit.xml"
TEXT_REPORT = REPORTS_DIR / "report.txt"


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    return logging.getLogger("ncins200")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NCINS-200: прогон API-метода calculate через pytest+requests")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--api", action="store_true", default=True, help="API-тесты метода (по умолчанию)")
    g.add_argument("--unit", action="store_true", help="Только unit-тесты без сети")
    g.add_argument("--all", action="store_true", help="unit + api")
    p.add_argument("-v", "--verbose", action="store_true", help="Подробный лог")
    p.add_argument(
        "--skip-if-offline",
        action="store_true",
        help="Пропускать API-тесты, если gateway недоступен (по умолчанию НЕ пропускаем — падаем с ошибкой сети)",
    )
    return p.parse_args()


class ReportPlugin:
    """Собирает результаты и пишет текстовый отчёт = CHECKLIST + статусы."""

    def __init__(self, log: logging.Logger):
        self.log = log
        self.rows: list[tuple[str, str, str]] = []  # nodeid, outcome, reason

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and not (report.when == "setup" and report.failed):
            return
        if report.when == "setup" and report.skipped:
            outcome = "SKIPPED"
            reason = str(report.longrepr) if report.longrepr else ""
        elif report.skipped:
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
        # берём последнюю строку с исключением — обычно самая полезная
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
            "NCINS-200 — отчёт прогона метода POST /v1/ins-premium/calculate",
            f"Время: {now}",
            f"Exit code: {exit_code}",
            f"Команда: python app.py",
            "",
            "=" * 72,
            "ЧЕК-ЛИСТ ПРОВЕРОК (из задачи / PDF)",
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
        artifact = ARTIFACTS_DIR / "ncins200_report.txt"
        artifact.write_text(text, encoding="utf-8")
        return TEXT_REPORT


def main() -> int:
    args = parse_args()
    log = setup_logging(args.verbose)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # API-тесты по умолчанию реально бьют в метод через requests
    if args.unit:
        marker = "unit"
        log.info("Режим: unit (без вызова API)")
    elif args.all:
        marker = "unit or integration"
        log.info("Режим: unit + api")
    else:
        marker = "integration"
        log.info("Режим: API-метод calculate через requests + pytest")

    if args.skip_if_offline:
        os.environ["SKIP_IF_OFFLINE"] = "1"
        log.info("SKIP_IF_OFFLINE=1 — при недоступном gateway тесты будут skipped")
    else:
        os.environ.pop("SKIP_IF_OFFLINE", None)
        os.environ["FORCE_INTEGRATION"] = "1"
        log.info("FORCE_INTEGRATION=1 — API-тесты не пропускаются из-за offline")

    log.info("BASE_URL / endpoint берутся из .env или defaults в config.py")
    log.info("Чек-лист проверок: %s", CHECKLIST)
    log.info("Старт pytest...")

    plugin = ReportPlugin(log)
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

    log.info("Готово. exit_code=%s", exit_code)
    log.info("Текстовый отчёт: %s", report_path)
    log.info("Артефакт: %s", ARTIFACTS_DIR / "ncins200_report.txt")
    log.info("JUnit XML: %s", JUNIT_XML)
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
