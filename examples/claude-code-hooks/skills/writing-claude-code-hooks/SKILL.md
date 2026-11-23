---
name: writing-claude-code-hooks
description: Write working Claude Code hooks (settings.json entry plus scripts) for concrete behaviour - block dangerous commands, protect files, auto-format/lint after edits, log commands, notify on finish, inject context at session start, or keep Claude working until tests pass. Use when the user says "write a hook", "make Claude always/never...", "block Claude from...", "run X after every edit", "notify me when Claude finishes", or asks which hook event to use. Do not use for reviewing or debugging existing hooks (use auditing-claude-code-hooks), git hooks/pre-commit, React hooks, or video/content "hooks".
---

# Writing Claude Code hooks

Answer the user's actual request first and fully: deliver finished config and scripts, ready to paste. The steps below are the minimum to cover, not a template. Use your own knowledge of Claude Code where these notes are silent, and point to current docs (code.claude.com/docs, "Hooks reference") for version-specific details.

## When a hook is the right tool

A hook is a shell command Claude Code runs at a fixed lifecycle moment, every time, whether or not the model "remembers". Pick it when the answer to "must this happen every time, without asking?" is yes.

- A CLAUDE.md line is a request; a PreToolUse hook that blocks enforces it.
- Repeatable procedure Claude should choose to run -> skill, not hook.
- Pure "never touch path X" -> also add a `permissions.deny` rule (e.g. `"Edit(./migrations/**)"`, `"Read(./.env)"`) as a second layer; the hook adds a custom message and logic the deny rule can't.
- Hooks cost zero context unless their output is fed back to Claude.

## Steps

1. **Event + matcher** per behaviour (table below). Several behaviours -> several entries in one merged `hooks` block, one script per concern.
2. **Scope**: `.claude/settings.json` (project, committed, whole team gets it), `.claude/settings.local.json` (project, just you, git-ignored), `~/.claude/settings.json` (all your projects).
3. **Language**: bash + `jq` for short checks; Python 3.8+ (stdlib only) when the repo is Python, `jq` may be missing, or logic is more than ~3 conditions.
4. **Write scripts** in `.claude/hooks/` (project) or `~/.claude/hooks/` (user), with a shebang, `chmod +x`.
5. **Write the settings block**: show it standalone and say "merge under your existing `hooks` key; don't replace other entries".
6. **Check failure modes** (Rules) before handing it over.
7. **Test commands** the user can run without Claude, plus how to verify live.

## Events (verify against `/hooks` on the user's version)

| Event | Fires | Matcher matches | Can block? |
|---|---|---|---|
| PreToolUse | before a tool call | tool name | yes: exit 2, or JSON `permissionDecision: "deny"` |
| PermissionRequest | when a permission dialog would show | tool name | yes: JSON allow/deny |
| PostToolUse | after a tool call succeeds | tool name | can't undo; exit 2 / `decision:"block"` sends feedback to Claude |
| UserPromptSubmit | user submits a prompt | (none) | yes: exit 2 erases the prompt; stdout on exit 0 becomes context |
| Notification | Claude needs permission or is idle | notification type | no |
| Stop / SubagentStop | agent / subagent finishes responding | (none) | yes: exit 2 or `decision:"block"` makes Claude continue |
| PreCompact | before compaction | `manual` / `auto` | no |
| SessionStart | start / resume / clear / compact | `startup`, `resume`, `clear`, `compact` | no; stdout becomes context |
| SessionEnd | session ends | reason | no |

**Matchers**: case-sensitive regex on tool name: `Bash`, `Edit|MultiEdit|Write|NotebookEdit`, `mcp__github__.*`; `*` or omitted = all. Keep `MultiEdit` in matchers: harmless if the version lacks it.

**`tool_input` fields**: Bash `.command`; Edit/MultiEdit/Write/Read `.file_path` (absolute); NotebookEdit `.notebook_path`; PostToolUse also has `.tool_response`.

