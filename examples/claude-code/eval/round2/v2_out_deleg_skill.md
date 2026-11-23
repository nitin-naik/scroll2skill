# Splitting the moment.js → date-fns migration across Claude Code sessions

**Short answer:** this job has three kinds of work, and each needs a different mode:

- **Finding things** (where moment is used, which call sites look timezone-unsafe). Give this to a read-only subagent that writes one inventory file.
- **Mechanical refactoring** (40 files). Use 2–3 parallel sessions, each in its own git worktree and each owning its own set of directories. Every one of them must keep current behaviour exactly, including the bugs.
- **Behaviour changes** (the timezone fixes). Do these in one session on a separate branch, after the refactor, so the fixes can be reviewed and reverted without touching the refactor.

The docs update is small and comes last. A fresh-context reviewer subagent checks every branch before it merges.

Don't hand all of this to one session. 40 files is far more than "a few turns", and if refactor and bug fixes share one diff, nobody can review it. Don't use an orchestrator or agent team either: 3–4 pieces are easy to run yourself, and teams cost several times more tokens.

---

## 1. Split

| # | Piece | Mode | Depends on | Why |
|---|---|---|---|---|
| 0 | Set up the branch | **Main session** | none | Two commands. CLAUDE.md says never commit to main, so everything happens on `feat/date-fns` (the integration branch). |
| 1 | Inventory + timezone-suspect list | **Subagent** (general-purpose, *not* Explore) | 0 | It means reading 40+ files when you only need the conclusion. Explore doesn't load CLAUDE.md. It writes one file: `docs/migration/inventory.md`. |
| 2 | Shared foundation: `src/lib/dates.ts`, deps, lint guard | **Main session** | 1 | Every later piece depends on this API, so decide it once and with full context. |
| 3a/3b/3c | Migrate files, grouped by directory (about 13 files each) | **Parallel worktree sessions** | 2 | Independent files and many edits. Worktrees keep the sessions from colliding. |
| 4 | Fix the timezone bugs | **Worktree session** (single) | 3a–c merged | These change behaviour, so they go on a separate branch. Some fixes may change API payloads, so it has to stop and ask. |
| 5 | Update the developer docs | **Subagent** | 2 (API final), 4 (conventions final) | A few files that nothing else is editing by then. |
| R | Review each branch before merge | **Reviewer subagent, fresh context** (agent file below) | each of 3a–c, 4, 5 | It judges the diff without the assumptions the author session built up. |

### Main-session piece 0: set up the branch
```
git checkout main && git pull && git checkout -b feat/date-fns && git push -u origin feat/date-fns
```
Every later branch starts from `feat/date-fns` and merges back into it. Only `feat/date-fns` goes to `main`, through a PR.

### Main-session piece 2: decisions and commands
1. **Choose the timezone approach and write the helper.** With date-fns v4 (current), use `@date-fns/tz` (`TZDate`, `tz()`). On v3, use `date-fns-tz`. Then:
   `pnpm add date-fns @date-fns/tz` and write `src/lib/dates.ts`, which exports a small, deliberate API, for example:
   - `toUtcIso(d: Date): string`, which wraps `d.toISOString()`. It is the only allowed way to serialise a date.
   - `parseUtcIso(s: string): Date`, a strict `parseISO` that throws on input that is not ISO.
   - `formatDisplay(d, pattern, timeZone?)` for UI formatting in the user's zone.
   - `startOfDayInZone(d, timeZone)` and similar, but only where the inventory shows they are needed.

   Add a unit test file for it, and run it under several timezones (see the merge plan).
2. **Make progress measurable.** Add an ESLint `no-restricted-imports` rule for `moment` and `moment-timezone`, set to `warn` for now. "How many left?" then has a one-command answer: `pnpm lint 2>&1 | grep -c "moment"`. Raise the rule to `error` after 3a–c are merged.
   Commit to `feat/date-fns`. Also add one line to CLAUDE.md so every later session inherits it: *"Date handling goes through `src/lib/dates.ts`; don't import date-fns tz helpers directly in components. Moment is banned."*

