# Public Repo Safety Kit

Before you share a repository, check for files and text that may not belong
in public: a real `.env` file, an export of contacts, a symbolic link or a
value that looks like a credential. This small Python tool reports matches
for you to review locally. It needs no extra dependencies.

Use it as an extra check alongside a dedicated secret scanner and human
review. It does not make a publication decision or publish anything.

## Run

From this repository’s folder, use Python 3 and replace the example path with
the folder you intend to check. Git-aware mode also needs Git:

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

Read any findings before proceeding. A match needs investigation; it is not
a confirmed secret. A clean result means this guard found no matches in the
files and metadata it inspected, not that publication is safe.

<!-- toolkit-trust-card:placement -->

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

## What It Checks

- Real environment files such as `.env` and `.env.local`.
- Symbolic links (symlinks), which can point to files outside a repository.
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

## Related Tools

For checks beyond publication hygiene, try these related examples:
- [EvidenceGate](https://github.com/TheDarkniteFalls/evidencegate) records the
  evidence and checks behind an AI-assisted change.
- [Local Model Reliability Example](https://github.com/TheDarkniteFalls/local-model-reliability-example)
  validates structured model output and protected-path boundaries.
- [Context Boundary Examples](https://github.com/TheDarkniteFalls/context-boundary-examples)
  checks whether an answer stays inside supplied evidence.
- [Green-Spine QA Pattern](https://github.com/TheDarkniteFalls/green-spine-qa-pattern)
  puts checks for an important workflow behind one repeatable command.
- [Codex Project Instructions Starter](https://github.com/TheDarkniteFalls/codex-project-instructions-starter)
  gives coding agents clear project rules before they work.

## Public Data Notice

This repository uses synthetic examples only. Do not add credentials, personal
data, connector exports, private notes, or raw logs.

## Scope

Keep the result with your other pre-publication checks. The guard’s coverage
is limited to the rules above; dedicated secret scanning and human review
are still needed before publication.

## Quality Checks

```sh
python3 public_repo_guard.py --self-test
python3 -m unittest -v
python3 public_repo_guard.py .
python3 public_repo_guard.py --git-aware .
python3 public_repo_guard.py templates/public-repo
python3 -m py_compile public_repo_guard.py test_public_repo_guard.py
```
