# Blind judgment

Fixture verified: there is no `build` script; `packageManager` is pnpm@9.12.0; settings use `bypassPermissions` + `Bash(*)`; 6 MCP servers are enabled with no `.mcp.json`; `src/services`, `prisma/` and `tests/` don't exist; `legacy/checkout.ts` is still used by iOS v3; the directory is not a git repo. Both audits get all of these facts right.

## 1. Audit

**X got, Y missed**
1. How to actually launch the overnight run: headless `claude -p ... --max-turns 60 --output-format json`, so a blocked tool fails cleanly instead of hanging. This is the core of "unattended".
2. Explicit stop conditions (stop after 3 identical failures, or when a schema change or new dep is needed), work on a branch, commit per green step, never push, plus a morning review routine.
3. A read-only `tools:` restriction for the reviewer agent (it currently inherits Edit/Bash under bypass), and a mechanical `deny Edit(./src/legacy/**)`.

**Y got, X missed**
1. Enabling the sandbox (`sandbox.enabled`), with the point that test code in node_modules runs outside permission checks. X only suggests a container in prose.
2. Hooks that turn the advisory "test after every edit" into enforcement (PostToolUse typecheck/lint, Stop test, exit 2).
3. A per-file:line findings table plus a "verify on your version" table for less-certain settings (`auto` mode, `autoMode`, `TaskCompleted`).

**Errors / risks**
- X: `tools: ... Bash(git diff*)` in a subagent `tools:` field probably isn't valid there (that field takes tool names, not permission patterns). Minor.
- Y: an unconditional `Stop` hook running `pnpm -s test || exit 2` with no `stop_hook_active` guard can keep Claude looping all night when a test won't pass. That is a real overnight hazard. The per-edit full typecheck+lint is also costly (Y acknowledges this). It gives no launch command and no turn cap, and its reviewer has no tool restriction. `"defaultMode": "auto"` is hedged, which is acceptable.

**Winner: X.** It answers the "unattended overnight" question directly: a safe launch command, a turn cap, stop rules and branch hygiene. Y's stronger config (sandbox, hooks) comes with a Stop-hook loop risk and no plan for actually running it.

## 2. Loop

**X got, Y missed**
1. Fully paste-ready prompts for every phase (plan, failing tests, implement, fresh-session security review). Y pastes only the kickoff, and the rest is checklist prose.
2. An explicit 11-case test spec, including "correct password still 429", Retry-After decreasing over time, the 400 not counting, an enumeration-safe 429, and a TTL set only on the first increment. It also says "don't change tests to pass".
3. A security review prompt (concurrency races, X-Forwarded-For spoofing, Redis key collisions), an optional headless variant, and a note that per-IP-only spraying isn't covered.

**Y got, X missed**
1. Concrete commit checkpoints per sub-step and context hygiene (`/compact` after a commit, `/clear` between features).
2. Plan-mode UX: Ctrl+G to edit the plan, and "clear context and auto-accept edits" so the build starts with a clean context.
3. A risk section on proxy misconfiguration locking out a whole office, and on keeping deploy out of the session.

**Errors:** none significant. X's headless example uses `npx vitest` in allowedTools, but it says to adapt this to your package manager. Y leaves reset-on-success and fail mode to the plan (fine, though less decisive).

**Winner: X.** It gives the user something to paste at every step, with a test-first spec that pins down the requirement precisely.

## 3. Deleg

**X got, Y missed**
1. A ready reviewer agent file with migration-specific checks (format tokens, invalid-date handling, week start) and runs under multiple TZs.
2. Every prompt restates the CLAUDE.md rules, and it flags that some built-in agents may not load CLAUDE.md.
3. A merge plan: per-branch PRs to main, rebase plus test after each merge, a separate cleanup PR for `pnpm remove moment`, and a `@date-fns/tz` vs `date-fns-tz` version check.

**Y got, X missed**
1. Hands results between sessions through committed files (`docs/migration/inventory.md`, `tz-bugs.md`) instead of chat, and adds date rules to CLAUDE.md so every session inherits them.
2. A no-restricted-imports ESLint rule to track what's left, a DST-boundary test, `// TZ-BUG <id>` markers during migration, and a "stop and ask me" when a fix changes a payload or the UI.
3. Explicit pitfalls (moment mutability, `moment(undefined)` vs `parseISO`), and a clear rationale for why subagents shouldn't do parallel edits.

**Errors**
- Y: session 1 runs in plan mode but tells Claude to write `docs/migration/inventory.md`, which plan mode won't allow. That's an internal contradiction. Saying "subagents edit the same working tree" ignores the worktree-isolation option. Minor.
- X: it assumes a `pnpm build` script exists. The claim that Explore/Plan skip CLAUDE.md is plausible but should be verified.

**Winner: tie, leaning Y.** The two are roughly equal in substance. Y's file-based handoff and lint tracking are more robust than X's paste-the-table approach, and X's reviewer and merge plan are more complete. I score Y slightly higher on focus.

```json
{"audit": {"X": {"correctness":8,"coverage":8,"actionability":9,"focus":8}, "Y": {"correctness":7,"coverage":8,"actionability":8,"focus":7}, "winner": "X"}, "loop": {"X": {"correctness":9,"coverage":9,"actionability":9,"focus":8}, "Y": {"correctness":8,"coverage":8,"actionability":7,"focus":8}, "winner": "X"}, "deleg": {"X": {"correctness":8,"coverage":9,"actionability":9,"focus":7}, "Y": {"correctness":7,"coverage":9,"actionability":9,"focus":8}, "winner": "tie"}}
```
