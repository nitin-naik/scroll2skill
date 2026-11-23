# moment.js → date-fns: how to split it in Claude Code

## The shape
These are three tasks of different kinds. Don't hand all of them to one prompt.

| Work | Kind | Who does it |
|---|---|---|
| Inventory + timezone bug hunt | Read-only research | **Session 1**, using parallel **Explore subagents** |
| Migration (≈40 files) | Mechanical edits in batches | **Sessions 2a–2n**, one batch per session/branch (parallel via **git worktrees**) |
| Timezone bug fixes | Small targeted behavior changes | **Session 3**, one commit per bug, test first |
| Developer docs | Writing | **Session 4**, last, after the code is settled |

The key ordering decision: **find the timezone bugs before migrating, but fix them separately.** If a migration commit also changes behavior, reviewers can't tell "same behavior, new library" apart from "bug fix", and a regression becomes impossible to bisect. Migration commits should preserve behavior, bugs included. The fixes go in their own commits with tests.

Each session starts clean (`/clear`, or a new terminal). Results move between sessions through **files in the repo** (`docs/migration/…`), not through chat history.

---

## Step 0: CLAUDE.md additions (do once, commit on a branch)
Your three rules are good. Add the migration-specific ones so every session and subagent picks them up automatically:
```markdown
## Dates
- Dates must be stored and sent as UTC ISO 8601 strings (e.g. `2026-11-20T14:03:00.000Z`).
- Use date-fns (and date-fns-tz if we need IANA timezones). Do not add new moment imports.
- Only convert to local time at display time, in components, using the shared helpers in `src/lib/dates.ts`.
- Never use `new Date(string)` on non-ISO strings. Parse with `parseISO` or an explicit format.

## Commands
- Install: `pnpm install` | Test: `pnpm test` | Typecheck: `pnpm typecheck` | Lint: `pnpm lint`  (adjust to your real scripts)
```
And keep: always pnpm; never commit to main.

---

## Session 1: Inventory and bug hunt (read-only, plan mode)
Start in **plan mode** (Shift+Tab) so nothing gets edited.
```
We're migrating from moment.js to date-fns. Don't edit any source files in this session. The only file you may write is docs/migration/inventory.md.

1. Use Explore subagents in parallel (split the work by top-level folder under src/) to find every use of moment: imports, moment(), .format(), .add/.subtract, .diff, .startOf/.endOf, .utc(), .local(), moment-timezone (.tz), locale usage, moment.duration, and places that pass moment objects through props, state, or API payloads.
2. Write docs/migration/inventory.md with:
   - a table with columns: file | moment APIs used | date-fns equivalent | risk (low/med/high) | notes
   - files grouped into batches of about 8–10 that can be migrated independently (keep files that share moment objects in the same batch)
   - the set of shared helpers we should create in src/lib/dates.ts (formatting presets, toUtcIso, parseUtc, etc.) so the batches don't each reinvent them
   - any moment behavior with no direct date-fns equivalent (mutability, locale-aware week start, lenient parsing, relative-time strings)
3. Timezone audit. Our rule: dates are stored and sent as UTC ISO strings. Find violations and likely bugs, for example:
   - sending local-time strings or format() output without "Z" or an offset to the API
   - moment(x) on a server UTC string without .utc(), where x has no offset
   - date-only values ("2026-03-08") that shift a day when parsed as UTC and shown locally
   - startOf('day') / endOf('day') used in API queries (local vs UTC day boundaries)
   - DST-sensitive arithmetic (add(24,'hours') vs add(1,'day'))
   - tests that only pass because CI runs in UTC
   Put each one in docs/migration/tz-bugs.md as: id | file:line | what happens | example input → wrong output | proposed fix | confidence. Don't fix anything.

Finish with a summary: file count, batch count, number of suspected tz bugs by confidence.
```
**Your job after this:** read both files. Remove false positives and adjust the batches. Commit them on `chore/date-fns-migration` so the later sessions can read them.

---

## Session 2: Foundation (one session, before the batches)
```
Read docs/migration/inventory.md. On branch chore/date-fns-migration (never commit to main):
1. pnpm add date-fns (and date-fns-tz only if the inventory says we need IANA timezones).
2. Create src/lib/dates.ts with the helpers listed in the inventory, plus unit tests. The tests must run under at least two timezones: add a test script that runs with TZ=America/New_York and TZ=Asia/Kolkata, as well as UTC. Include a DST-boundary case.
3. Add an ESLint rule (no-restricted-imports) that warns on 'moment' so we can track what's left.
Don't migrate any feature files yet. Run pnpm test and pnpm typecheck. Commit.
```