---

## 2. Prompts

Paste these as written. Each one restates your CLAUDE.md rules, because a subagent or new session sees none of this conversation (and Explore/Plan agents don't even see CLAUDE.md).

### Piece 1: Inventory subagent
Ask the main session to "use a general-purpose subagent with this prompt". Don't use Explore.

```
Goal: Produce a complete inventory of moment.js usage in this React app, so the
migration to date-fns can be split into parallel pieces and timezone bugs can be fixed
afterwards. You are mapping, not fixing.

Already known: About 40 files import moment (possibly also moment-timezone). We are on
branch feat/date-fns. The target is date-fns v4 with @date-fns/tz. Nothing has been
migrated yet.

Rules (from CLAUDE.md, restated):
- Always use pnpm, never npm or yarn.
- Never commit to main. Commit only to the current branch, feat/date-fns.
- Dates must be stored and sent as UTC ISO strings (e.g. "2026-11-20T09:30:00.000Z").

Scope: READ-ONLY except for one new file: docs/migration/inventory.md. Do not edit any
source file. You may run grep/rg, `pnpm ls moment`, and read any file.

What to record in docs/migration/inventory.md:
1. A table of every file that imports moment: path · moment APIs used (format, diff,
   add, startOf, utc, tz, locale, isValid, duration, ...) · rough complexity (S/M/L).
2. A proposed grouping into 3 batches by top-level directory, about 13 files each, with
   no file in two batches. Shared utilities should go in the batch that owns their
   directory.
3. "Timezone suspects": every call site that may break the UTC rule or behave
   differently across zones, as path:line · what it does · why it is suspect. Look
   especially for:
   - moment(str) on date-only strings ("2026-11-20"), which parse as local time
   - moment() / format() values sent to an API or stored without .utc()/.toISOString()
   - startOf('day') / endOf('day') used for date-range queries
   - format() strings without Z/offset that get sent to the server
   - diff() in days across DST
   - hard-coded offsets, or new Date(y, m, d) mixed with UTC values
   - mutation bugs (moment objects reused after .add()/.subtract())
4. Format-token gotchas present in this codebase (YYYY→yyyy, DD→dd, Do→do, A→a, X/x, etc.)
   and any locale usage.
5. Test coverage: which of these files have tests, and the test command(s).

Done when: inventory.md exists, covers every file `rg -l "from 'moment'|require\\('moment'\\)"`
returns (state the count), and is committed to feat/date-fns with message
"docs: moment usage inventory".

Return (max 15 lines): file count, the 3 batches as directory lists, the number of timezone
suspects with the 5 most serious as path:line, and anything surprising. Don't paste the
file contents.
```

### Pieces 3a / 3b / 3c: parallel migration sessions
Start each in its own worktree from the foundation branch:
```
git worktree add ../dates-a -b refactor/date-fns-a feat/date-fns && cd ../dates-a && pnpm install && claude
```
(or `claude --worktree dates-a`, but check `claude --help` on your version and make sure it branches from `feat/date-fns`, not `main`). Repeat for b and c. Use the same prompt for each and change only the batch letter.

```
Goal: Replace moment.js with date-fns in batch A (listed in docs/migration/inventory.md),
as a PURE REFACTOR: identical behaviour, including existing bugs. This keeps the
refactor reviewable and lets the timezone fixes land separately.

Already known:
- docs/migration/inventory.md lists your files, the APIs they use, format-token
  gotchas and timezone suspects. Read it first.
- src/lib/dates.ts is the shared helper API (toUtcIso, parseUtcIso, formatDisplay, ...).
  Use it, and don't change its signatures. If you need something it lacks, add a
  private helper in your file and note it in your report.
- Two other sessions are migrating batches B and C in parallel. Don't touch their files.

Rules (from CLAUDE.md, restated):
- Always use pnpm (pnpm test, pnpm lint, pnpm tsc / pnpm typecheck).
- Never commit to main. Commit only to this branch, refactor/date-fns-a.
- Dates must be stored and sent as UTC ISO strings. Serialise via toUtcIso() only.

Scope: Edit ONLY the files in batch A, their colocated tests, and
docs/migration/timezone-findings-a.md. Don't edit src/lib/dates.ts, package.json,
the lockfile, or other batches' files.

How to work:
- date-fns is immutable and moment is mutable. Where moment code relied on mutation,
  reproduce the result exactly.
- Translate format tokens carefully (YYYY→yyyy, DD→dd, etc.). A wrong token is a
  silent bug.
- If an exact equivalent would change output, an API payload, or what the user sees,
  STOP on that file and ask me. Don't guess.
- If you notice a timezone bug, DO NOT fix it. Keep the current behaviour, and append
  path:line · bug · proposed fix to docs/migration/timezone-findings-a.md.

Done when: no batch-A file imports moment (`pnpm lint` shows no moment warnings for
these paths); `pnpm tsc`, `pnpm lint` and `pnpm test` pass; tests also pass with
`TZ=America/New_York pnpm test` and `TZ=Asia/Kolkata pnpm test`; work committed in
small commits on refactor/date-fns-a.

Return (max 15 lines): files migrated (count), any file you stopped on and why, helpers
you added, new timezone findings (count + path:line), and test results.
```

### Piece 4: Timezone-fix session (after 3a–c are merged)
```
git worktree add ../dates-tz -b fix/date-timezones feat/date-fns && cd ../dates-tz && pnpm install && claude
```
```
Goal: Fix the timezone bugs found during the migration, so that every date is stored and
sent as a UTC ISO string and displayed correctly in the user's zone.

Already known:
- moment is fully removed. All date code now uses date-fns via src/lib/dates.ts.
- Bugs are listed in docs/migration/inventory.md ("Timezone suspects") and
  docs/migration/timezone-findings-{a,b,c}.md. Read all of them, then de-duplicate.
- The migration was deliberately behaviour-preserving, so these bugs are still present.

Rules (from CLAUDE.md, restated):
- Always use pnpm.
- Never commit to main. Commit only to fix/date-timezones.
- Dates must be stored and sent as UTC ISO strings. This is the rule you are enforcing.

Scope: You may edit any src/ file named in those findings, plus src/lib/dates.ts and
tests. One commit per bug, so each fix can be reverted on its own.

How to work:
- For each bug, write a failing test first that reproduces it under a non-UTC TZ
  (e.g. TZ=America/Los_Angeles, and a DST-boundary date such as 2026-03-08 or
  2026-11-01), then fix it.
- STOP and ask me before any fix that changes an API request/response payload, a stored
  value's format, or a date the user sees. List those as "needs decision" with the
  before/after value.
- If a finding is not actually a bug, mark it "not a bug" with a reason.

Done when: every finding is fixed, marked "needs decision", or marked "not a bug" in
docs/migration/timezone-findings.md (merged list, with status per item);
pnpm tsc/lint/test pass under TZ=UTC, America/Los_Angeles and Asia/Kolkata.

Return (max 20 lines): a table path:line · bug · status (fixed / needs decision / not a
bug) · commit sha, followed by the "needs decision" items with before/after values.
```

### Piece 5: Docs subagent (after 4 is merged)
```
Goal: Update the developer docs so new code follows the new date conventions, not
moment-era guidance.

Already known: moment is gone; date handling goes through src/lib/dates.ts (read it and
its tests); conventions and fixed pitfalls are in docs/migration/timezone-findings.md.

Rules (from CLAUDE.md, restated): use pnpm in any command shown in the docs; never
commit to main; commit only to the current branch (docs/date-fns); dates are stored and
sent as UTC ISO strings, so state this prominently.

Scope: Edit only files under docs/ (excluding docs/migration/), README.md and
CONTRIBUTING.md if they mention dates or moment. No source changes.

Cover: which helper to use for what (serialise / parse / display / ranges in the user's
zone); the UTC-ISO rule with one right and one wrong example; date-fns format tokens vs
moment; how to run tests under multiple TZ values; that moment is banned by lint.
Remove or rewrite every moment reference (`rg -i moment docs README.md CONTRIBUTING.md`
should only return the historical migration notes).

Done when: that rg check is clean, and every code sample uses real exports from
src/lib/dates.ts. Commit as "docs: date-fns conventions".

Return (max 10 lines): files changed, sections added/removed, anything you couldn't
verify against the code.
```

---

## 3. Agent file (reused for 5 reviews)

Save as `.claude/agents/date-migration-reviewer.md`. After each branch is done, run it from that worktree: *"Use the date-migration-reviewer agent on the diff `feat/date-fns...HEAD`."*

```markdown
---
name: date-migration-reviewer
description: Reviews a branch diff from the moment.js → date-fns migration or timezone fixes before it merges into feat/date-fns. Use after each migration batch, the timezone-fix branch, and the docs branch.
tools: Read, Grep, Glob, Bash
---
## Rules to enforce (from CLAUDE.md)
- pnpm only; nothing committed to main; dates stored and sent as UTC ISO strings.

## What to check
- No remaining `moment` / `moment-timezone` imports or `require` in changed files.
- Format tokens translated correctly (yyyy not YYYY, dd not DD, do/a/X/x equivalents).
- Places that relied on moment's mutability now produce the same values.
- Every date sent to an API or stored goes through toUtcIso() / is a UTC ISO string.
- No date-only string parsed as local time; no startOf/endOf-day used for server ranges without an explicit zone.
- Refactor branches (refactor/*): NO behaviour change. Any behaviour difference is a defect.
- Fix branch (fix/date-timezones): each behaviour change has a test that fails without it, and any payload/visible change is listed as "needs decision".
- Changes stay inside the branch's declared scope (batch files / docs only).

## How to work
- Read docs/migration/inventory.md and src/lib/dates.ts first.
- `git diff feat/date-fns...HEAD`, then read each changed file in full before making claims.
- Run `pnpm tsc`, `pnpm lint`, `pnpm test`, and `TZ=America/Los_Angeles pnpm test`.
- `rg "moment" <changed paths>`; `rg "format\(.*['\"].*YYYY|DD" <changed paths>`.

## Output format
Severity · file:line · Issue · Risk · Fix
Summarize in a table sorted by severity. If a category has no issues, say so briefly. Don't pad the report.
Flag only issues that affect correctness, the stated requirements or the done condition; list anything else as optional.
```

Pieces 1, 3, 4 and 5 are one-off jobs, so they stay plain prompts.

---

## 4. Merge plan

| Step | Merge | Verify after |
|---|---|---|
| 1 | Inventory commit (already on `feat/date-fns`) | Read it yourself. Check that the batches don't overlap and the file count matches `rg -l moment src \| wc -l`. Fix the grouping now if it's wrong. |
| 2 | Foundation commit (piece 2) | `pnpm tsc && pnpm test`; the lint warning count equals the inventory count. |
| 3 | `refactor/date-fns-a`, then `-b`, then `-c` → `feat/date-fns` (one at a time, reviewer agent first on each) | After each: `pnpm tsc && pnpm lint && pnpm test` and `TZ=Asia/Kolkata pnpm test`; the lint moment count drops by that batch's size. Click through screens that show dates. |
| 4 | Finish the moment removal on `feat/date-fns` (main session) | `pnpm remove moment moment-timezone`; lint rule → `error`; zero hits for `rg moment src`; bundle size check. |
| 5 | `fix/date-timezones` → `feat/date-fns` (reviewer first) | Answer the "needs decision" items before merging. Run the full test suite under three TZ values. Compare a few real API request payloads before and after (DevTools/network log): every date ends in `Z`. |
| 6 | `docs/date-fns` → `feat/date-fns` (reviewer first) | Code samples match the real exports in `src/lib/dates.ts`. |
| 7 | PR `feat/date-fns` → `main` | CI green; never a direct commit to main. |

Clean up afterwards with `git worktree remove ../dates-a`, and the same for the others. Pieces 1→2→3 run in sequence because the batches can't be decided before the inventory exists. Only 3a/3b/3c run in parallel.
