# Public Repo Safety Kit

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
python3 public_repo_guard.py --self-test
```

The command exits `0` when no findings are present and `1` when manual review is
needed.

Example clean output:

```text
No public-repo guard findings.
```

## What It Checks

- Real environment files such as `.env` and `.env.local`.
- Symlinks, which can point outside a repository.
- Common private-key and token-looking strings.
- Raw export file names such as `email_export.json` or `contacts.csv`.

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
python3 public_repo_guard.py .
python3 public_repo_guard.py templates/public-repo
python3 -m py_compile public_repo_guard.py
```
