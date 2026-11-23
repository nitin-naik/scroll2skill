---
name: auditing-claude-code-hooks
description: Review and fix existing Claude Code hooks (the "hooks" block in settings.json plus the scripts it calls) for bugs that make them silently not fire, not block, over-block, loop forever, slow Claude down, or open security holes. Use when the user says "review/debug/audit my hooks", "my hook isn't working/blocking", "Claude keeps looping/never stops", or pastes a settings.json with hooks. Do not use for writing a new hook from scratch (use writing-claude-code-hooks), git hooks, or React hooks.
---

# Auditing Claude Code hooks

Answer the user's actual question first: for each symptom they reported, lead with the full **chain** of causes (often several independent bugs stack up), then the rest. The checklist is the minimum to cover, not a template. Use your own knowledge where it is silent; point to current docs (code.claude.com/docs, "Hooks reference") for version-specific behaviour.

## Steps

1. Read every settings file in play: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, plugin `hooks/hooks.json`. If you can't read one, say so and tell the user to check it for duplicates; all matching hooks from all scopes run.
2. Read every script a hook calls; note mode (`ls -l`), shebang, and dependencies.
3. Run the checklist. Record: file:line, what breaks, severity, fix.
4. **Prove it.** Copy the hooks to a temp dir, `export CLAUDE_PROJECT_DIR=<copy>`, and run each script with crafted stdin, before and after the fix: `echo '{"tool_name":"Bash","tool_input":{"command":"rm -fr /"}}' | ./guard.sh; echo "exit=$?"`. Never run hooks in the user's repo (they may run tests, installs, deletes). Config-level bugs (matcher case, wrong nesting) can't be run: show them with `jq '.hooks' settings.json` and cite the rule.
5. Return fixed files in full, keeping the user's file names; if you remove a hook, say why and show the replacement.
6. Validate fixed files: `jq . settings.json`, `bash -n script.sh` / `python3 -m py_compile`, and a negative test set (things that must still be allowed).

## Severity

- **BROKEN**: never fires or never has its intended effect.
- **LEAKY**: fires but misses cases (regex holes, missing tools).
- **OVER-BLOCKS**: blocks legitimate work (false positives, loops).
- **UNSAFE**: security hole (injection, fail-open guard, secrets exposed).
- **SLOW** / **STYLE**.

## Checklist

**Config shape**
- `hooks.<Event>` is an array of `{ "matcher", "hooks": [ { "type": "command", "command", "timeout"? } ] }`. Other shapes are silently ignored.
- Event names are case-sensitive and exact (`PreToolUse`).
- Matcher is a case-sensitive regex on tool name: `bash` never matches `Bash`. File guards need `Edit|MultiEdit|Write|NotebookEdit` (NotebookEdit uses `.tool_input.notebook_path`). Matchers on Stop/UserPromptSubmit do nothing.
- Command path: relative paths resolve against the current cwd and fail with exit 127 (non-blocking) once Claude `cd`s; use `"$CLAUDE_PROJECT_DIR"/.claude/hooks/x.sh` with the quotes. Unquoted paths break on spaces.
- Missing `chmod +x` or shebang -> exit 126, non-blocking: the guard is silently off.

**Blocking semantics**
- Blocking needs **exit 2** with the reason on **stderr**. Exit 1 or any other code only warns the user and the tool runs anyway. stdout on exit 2 is not shown to Claude.
- JSON output (`permissionDecision`, `decision`, `continue`) is only parsed on **exit 0**. JSON + exit 2: still blocks, but Claude gets stderr (often empty) instead of the reason. Fix: exit 0 with the JSON, or stderr + exit 2.
- PostToolUse can't undo the call; move guards to PreToolUse.
- UserPromptSubmit exit 2 erases the user's prompt; confirm that's intended.

