from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import public_repo_guard as guard


class GitAwareGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name).resolve()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Synthetic Reviewer")
        self.git(
            "config",
            "user.email",
            "12345+synthetic-reviewer"
            + "@"
            + "users.noreply."
            + "github"
            + ".com",
        )

    def git(self, *args: str, env=None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    def commit(self, filename: str, content: str, *, author=None, committer=None):
        (self.root / filename).write_text(content, encoding="utf-8")
        self.git("add", "--", filename)
        environment = os.environ.copy()
        if author:
            environment["GIT_AUTHOR_EMAIL"] = author
        if committer:
            environment["GIT_COMMITTER_EMAIL"] = committer
        self.git("commit", "--quiet", "-m", f"Add {filename}", env=environment)

    def test_ignored_local_file_is_excluded(self) -> None:
        self.commit(".gitignore", ".env\n")
        key_name = "API" + "_KEY"
        fake_value = "synthetic-" + "secret-value"
        (self.root / ".env").write_text(
            f"{key_name}={fake_value}\n", encoding="utf-8"
        )
        self.assertEqual(guard.check_git_aware(self.root), [])

    def test_tracked_and_nonignored_untracked_findings_are_scanned(self) -> None:
        (self.root / ".gitignore").write_text(".env\n", encoding="utf-8")
        self.git("add", "--", ".gitignore")
        key_name = "API" + "_KEY"
        fake_value = "synthetic-" + "secret-value"
        (self.root / ".env").write_text(
            f"{key_name}={fake_value}\n", encoding="utf-8"
        )
        self.git("add", "--force", "--", ".env")
        (self.root / "contacts.csv").write_text("name\nSynthetic User\n")
        reasons = {finding.reason for finding in guard.check_git_aware(self.root)}
        self.assertIn("real environment file should not be public", reasons)
        self.assertIn("possible assigned secret", reasons)
        self.assertIn("raw export-looking file should be replaced with a fixture", reasons)

    def test_symlink_is_a_manual_review_finding(self) -> None:
        target = self.root / "fixture.txt"
        target.write_text("synthetic\n", encoding="utf-8")
        try:
            (self.root / "linked.txt").symlink_to(target.name)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        findings = guard.check_git_aware(self.root)
        self.assertIn(
            guard.Finding(Path("linked.txt"), "symlink requires manual review"),
            findings,
        )

    def test_github_noreply_history_is_clean(self) -> None:
        self.commit("README.md", "# Synthetic fixture\n")
        history = [
            finding
            for finding in guard.check_git_aware(self.root)
            if finding.path == Path("<git-history>")
        ]
        self.assertEqual(history, [])

    def test_personal_email_in_reachable_history_is_flagged(self) -> None:
        personal_email = "synthetic" + "@" + "example.test"
        self.commit(
            "first.txt",
            "first\n",
            author=personal_email,
            committer=personal_email,
        )
        self.commit("second.txt", "second\n")
        reasons = [finding.reason for finding in guard.check_git_aware(self.root)]
        self.assertTrue(any("author email" in reason for reason in reasons))
        self.assertTrue(any("committer email" in reason for reason in reasons))
        self.assertTrue(all(personal_email not in reason for reason in reasons))

    def test_unborn_repository_has_no_history_failure(self) -> None:
        (self.root / "README.md").write_text("# Synthetic fixture\n")
        self.assertEqual(guard.check_git_aware(self.root), [])

    def test_invalid_target_and_subdirectory_return_exit_two(self) -> None:
        missing = self.root / "missing"
        self.assertEqual(guard.main(["--git-aware", str(missing)]), 2)
        subdirectory = self.root / "nested"
        subdirectory.mkdir()
        self.assertEqual(guard.main(["--git-aware", str(subdirectory)]), 2)

    def test_git_unavailable_returns_exit_two(self) -> None:
        with patch.object(guard.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(guard.main(["--git-aware", str(self.root)]), 2)


if __name__ == "__main__":
    unittest.main()