---

## Sessions 2a…2n: Migration batches (parallel, one per worktree)
Run each batch in its own git worktree so the sessions don't edit the same checkout:
```bash
git worktree add ../app-batch1 -b chore/date-fns-batch1 chore/date-fns-migration
cd ../app-batch1 && pnpm install && claude
```
(Or start Claude with `claude --worktree` if your version supports it.) 3–4 in parallel is plenty. Paste this into each one, changing the batch number:
```
Migrate batch 3 from docs/migration/inventory.md from moment to date-fns. Only touch the files in that batch (and their tests). Use the helpers in src/lib/dates.ts. If you need a new helper, add it there with a test and mention it in your summary.

Rules:
- Preserve behavior EXACTLY, including behavior listed in docs/migration/tz-bugs.md. Don't fix tz bugs here. If you touch a line that's in tz-bugs.md, leave a `// TZ-BUG <id>` comment and move on.
- Watch out: moment objects are mutable and date-fns functions return new values; moment's format tokens differ from date-fns' (YYYY→yyyy, DD→dd, etc.); moment(undefined) is "now" but parseISO(undefined) throws.
- Dates crossing the API stay UTC ISO strings.
- pnpm only. Never commit to main.

Done when: no moment imports remain in the batch, pnpm typecheck, pnpm lint, and pnpm test pass (including the multi-TZ test script), and you've committed on this branch. Finish with: files changed, any behavior you couldn't preserve exactly, and new helpers you added.
```
Merge each batch branch into `chore/date-fns-migration` once it's reviewed. If two batches add a helper with the same name, sort that out at merge time. That's the reason helpers are in one file.

**Final batch session:** remove `moment` (and `moment-timezone`) with `pnpm remove`, turn the lint rule into an error, and do a full build + test.

---

## Session 3: Timezone bug fixes (after migration)
```
Fix the bugs in docs/migration/tz-bugs.md that are marked confirmed, one at a time, on branch fix/tz-bugs (based on chore/date-fns-migration, never main).
For each bug:
1. Write a failing test that reproduces it under a non-UTC TZ (use the multi-TZ test script).
2. Fix it, following the rule: store and send UTC ISO strings, convert to local only for display.
3. Run the test file, then pnpm test.
4. Commit with the message "fix(dates): <id> <short description>".
If a fix would change an API payload format or what the user sees in a way that isn't obviously a bug, stop and ask me.
At the end, update tz-bugs.md with the status of each bug and its commit hash.
```
Use **one session** for this, not parallel ones. The fixes are small, and you want to approve any that change behavior.

---

## Session 4: Developer docs (last)
```
Update the developer docs for the date-fns migration. Read docs/migration/inventory.md, docs/migration/tz-bugs.md, src/lib/dates.ts and its tests first.
- Find existing docs that mention moment or date handling (README, docs/, CONTRIBUTING, code comments that link to docs) and update them.
- Add or extend a "Working with dates" section: the UTC ISO rule with right/wrong examples, when to use each helper in src/lib/dates.ts, how to show local time, how to run the multi-TZ tests, and a short moment→date-fns cheat sheet for the APIs we actually use.
- Keep it short and only document what exists in the code. Don't describe helpers that don't exist.
Then delete docs/migration/ or move the useful parts into the permanent docs (ask me which).
pnpm only; commit on the migration branch, not main.
```

---

## Where subagents help, and where they don't
- **Good:** fanning out the read-only inventory (session 1). Each subagent reads ~10 files and sends back a summary, so the main session's context stays small. Also a **fresh reviewer** at the end: "Use a subagent to review `git diff main...chore/date-fns-migration` for behavior changes outside of tz-bugs.md commits, and for any non-UTC value being sent to the API."
- **Not good:** using subagents for the edits themselves. They edit the same working tree, can't see each other's changes, and you only see their summaries. Use separate sessions in worktrees for parallel edits so each one has its own branch and diff you can review.

## Review checkpoints for you
1. After session 1: check the inventory and confirm which tz bugs are real.
2. After each batch: skim the diff (it should be boring, library swap only).
3. After session 3: read every fix commit. These are the real behavior changes.
4. Before merging into main: one PR, or one per phase if your team wants smaller reviews.