## Settings format

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command",
                     "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh",
                     "timeout": 10 } ] }
    ]
  }
}
```
Always `"$CLAUDE_PROJECT_DIR"` (quoted) for project scripts. `timeout` is seconds (default 60): guards 10, formatters/linters 30-60, test runs 120-300. Logging-only hooks can add `"async": true` *(version-dependent)*.

## Script contract

- **Input**: one JSON object on stdin: `session_id`, `transcript_path`, `cwd`, `hook_event_name`, plus event fields (`tool_name`, `tool_input`, `tool_response`, `prompt`, `stop_hook_active`). Read stdin once: `INPUT=$(cat)` / `json.load(sys.stdin)`.
- **Exit codes**: `0` ok (stdout to transcript; context for UserPromptSubmit/SessionStart). `2` blocking: **stderr** goes to Claude. Any other code (incl. 126 not-executable, 127 not-found): non-blocking, stderr to the user, action continues.
- **JSON output** is only parsed on exit 0: PreToolUse `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`; PostToolUse/Stop `{"decision":"block","reason":"..."}`; any event `{"continue":false,"stopReason":"..."}`. Build JSON with `jq -n --arg r "$MSG" '...'` or `json.dumps`, never string concatenation.
- **Steer, don't just refuse**: the message tells Claude what to do instead ("Use bun/bunx instead of npm/npx", "use --force-with-lease", "change models.py and ask the user to run makemigrations").

## Rules

- **Fail policy**: guards fail closed (bad input / missing `jq` -> exit 2 with a message); formatters, loggers, notifiers fail open (exit 0 or 1). State the choice in a comment.
- **Path guards**: resolve `file_path` relative to `$CLAUDE_PROJECT_DIR`, match whole path segments (`migrations/` dir, not `migrations_helper.py`), match `.env` and `.env.*` but allow `.env.example` / `.env.sample` / `.env.template`. Ask, or default and say so, whether tool-generated writes (e.g. `makemigrations`, `alembic revision` via Bash) are allowed: default yes, they aren't Claude hand-edits.
- **Bash side of file guards**: Edit/Write matcher is primary. Optionally add a Bash check for write-ish commands naming the path (`>`, `tee`, `sed -i`, `cp`, `mv`, `rm`); allow reads. Say in one line that string checks are bypassable (`bash -c`, `python -c`) and `permissions.deny` is the stronger layer.
- **Command regexes**: catch end-of-line and flag order. `--force[^-]` misses a trailing `--force`; use `(^|\s)(-f|--force)(\s|$)`. For `rm`, parse flags (`-rf`, `-fr`, `-r -f`, `-R`) and check targets (`/`, `~`, `.`, `*`, `$HOME`) instead of one literal pattern.
- **Formatters (PostToolUse)**: run only on the edited file; skip if it no longer exists or has the wrong extension. Find the binary in order: project `.venv/bin/` -> `PATH` -> `uvx`/`npx` fallback; if none, exit 0 with a stderr note. Pass `--force-exclude` (ruff) or the tool's equivalent so project excludes apply to explicit paths. Ruff order: `ruff check --fix` then `ruff format`. If lint errors remain, exit 2 with the first ~40 lines on stderr so Claude fixes them; formatting changes alone exit 0. Note that the file now differs from what Claude wrote; Claude re-reads before its next edit.
- **Stop hooks** that block must exit 0 when `stop_hook_active` is `true`, `cd "$CLAUDE_PROJECT_DIR"` first, check the gating command exists, and pass the last ~30 lines of failure output to Claude.
- Hooks run with the user's full permissions. Quote every variable; never `eval` input.
- Hooks are loaded at session start: after editing settings outside Claude Code, restart Claude Code (or open `/hooks` to review) and confirm the hook is listed.

## Output format

1. One line per hook: event + matcher and why.
2. The settings.json block, with the file it goes in.
3. Each script, complete, with shebang; one line under each on any non-obvious design choice.
4. Setup commands (`mkdir -p`, `chmod +x`).
5. Tests: `echo '<sample JSON>' | path/to/script; echo "exit=$?"` for pass and block cases of each hook (use absolute `file_path` values; clean up any temp files).
6. Live check: `/hooks` lists it; `claude --debug` shows it running.
7. One short "check before you use this" list (bypasses, behaviour the user may not expect).

## Example: Stop hook that keeps Claude working until tests pass

```bash
#!/usr/bin/env bash
INPUT=$(cat)
[ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ] && exit 0   # avoid infinite loop
cd "$CLAUDE_PROJECT_DIR" || exit 0
command -v npm >/dev/null && [ -f package.json ] || exit 0              # fail open
OUT=$(npm test 2>&1) || { echo "Tests failing, fix before stopping:" >&2; echo "$OUT" | tail -n 30 >&2; exit 2; }
exit 0
```

## Scope and limits

Videos covered: PreToolUse blocking (exit 2 and JSON deny), PostToolUse auto-format, command logging, Notification/Stop sound alerts, phone push via ntfy (UNVERIFIED), `$CLAUDE_PROJECT_DIR`, team sharing. From my own knowledge, not the sources: PermissionRequest, `updatedInput`, SessionStart context injection, `CLAUDE_ENV_FILE`, prompt-type hooks, plugin `hooks/hooks.json`, hooks in skill/subagent frontmatter, managed hooks, Windows.

## Sources

- Claude (official), "Hooks in Claude Code", 2026-05-07: https://www.youtube.com/watch?v=IkaPHiMDazM - deterministic vs CLAUDE.md &t=7, config &t=58, auto-format `Edit|MultiEdit|Write` &t=98, exit 2 script + force regex &t=114, JSON deny &t=137, project scope &t=146, `$CLAUDE_PROJECT_DIR` &t=161, async logger &t=90.
- Better Stack, "How Claude Code Hooks Save Me HOURS Daily", 2025-07-12: https://www.youtube.com/watch?v=Q4gsvJvRjCU - `/hooks` &t=20, exit codes &t=54, input JSON &t=73, use-bun exit 2 steer &t=92, fail-open exit 1 &t=105, .env guard allowing .env.sample &t=118, matchers optional &t=118.
- Skills For AI, "Skills vs Subagents vs MCP vs Hooks vs Plugins", 2026-10-17: https://www.youtube.com/watch?v=qljN6aKRez8 - zero context cost &t=224, hook vs CLAUDE.md &t=243, decision rule &t=329.
- *(inferred / own knowledge)*: event table beyond the 5 shown in videos, `tool_input` field table, permissions.deny layering, formatter binary discovery, Stop-hook template.

Built from 3 videos (uploaded 2025-07-12–2026-10-17) on YouTube, 2026-11-22. Date-sensitive rules: event list, `async` flag, MultiEdit tool name, restart/`/hooks` review behaviour, 60 s default timeout.
