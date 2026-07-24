#!/usr/bin/env python3
"""Tiny public-repo sanity checks with no third-party dependencies."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
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


class GitInspectionError(RuntimeError):
    """Raised when Git-aware inspection cannot produce a trustworthy result."""


def interesting_files(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield path, rel


def check_paths(root: Path, relative_paths) -> list[Finding]:
    findings: list[Finding] = []
    for rel in relative_paths:
        path = root / rel
        if not path.exists() and not path.is_symlink():
            continue
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


def check(root: Path) -> list[Finding]:
    return check_paths(root, (rel for _, rel in interesting_files(root)))


def run_git(root: Path, *args: str, allowed: tuple[int, ...] = (0,)):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        raise GitInspectionError("Git is unavailable") from exc
    if result.returncode not in allowed:
        command = " ".join(args)
        raise GitInspectionError(
            f"git {command} failed with exit status {result.returncode}"
        )
    return result


def require_exact_git_root(root: Path) -> None:
    result = run_git(root, "rev-parse", "--show-toplevel")
    top_level_text = os.fsdecode(result.stdout).rstrip("\r\n")
    if not top_level_text:
        raise GitInspectionError("Git returned no worktree root")
    try:
        top_level = Path(top_level_text).resolve()
    except OSError as exc:
        raise GitInspectionError("Git returned an unreadable worktree root") from exc
    if top_level != root:
        raise GitInspectionError(
            "target must be the exact Git worktree root, not a parent or subdirectory"
        )


def git_candidate_paths(root: Path) -> list[Path]:
    result = run_git(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    )
    candidates: list[Path] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(os.fsdecode(raw_path))
        if relative.is_absolute() or ".." in relative.parts:
            raise GitInspectionError("Git returned a path outside the worktree")
        candidates.append(relative)
    return sorted(set(candidates), key=lambda path: path.as_posix())


def is_github_noreply(email: str) -> bool:
    normalized = email.strip().lower()
    github_domain = "github" + ".com"
    return normalized == "noreply" + "@" + github_domain or normalized.endswith(
        "@" + "users.noreply." + github_domain
    )


def git_history_findings(root: Path) -> list[Finding]:
    head = run_git(root, "rev-parse", "--verify", "--quiet", "HEAD", allowed=(0, 1))
    if head.returncode == 1:
        return []

    result = run_git(root, "log", "-z", "--format=%H%x00%ae%x00%ce", "HEAD")
    fields = result.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 3:
        raise GitInspectionError("Git returned malformed commit identity data")

    findings: list[Finding] = []
    for index in range(0, len(fields), 3):
        commit = os.fsdecode(fields[index])
        author_email = os.fsdecode(fields[index + 1])
        committer_email = os.fsdecode(fields[index + 2])
        for role, email in (
            ("author", author_email),
            ("committer", committer_email),
        ):
            if not is_github_noreply(email):
                findings.append(
                    Finding(
                        Path("<git-history>"),
                        (
                            f"{role} email in commit {commit[:12]} is not a "
                            "GitHub noreply address; manual review required"
                        ),
                    )
                )
    return findings


def check_git_aware(root: Path) -> list[Finding]:
    require_exact_git_root(root)
    findings = check_paths(root, git_candidate_paths(root))
    findings.extend(git_history_findings(root))
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--git-aware",
        action="store_true",
        help="scan Git publication candidates and reachable commit identities",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        print("self-test passed")
        return 0

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    if args.git_aware:
        try:
            findings = check_git_aware(root)
        except GitInspectionError as exc:
            print(f"Git-aware inspection failed: {exc}", file=sys.stderr)
            return 2
    else:
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
