# Blind judgment 2

Fixture checked: package.json, CLAUDE.md, .claude/settings.json, .claude/agents/reviewer.md, src/legacy/checkout.ts, src/routes/auth.ts. No tsconfig, ESLint config, .mcp.json, tests, prisma/ or src/server.ts exist.

## 1. Audit (audit_X vs audit_Y)

Both correctly flag: bypassPermissions + Bash(*); no git repo; missing `build` script; npm vs pnpm@9.12.0 conflict; src/legacy used by iOS v3; db:migrate risk; six MCP servers enabled with no .mcp.json; vague reviewer with no `tools:`; nonexistent folders in CLAUDE.md; "keep going until done" with no stop rule; headless `-p --max-turns` launch.

Y got, X missed:
1. None of the check commands can pass yet: no tsconfig, no ESLint config, no tests, no node_modules. That is true of the fixture, and it is the reason an overnight run would fail or loop.
2. Mechanical verification through PostToolUse and Stop hooks (exit 2, `stop_hook_active` guard), instead of leaving it as advice in CLAUDE.md.
3. Sandbox for third-party code run by `pnpm test`/`install`, a `~/.ssh` deny, plus an ordered pre-flight and a verify list.

X got, Y missed:
1. Notes that `Bash(*)` is redundant under bypass mode.
2. Suggests enforcing "no any" through `@typescript-eslint/no-explicit-any`.
3. Denies curl/wget for network egress.

Errors:
- X: puts `Bash(git diff*)` in an agent `tools:` list. Pattern specifiers may not be honoured there (minor).
- Y: says "You asked me to leave out ~/.claude", which the user never asked (minor fabrication of context). Its "eslint . fails on ESLint 9" is likely but unverified. Uses emoji status icons.

Winner: **Y**. It finds the most important repo-specific blocker (no check command can pass) and supplies enforceable hooks and a sandbox. Its extra length mostly carries content.

## 2. Loop (loop_X vs loop_Y)

Both give: plan mode, then failing tests, then implement, then fresh-context review; atomic INCR+TTL set on first failure only; lock checked before the password; email normalization; validation 400s don't count; fail-open decision; trust-proxy/X-Forwarded-For risk; no enumeration.

X got, Y missed:
1. Warns that Vitest fake timers do not advance real Redis TTL. Y tells Claude to use `vi.useFakeTimers` for the window, which silently breaks tests against real Redis.
2. Stop hook (exit 2) added only after the tests-first step, plus a commit after each green step.
3. Concurrency test, 5xx-not-counted test, TTL-not-extended test, and a risk section that also covers lockout DoS, a config flag, and a Redis timeout.

Y got, X missed:
1. Creates a feature branch up front and suggests `/init` if there is no CLAUDE.md.
2. A headless `-p` option with scoped `--allowedTools`.
3. A clearer limiter API and config constants. It is more concise overall.

Errors:
- Y: the fake-timers advice is wrong for a real Redis TTL unless Redis is mocked.
- X: the details of Ctrl+G plan editing and the "clear context and auto-accept edits" option depend on the version but are plausible. X is long (about 10.5k) with some repetition between the prompts and the checklist.

Winner: **X**. It is more correct on the subtle test-timing trap and covers more edge cases, at the cost of length.

## 3. Delegation (deleg_X vs deleg_Y)

Both give: read-only inventory first; a shared src/lib/dates.ts foundation; parallel worktree batches that preserve behaviour, bugs included; timezone fixes afterwards in one session, test first, one commit per bug; docs last; multi-TZ test runs; a no-restricted-imports lint guard; format-token and mutability gotchas; CLAUDE.md rules (pnpm, never main, UTC ISO).

Y got, X missed:
1. Every prompt restates the CLAUDE.md rules and gives a scope, a done condition and a return format. It also notes that Explore and Plan subagents don't load CLAUDE.md and chooses a general-purpose agent instead.
2. A reusable reviewer agent file, and an explicit merge plan with a verification step at each merge, including a check of real API payloads that every date ends in Z.
3. date-fns v4 uses `@date-fns/tz` (date-fns-tz is for v3). It also has a "stop and ask" rule for payload or visible changes during the refactor.

X got, Y missed:
1. Adds a "Dates" section to CLAUDE.md so every session inherits the rules automatically.
2. Explains clearly why subagents should not do parallel edits.
3. More concise, at about 9.4k against 16.4k.

Errors:
- X: Session 1 runs in plan mode but tells Claude to write docs/migration/inventory.md. Plan mode blocks that write.
- X: uses Explore subagents for the inventory without noting that they skip CLAUDE.md (minor, because the rules are in the prompt).
- Y: its YYYY|DD rg regex is sloppy (minor). Its length is high but mostly paste-ready content.

Winner: **Y**. It is more complete and more actionable, with self-contained prompts, a reviewer agent and a merge plan, and it has no workflow contradiction.

```json
{"audit": {"X": {"correctness":8,"coverage":7,"actionability":8,"focus":8}, "Y": {"correctness":8,"coverage":9,"actionability":9,"focus":7}, "winner": "Y"}, "loop": {"X": {"correctness":9,"coverage":9,"actionability":8,"focus":6}, "Y": {"correctness":7,"coverage":7,"actionability":8,"focus":8}, "winner": "X"}, "deleg": {"X": {"correctness":7,"coverage":8,"actionability":8,"focus":8}, "Y": {"correctness":9,"coverage":9,"actionability":9,"focus":6}, "winner": "Y"}}
```
