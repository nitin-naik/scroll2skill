# Splitting the moment.js → date-fns migration across Claude Code sessions

Split this into five pieces. First, a read-only scan maps where moment is used and where timezones are at risk. Next, you and the main session agree on one date helper module. Then the 40 files get migrated in a few parallel worktrees. Timezone bugs are fixed on their own branch, so the "same behaviour" diffs stay apart from the "changed behaviour" diffs. A fresh reviewer checks each branch before it merges.

Cost check: parallel sessions use several times more tokens than a single session. 40 files is more than "a few turns", so splitting is worth it. Keep it to about three migration worktrees, not one per file.

## 1. Split

| # | Piece | Mode | Why |
|---|---|---|---|
| 1 | Inventory moment usage and timezone risk spots | **Subagent** (read-only) | A wide search over about 40 files. You only need the summary, not the file contents in your main thread. |
| 2 | Choose the helper API (`src/lib/dates.ts`) and the timezone approach, then build it with tests | **Main session** | Needs your decisions and the inventory you just discussed. Every later piece depends on it. |
| 3 | Migrate call sites, in groups by directory (e.g. A: `components/`, B: `pages/`+`hooks/`, C: `api/`+`utils/`+rest) | **Parallel sessions, one git worktree each** | Independent, and each touches different files, so nothing collides. Each gets its own branch and PR. |
| 4 | Fix the timezone bugs from the inventory | **Worktree session** (its own branch, after #3 merges) | These change behaviour. Keep them out of the migration diffs so a regression can be traced to one or the other. |
| 5 | Update the developer docs | **Subagent** (edits only `docs/`, on its own branch) | Small and self-contained. Its input is the merged helper API. |
| R | Review each branch before merge | **Reviewer subagent, fresh context** | It judges the diff without your session's assumptions. |

Starting a worktree session: `claude --worktree dates-components` (check that the flag exists with `claude --help`). Or run `git worktree add ../dates-components -b chore/date-fns-components` and start `claude` in that folder.

## 2. Prompts

Every prompt restates your CLAUDE.md rules. Subagents normally load CLAUDE.md, but the built-in **Explore** and **Plan** agents don't. A prompt you paste into a new session also doesn't carry anything from this conversation.

### Piece 1: inventory subagent (in the main session)

> Use a general-purpose subagent (not Explore, because Explore skips CLAUDE.md) with this prompt:

```
Goal: Produce an inventory of every moment.js usage in this React app and every spot with a likely
timezone bug, so we can plan a migration to date-fns. This is input for a migration plan; accuracy
of file:line matters more than prose.

Already known: about 40 files import moment. We are moving to date-fns. Nothing has been changed yet.

Rules (from CLAUDE.md, restated):
- Use pnpm for any command (never npm/yarn).
- Never commit to main. (You will not commit at all; this is read-only.)
- Dates must be stored and sent as UTC ISO strings. Treat any violation as a timezone bug.

Scope: READ-ONLY. Do not edit, install, or commit anything. Search all of src/ plus package.json
and any test/setup files. Include moment-timezone and moment plugins if present.

What to find:
1. Every import/require of moment, moment-timezone, or moment plugins.
2. Every moment API used (format, add/subtract, diff, startOf/endOf, isBefore/isAfter, utc(),
   tz(), locale(), duration, parsing with format strings, moment() with no args).
3. Timezone risks: dates sent to the API or stored that are not UTC ISO (e.g. format() without
   .utc(), toString(), local-format strings in payloads); parsing date-only strings ("2024-05-01")
   which become local midnight; startOf('day') on server dates; new Date(string) with non-ISO
   input; comparisons that mix local and UTC; hard-coded offsets; DST-sensitive add(1,'day').
4. Global moment config (locale, default timezone) and test setup that mocks time or TZ.

Done when every moment import is accounted for.
Return format (short, no file dumps):
- Table A: file:line | moment API(s) used | suggested date-fns equivalent | notes
- Table B: file:line | timezone risk | why it is a bug under the "UTC ISO" rule | severity (high/med/low)
- List of distinct moment APIs used, with counts
- Suggested grouping of files into 3 groups of roughly equal size with no overlapping files
- Anything you could not determine
```

### Piece 3: migration worker (paste into each worktree session, changing GROUP)

```
Goal: Replace moment.js with date-fns in the files listed below, with no change in behaviour.
This is one of three parallel branches; others are migrating other files at the same time.

Already known / decided:
- The shared helper module is src/lib/dates.ts (already merged on main; pull it first). Use its
  functions for parsing, formatting, and serialising. Do not add new helpers; if you need one, stop
  and list it in your report instead.
- Timezone bugs are being fixed separately on another branch. Do NOT fix timezone bugs here, even
  obvious ones. Keep current behaviour, and list every one you notice in your report.
- Inventory for your files (paste the Table A rows for this group here).

Rules (from CLAUDE.md, restated):
- Use pnpm only (pnpm install, pnpm test, pnpm lint, pnpm build). Never npm or yarn.
- Never commit to main. Work on branch chore/date-fns-<GROUP> and open a PR to main.
- Dates must be stored and sent as UTC ISO strings. Anything going to the API or to storage must
  go through the helper's UTC ISO serialiser.

Scope: Edit ONLY these files and their tests: <GROUP FILE LIST>. Do not touch package.json,
src/lib/dates.ts, docs/, or files outside the list. Do not remove the moment dependency (that
happens after all branches merge).

Done when:
- No moment import remains in your files (grep confirms).
- pnpm lint, pnpm test, and pnpm build pass.
- Work is committed to your branch and a PR is opened.
Return format (short): PR link; table of file | moment calls replaced | notes; list of timezone
issues noticed but not fixed (file:line + one line each); any helper you needed but didn't add.
No file dumps.
```

### Piece 4: timezone-fix session (worktree, after every migration PR has merged)

```
Goal: Fix the timezone bugs found during the moment → date-fns migration so that all dates are
stored and sent as UTC ISO strings and shown correctly in the user's local time.

Already known:
- Migration is done; moment is gone and all date code goes through src/lib/dates.ts.
- Bug list: (paste Table B from the inventory plus the "noticed but not fixed" lists from each
  migration PR).
- Decision on display timezone: (state yours, e.g. "show in the browser's local zone").

Rules (from CLAUDE.md, restated):
- pnpm only.
- Never commit to main. Branch fix/date-timezones, PR to main.
- Dates must be stored and sent as UTC ISO strings. This is the rule you are enforcing.

Scope: Edit the files in the bug list, src/lib/dates.ts if a helper is wrong, and their tests.
Nothing else. For each bug, first write a failing test that reproduces it (run the suite under a
non-UTC TZ, e.g. TZ=America/New_York pnpm test, and also under TZ=UTC), then fix it.

Done when: every listed bug has a test that fails before and passes after; pnpm test passes under
both TZ=UTC and a non-UTC TZ; pnpm lint and pnpm build pass; PR opened.
Return format: PR link; table of bug | file:line | test name | fix in one line; any bug you judged
not a bug, with the reason.
```

### Piece 5: docs subagent (after piece 4 merges)

```
Goal: Update the developer docs so they describe date handling with date-fns and the UTC ISO rule,
and no longer mention moment.

Already known: moment has been fully removed. The public API is src/lib/dates.ts (read it; it is
the source of truth). Timezone fixes have merged.

Rules (from CLAUDE.md, restated): pnpm only in any command shown in the docs; never commit to main
(branch docs/date-fns, PR to main); dates are stored and sent as UTC ISO strings, so state this
rule clearly in the docs.

Scope: Edit only docs/ (and README.md sections about dates, if any). Do not change source code.

Done when: grep finds no "moment" in docs/; there is a short "Working with dates" section covering
the helper functions, the UTC ISO rule with a correct and an incorrect example, and how to run the
tests under a non-UTC TZ; code examples match the actual helper signatures; PR opened.
Return format: PR link; list of files changed with one line each; anything in the docs you couldn't
verify against the code.
```

### Review (before merging each PR, in the main session)

Run the `date-migration-reviewer` agent below on each branch: "Review the diff of branch <branch> against main. Done condition: <paste that piece's done-when>."

## 3. Agent files

`.claude/agents/date-migration-reviewer.md`

```markdown
---
name: date-migration-reviewer
description: Use to review a branch of the moment.js → date-fns migration or the timezone fixes before it is merged.
tools: Read, Grep, Glob, Bash
---
## What to check
- No remaining imports of moment, moment-timezone, or moment plugins in changed files.
- Each replacement keeps the same behaviour: format tokens translated correctly (moment `YYYY`/`DD` vs date-fns `yyyy`/`dd`), month/day arithmetic, start/end of day/week (week start locale), inclusive/exclusive diffs, invalid-date handling (moment returns an "Invalid date" string; date-fns throws or returns Invalid Date).
- Every date sent to the API or stored is a UTC ISO string produced by the helper in src/lib/dates.ts.
- Date-only strings are not parsed as local midnight by accident; no new Date(nonISOString).
- Only pnpm is used in scripts or docs; package.json changes are expected only in the final cleanup.
- Commits are on a feature branch, not main.
- Scope: the diff touches only the files that piece was allowed to edit.

## How to work
- Read the relevant source files before making any claims.
- `git diff main...HEAD`; `grep -rn "moment" src/`; `grep -rn "new Date(" src/`; `grep -rn "toISOString\|formatISO" src/`.
- Run `pnpm test`, then `TZ=America/New_York pnpm test` and `TZ=Asia/Kolkata pnpm test`.
- Flag only issues that affect correctness, the stated requirements, or the done condition. List anything else as optional.

## Output format
Severity · file:line · Issue · Risk · Fix
Summarize in a table sorted by severity. If a category has no issues, say so briefly. Don't pad the report.
```

Optional: if you plan to run more timezone audits later, save the piece 1 prompt as `.claude/agents/tz-auditor.md` using the same template. For a one-off job, the prompt above is enough.

## 4. Merge plan

1. **Inventory (piece 1).** Check that each file appears in Table A exactly once and that the three groups don't overlap. Check the moment import count against `grep -rln "from 'moment'" src | wc -l`.
2. **Helper module (piece 2), from the main session on a branch, PR to main.** Pick the date-fns timezone add-on now. Use `@date-fns/tz` for date-fns v4, or `date-fns-tz` for v3; check what your version supports. Then `pnpm add date-fns` (and the add-on), write helper tests under `TZ=UTC` and a non-UTC zone, and merge. The workers start only after this is on main.
3. **Migration worktrees A, B, C (piece 3), in parallel.** Run the reviewer on each PR. Merge them one at a time. After each merge, rebase the others on main and run `pnpm test && pnpm build`. Once all three are in, make one small cleanup PR: `pnpm remove moment` (plus moment-timezone if used), confirm `grep -rn moment src` is empty, and check that the bundle got smaller.
4. **Timezone fixes (piece 4).** Run the reviewer. Verify that the suite passes under both `TZ=UTC` and a non-UTC TZ, and test one real date round-trip by hand (create → API → reload) to confirm the payload is a UTC ISO string.
5. **Docs (piece 5).** Check that the examples match the helper signatures and that `grep -rn moment docs/` is empty. Merge.

After that, clean up the worktrees with `git worktree list` and `git worktree remove <path>`.
