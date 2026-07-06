#!/usr/bin/env python3
"""Tiny public-repo sanity checks with no third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "__pycache__", "node_modules", "dist", "build"}
SAFE_ENV_NAMES = {".env.example", ".env.sample", ".env.template"}
RAW_EXPORT_NAMES = {"email_export.json", "calendar_export.json", "contacts.csv", "raw_logs.txt"}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("openai key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "assigned secret",
        re.compile(
            r"(?i)\b(password|secret|api[_-]?key|token)\s*=\s*"
            r"['\"]?(?!changeme|example|placeholder|redacted|your_)[^\s'\"]{8,}"
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    reason: str


def interesting_files(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield path, rel


def check(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path, rel in interesting_files(root):
        if path.is_symlink():
            findings.append(Finding(rel, "symlink requires manual review"))
            continue
        if not path.is_file():
            continue
        if path.name.startswith(".env") and path.name not in SAFE_ENV_NAMES:
            findings.append(Finding(rel, "real environment file should not be public"))
        if path.name in RAW_EXPORT_NAMES:
            findings.append(Finding(rel, "raw export-looking file should be replaced with a fixture"))
        if path.stat().st_size > 1_000_000:
            findings.append(Finding(rel, "large file requires manual review"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(Finding(rel, f"possible {label}"))
    return findings


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Safe fixture\n", encoding="utf-8")
        assert check(root) == []
        key_name = "API" + "_KEY"
        fake_value = "super" + "-secret-value"
        (root / ".env").write_text(f"{key_name}={fake_value}\n", encoding="utf-8")
        reasons = {finding.reason for finding in check(root)}
        assert "real environment file should not be public" in reasons
        assert "possible assigned secret" in reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("self-test passed")
        return 0

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    findings = check(root)
    if not findings:
        print("No public-repo guard findings.")
        return 0
    print("Public-repo guard findings:")
    for finding in findings:
        print(f"- {finding.path}: {finding.reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
