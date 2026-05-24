# Fork Divergence Log

> This document tracks the divergence between Hermes Maestro and the upstream
> AI Maestro project (https://github.com/23blocks-OS/ai-maestro).

---

## Overview

Hermes Maestro is a hard fork of AI Maestro by 23blocks. The fork was created
to pursue an independent development direction while preserving full attribution
to the original authors. This document serves as the canonical record of all
changes made post-fork and the procedure for upstream synchronization.

**Fork date:** 2026-05-24
**Fork point:** `23blocks-OS/ai-maestro` main branch
**Upstream license:** MIT (see `LICENSE.upstream`)
**Fork license:** MIT (dual-licensed, see `LICENSE`)

---

## Renaming

| Original | Fork |
|----------|------|
| AI Maestro | Hermes Maestro |
| `ai-maestro` (package name) | `hermes-maestro` |
| `23blocks-OS/ai-maestro` (repo) | `valapati414/ai-maestro` (repo) |

Additional renames will be tracked here as they are applied (e.g., binary names,
CLI commands, configuration directories, environment variables).

---

## New Files Added

| File | Purpose |
|------|---------|
| `LICENSE.upstream` | Verbatim copy of the original MIT license |
| `docs/FORK_DIVERGENCE.md` | This document — fork change tracking |

---

## Modified Files

| File | Change |
|------|--------|
| `LICENSE` | Added fork copyright section (dual-licensed MIT) |
| `README.md` | Fork attribution, renamed to Hermes Maestro, updated links |
| `package.json` | `name` field changed from `ai-maestro` to `hermes-maestro` |

---

## Upstream Sync Procedure

1. Add upstream remote (if not already present):
   ```bash
   git remote add upstream https://github.com/23blocks-OS/ai-maestro.git
   ```

2. Fetch upstream changes:
   ```bash
   git fetch upstream
   ```

3. Merge upstream into a dedicated branch for review:
   ```bash
   git checkout -b upstream-sync upstream/main
   ```

4. Resolve conflicts manually — see [Conflict-Prone Files](#conflict-prone-files) below.

5. After resolving, merge into `main`:
   ```bash
   git checkout main
   git merge upstream-sync
   ```

6. Update this document with any new divergence points.

---

## Conflict-Prone Files

These files are most likely to conflict during upstream sync due to fork-specific
modifications:

| File | Why it conflicts |
|------|-----------------|
| `LICENSE` | Fork copyright section added below original text |
| `README.md` | Extensive fork attribution and renamed branding |
| `package.json` | `name` field changed to `hermes-maestro` |
| `docs/FORK_DIVERGENCE.md` | Fork-only file, does not exist upstream |

> **Note:** This list should be updated whenever fork-specific changes are made
> to additional files.