**Loops and hangs**
- Stop/SubagentStop hook that blocks without exiting 0 when `stop_hook_active` is `true` loops forever. Also check its gating command can succeed at all (exists, right cwd: `cd "$CLAUDE_PROJECT_DIR"`), else the loop is permanent; and pass failure output (last ~30 lines) to Claude, not `>/dev/null`.
- Script reads stdin twice (two `jq` calls on stdin): second read gets nothing. Save `INPUT=$(cat)` once.
- Slow commands on PostToolUse with `*`/no matcher run after every tool call (default timeout 60 s). Narrow the matcher to `Edit|MultiEdit|Write`, scope to the edited file, set `timeout`, or move test runs to Stop.

**Pattern correctness**
- Command regexes: `--force[^-]` misses a trailing `--force`; use `(^|\s)(-f|--force)(\s|$)`. `rm -rf /` literal checks miss `rm -fr`, `rm -r -f`, `rm -Rf`, `/bin/rm`, `sudo rm`, and over-match `rm -rf /tmp/x`: parse flags and check targets (`/`, `/*`, `~`, `$HOME`, `.`, `*`).
- Path globs: `*.env*` also hits `.envrc`, `.env.example`, `environment.py`; match `.env` and `.env.*`, allow `.env.example`/`.env.sample`.
- String blocklists are bypassable (`bash -c`, `python -c`, redirection from Bash into a protected file). Recommend `permissions.deny` (e.g. `"Edit(./.env)"`, `"Read(./.env)"`) as the real control.
- `grep` without `-E`, unquoted `$VAR` in `[[ ]]`/`echo`, and `echo "$CMD"` with `-n`/`-e` content all mis-handle input.

**Robustness and security**
- Missing `jq`/`python3`: guards should fail closed (exit 2); Stop hooks, formatters, loggers fail open (exit 0) to avoid loops/blocking work.
- `eval`, unquoted input, or interpolating `tool_input` into a shell command = injection. Build JSON with `jq -n --arg`.
- Committed `.claude/settings.json` hooks run for every teammate; personal hooks belong in `.claude/settings.local.json`.

## Output format

1. **Answer to the symptoms**: one short paragraph per reported symptom with its full cause chain.
2. **Findings table**: # | severity | file:line | problem | fix.
3. **Fixed files** in full + `chmod +x` command.
4. **Proof**: before/after test commands and results, including the must-still-allow cases.
5. **Behaviour changes**: anything the fixed hooks now allow or block that the old ones (nominally) didn't.
6. One short "check before you use this" list (restart Claude Code / check `/hooks`, other scopes you couldn't read).

## Scope and limits

Sources showed working hooks, not audits; this checklist combines their correct patterns with known failure modes *(inferred)*. Not covered by the sources: plugin hooks, managed/enterprise hook policies, prompt-type hooks, PermissionRequest hooks.

## Sources

- Claude (official), "Hooks in Claude Code", 2026-05-07: https://www.youtube.com/watch?v=IkaPHiMDazM&t=58 (config shape), &t=98 (`Edit|MultiEdit|Write`), &t=114 (exit 2 + stderr, force-push regex with the trailing-flag bug), &t=137 (JSON deny on exit 0), &t=146 (team scope), &t=161 (`$CLAUDE_PROJECT_DIR`).
- Better Stack, 2025-07-12: https://www.youtube.com/watch?v=Q4gsvJvRjCU&t=54 (exit codes 0/2/other), &t=105 (fail-open exit 1), &t=118 (.env guard allowing .env.sample; matchers optional).
- Skills For AI, 2026-10-17: https://www.youtube.com/watch?v=qljN6aKRez8&t=243 (hook vs CLAUDE.md).
- *(inferred / own knowledge)*: stop_hook_active loop, stdin-read-twice, exit 126/127, over-blocking class, permissions.deny layering.

Built from 3 videos (uploaded 2025-07-12–2026-10-17) on YouTube, 2026-11-22. Date-sensitive rules: event names, `async`, MultiEdit, default timeout.
