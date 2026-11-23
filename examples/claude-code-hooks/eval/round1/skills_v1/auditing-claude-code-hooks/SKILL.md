---
name: auditing-claude-code-hooks
description: Review existing Claude Code hooks (the "hooks" block in settings.json plus the scripts it calls) for bugs that make them silently not fire, not block, loop forever, slow Claude down, or open security holes, then return fixed versions. Use when the user says "review/debug/audit my hooks", "my hook isn't working/blocking", "Claude keeps looping after my Stop hook", or pastes a settings.json with hooks. Do not use for writing a new hook from scratch (use writing-claude-code-hooks), git hooks, or React hooks.
---

# Auditing Claude Code hooks

Answer the user's actual question first: if they asked why one hook fails, lead with that cause and fix. The checklist below is the minimum to cover, not a template. Use your own knowledge where it is silent; check current docs (code.claude.com/docs, "Hooks reference") for version-specific behaviour.

## Steps

1. Read every settings file in play: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json` (and plugin `hooks/hooks.json` if present). Note duplicates across scopes: all matching hooks run.
2. Read every script a hook calls. If a script is missing or not executable, that is finding #1.
3. Run the checklist. For each finding record: file:line, what breaks, severity, fix.
4. Where possible, run each script with a crafted stdin to prove the bug: `echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main --force"}}' | ./script.sh; echo "exit=$?"`.
5. Return corrected settings and scripts in full.

## Checklist

**Config shape**
- `hooks.<Event>` is an array of `{ "matcher", "hooks": [ { "type": "command", "command", "timeout"? } ] }` [Claude official t=0:58]. A flat `{"PreToolUse": {"command": ...}}` is silently ignored.
- Event names are case-sensitive and exact (`PreToolUse`, not `preToolUse` / `BeforeTool`).
- Matcher is a case-sensitive regex on tool name: `bash` never matches `Bash`. `Edit|Write` misses `MultiEdit` where it exists [Claude official t=1:38]. Matcher on Stop/Notification is ignored [Better Stack t=1:58].
- Command path: relative paths break when cwd changes; use `"$CLAUDE_PROJECT_DIR"/.claude/hooks/x.sh` with the quotes [Claude official t=2:41]. Unquoted paths break on spaces.

**Blocking semantics**
- Blocking requires **exit 2** with the reason on **stderr**; exit 1 (or any other code) only warns the user and the tool runs anyway [Better Stack t=0:54].
- JSON output (`permissionDecision`, `decision`, `continue`) is only read on **exit 0**; JSON printed with exit 2 is ignored [Claude official t=2:17].
- PostToolUse cannot undo the tool call; a "guard" there is too late. Move it to PreToolUse.
- UserPromptSubmit exit 2 erases the user's prompt; check that is intended.

**Loops and hangs**
- Stop/SubagentStop hook that exits 2 (or `decision:"block"`) without checking `stop_hook_active` loops forever.
- Hook that reads stdin twice (`jq ... ` twice without saving `INPUT=$(cat)`) gets empty input the second time.
- Slow commands (full test suite, `npm install`) on PostToolUse with matcher `*` or no `timeout`: default timeout is 60 s and it runs after every tool call. Narrow the matcher, set `timeout`, or mark logging hooks `"async": true` [Claude official t=1:30] *(version-dependent)*.

**Pattern correctness**
- Command regexes: test end-of-string and flag variants. `--force[^-]` misses a trailing `--force` [Claude official t=1:54]; `rm -rf` checks miss `rm -fr`, `rm -r -f`, `/bin/rm`. String blocklists are bypassable via `bash -c`, `sh -c`, `python -c`; say so.
- File guards keyed only on Bash commands miss Edit/Write (and vice versa); `.env` guards should allow `.env.example`/`.env.sample` explicitly [Better Stack t=1:58].
- `grep` without `-E` treats `|`, `+`, `\s` differently; `grep -q` on unquoted variables word-splits.

**Robustness and security**
- Missing `jq` / `python3`: decide fail-open (exit 1 + message) or fail-closed (exit 2) explicitly; security guards should fail closed [Better Stack t=1:45 shows fail-open for a convenience hook].
- Unquoted `$VAR` from input, `eval`, or interpolating `tool_input` into a shell command = command injection.
- Hooks run with the user's full permissions; a committed project hook runs for every teammate [Claude official t=2:26].
- Script missing shebang or `chmod +x` -> fails with exit 126 (non-blocking, so the guard is silently off).

## Output format

1. **Verdict line**: how many hooks, how many findings, the worst one.
2. **Findings table**: # | severity (BROKEN = never works / UNSAFE = wrong block or security hole / SLOW / STYLE) | file:line | problem | fix.
3. **Fixed files** in full (settings block and each script).
4. **Proof commands**: the `echo ... | script; echo exit=$?` lines that show each fix.
5. At most one short "check before you use this" list.

## Scope and limits

Sources showed working hooks, not audits; this checklist combines their correct patterns with known failure modes *(inferred)*. Not covered by the sources: plugin hooks, managed/enterprise hook policies, prompt-type hooks, PermissionRequest hooks.

## Sources

- Claude (official), "Hooks in Claude Code", 2026-05-07: https://www.youtube.com/watch?v=IkaPHiMDazM&t=58 (config), &t=114 (exit 2 script, force-push regex), &t=137 (JSON deny), &t=161 (`$CLAUDE_PROJECT_DIR`).
- Better Stack, 2025-07-12: https://www.youtube.com/watch?v=Q4gsvJvRjCU&t=54 (exit codes), &t=105 (fail-open exit 1), &t=118 (.env guard).
- Skills For AI, 2026-10-17: https://www.youtube.com/watch?v=qljN6aKRez8&t=243 (hook vs CLAUDE.md).

Built from 3 videos (uploaded 2025-07-12–2026-10-17) on YouTube, 2026-11-22. Date-sensitive rules: event names, `async`, MultiEdit, default timeout.
