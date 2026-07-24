# Public Repo Safety Kit

<!-- toolkit-trust-card:start -->
> **Public contract:** Stable tool · about 5 min · Python 3; Git for repository checks · no model · no network
>
> **Operation:** Read-only check; examples may use temporary files
>
> **A pass establishes:** The ordinary scan checks the supplied tree; Git-aware mode checks tracked and nonignored untracked candidates plus reachable commit author and committer email identities.
>
> **It does not establish:** It does not scan historical file contents, replace a dedicated secret scanner or manual review, or grant permission to publish.
>
> **First check:** `python3 public_repo_guard.py --self-test`
<!-- toolkit-trust-card:end -->

Small, dependency-free checks for repositories that are about to be made public.

This project is for people who want one extra local sanity check before pushing
a repo into public view.

This is not a secret scanner replacement. It is a lightweight guard for the
boring mistakes that often happen before publishing: real `.env` files,
symlinks, private-key material, obvious token strings, and raw export-style
files.

## Why It Exists

Public repos often leak boring things: a real `.env`, a private export file, a
symlink to somewhere outside the repo, or a token-looking value in a fixture.
This guard catches those cases early and prints reviewable findings.

## Run

```sh
python3 public_repo_guard.py /path/to/public-candidate-repo
python3 public_repo_guard.py --git-aware /path/to/public-candidate-repo
python3 public_repo_guard.py --self-test
python3 -m unittest -v
```

The command exits `0` when no findings are present, `1` when manual review is
needed, and `2` when the target is invalid or a required inspection fails.

Example clean output:

```text
No public-repo guard findings.
```

## What It Checks

- Real environment files such as `.env` and `.env.local`.
- Symlinks, which can point outside a repository.
- Common private-key and token-looking strings.
- Raw export file names such as `email_export.json` or `contacts.csv`.

With `--git-aware`, the supplied path must be the exact Git worktree root. The
guard asks Git for tracked files and nonignored untracked files, then applies
the same environment-file, export-name, size, symlink, and credential-pattern
checks to those publication candidates. Ignored local files are excluded;
files already tracked by Git remain candidates even if a current ignore rule
matches them.

Git-aware mode also inspects the author and committer email metadata of every
commit reachable from `HEAD`. Any address other than a GitHub noreply address
is reported for manual review. An unborn repository has no commit identities
to inspect and is still scanned for publication candidates.

## Deliberate Limits

This guard does not inspect historical file contents. It does not replace
Gitleaks, TruffleHog, a security review, or a human review of what the project
reveals. A clean result is evidence for review; it never grants permission to
publish.

## Public-Safe Repo Template

`templates/public-repo/` is a copyable starter for small public repos:

- `README.template.md`
- `SECURITY.md`
- `.gitignore`
- `.github/workflows/checks.yml`
- `PUBLICATION_CHECKLIST.md`

Use it before adding real project files, then replace the placeholder command
with the smallest useful check for that repo.

## How These Fit Together

Public Repo Safety Kit is one piece of a small public toolkit:

- Public Repo Safety Kit checks a public-candidate repo before publishing.
- [EvidenceGate](https://github.com/TheDarkniteFalls/evidencegate) records the
  evidence and checks behind an AI-assisted change.
- [Local Model Reliability Example](https://github.com/TheDarkniteFalls/local-model-reliability-example)
  validates structured model output and protected-path boundaries before
  trusting it.
- [Context Boundary Examples](https://github.com/TheDarkniteFalls/context-boundary-examples)
  checks whether an answer stays inside supplied evidence.
- [Green-Spine QA Pattern](https://github.com/TheDarkniteFalls/green-spine-qa-pattern)
  bundles the important path behind one repeatable command.
- [Codex Project Instructions Starter](https://github.com/TheDarkniteFalls/codex-project-instructions-starter)
  gives coding agents clear project rules before they work.

## Public Data Notice

This repository uses synthetic examples only. Do not add credentials, personal
data, connector exports, private notes, or raw logs.

## Scope

The goal is a small pre-publish sanity check. Use a real secret scanner and
manual review before publishing anything important.

## Quality Checks

```sh
python3 public_repo_guard.py --self-test
python3 -m unittest -v
python3 public_repo_guard.py .
python3 public_repo_guard.py --git-aware .
python3 public_repo_guard.py templates/public-repo
python3 -m py_compile public_repo_guard.py test_public_repo_guard.py
```
