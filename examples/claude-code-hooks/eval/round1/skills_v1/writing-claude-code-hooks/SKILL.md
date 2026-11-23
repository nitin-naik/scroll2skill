---
name: writing-claude-code-hooks
description: Write a working Claude Code hook (settings.json entry plus script) for a concrete behaviour - block dangerous commands, protect files, auto-format after edits, log commands, notify on finish, inject context at session start, or keep Claude working until tests pass. Use when the user says "write a hook", "make Claude always/never...", "block Claude from...", "run X after every edit", "notify me when Claude finishes", or asks which hook event to use. Do not use for reviewing existing hooks (use auditing-claude-code-hooks), for git hooks/pre-commit, React hooks, or video/content "hooks".
---

# Writing Claude Code hooks

Answer the user's actual request first and fully: deliver the finished config and script, ready to paste. The steps below are the minimum to cover, not a template. Use your own knowledge of Claude Code where these notes are silent, and check the current docs (code.claude.com/docs, "Hooks reference") if the user's version may differ.

## When a hook is the right tool

A hook is a shell command Claude Code runs at a fixed lifecycle moment. It is deterministic: it runs every time, whether or not the model "remembers". Pick it when the answer to "must this happen every time, without asking?" is yes. [Claude official t=0:07; Skills For AI t=5:29]

- Rule Claude broke twice -> CLAUDE.md first; if it must never happen -> PreToolUse hook. "A CLAUDE.md line is a request; a hook that exits 2 enforces it." [Skills For AI t=4:03]
- Repeatable procedure Claude should choose to run -> skill, not hook.
- Hooks cost zero context unless they print output that gets fed back. [Skills For AI t=3:44]

## Steps

1. **Pick the event** (table below) and the **matcher**.
2. **Pick the scope**: `.claude/settings.json` (project, commit it so the whole team gets it) [Claude official t=2:26], `.claude/settings.local.json` (project, just you), `~/.claude/settings.json` (all your projects) [Better Stack t=0:54].
3. **Write the script** in `.claude/hooks/` (project) or `~/.claude/hooks/` (user), one script per concern, `chmod +x`. [Claude official t=1:22]
4. **Write the settings entry** with the command path quoted.
5. **Check failure modes** (section below) before handing it over.
6. **Give a test command** the user can run without starting Claude, plus how to verify live.

## Events (current set; verify against `/hooks` on the user's version)

| Event | Fires | Matcher matches | Can block? |
|---|---|---|---|
| PreToolUse | before a tool call | tool name | yes: exit 2, or JSON `permissionDecision: "deny"` |
| PermissionRequest | when a permission dialog would show | tool name | yes: JSON allow/deny |
| PostToolUse | after a tool call succeeds | tool name | no (tool already ran); exit 2 / `decision:"block"` feeds stderr/reason back to Claude |
| UserPromptSubmit | user submits a prompt, before Claude sees it | none | yes: exit 2 erases the prompt; stdout on exit 0 is added as context |
| Notification | Claude needs permission or is idle waiting | notification type (optional) | no |
| Stop / SubagentStop | main agent / subagent finishes responding | none | yes: exit 2 or `decision:"block"` forces Claude to continue |
| PreCompact | before compaction | `manual` / `auto` | no |
| SessionStart | session start/resume/clear/compact | `startup`, `resume`, `clear`, `compact` | no; stdout is added as context |
| SessionEnd | session ends | reason | no |

Older videos list only 5 events (July 2025) [Better Stack t=0:35]; the list above is from current docs *(inferred from my own knowledge; newer events may exist)*.

**Matchers**: case-sensitive regex on the tool name: `Bash`, `Edit|MultiEdit|Write` [Claude official t=1:38], `mcp__github__.*` for MCP tools, `*` or omitted for all. Matchers are optional for events without tools (Notification, Stop) [Better Stack t=1:58].

## Settings format

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh",
            "timeout": 10 }
        ]
      }
    ]
  }
}
```
[Claude official t=0:58]. `timeout` is seconds (default 60). Use `"$CLAUDE_PROJECT_DIR"` (quoted) for project scripts so the hook works from any cwd and with spaces in the path [Claude official t=2:41]. Merge into existing `hooks` keys; never overwrite the user's other hooks. A logging-only hook can be non-blocking with `"async": true` plus a short timeout [Claude official t=1:30] *(version-dependent; omit if the user's version rejects it)*.

## Script contract

- **Input**: one JSON object on stdin. Common fields: `session_id`, `transcript_path`, `cwd`, `hook_event_name`; tool events add `tool_name`, `tool_input` (e.g. `.tool_input.command`, `.tool_input.file_path`); PostToolUse adds `tool_response`; UserPromptSubmit adds `prompt`; Stop adds `stop_hook_active` [Better Stack t=1:13]. Read stdin once into a variable: `INPUT=$(cat)`.
- **Exit codes** [Better Stack t=0:54, Claude official t=1:54]:
  - `0` success. stdout goes to the transcript only, except UserPromptSubmit/SessionStart where it becomes context for Claude.
  - `2` blocking error: stderr is fed to Claude (PreToolUse: call blocked; Stop: Claude keeps going).
  - anything else: non-blocking error, stderr shown to the user, action continues.
- **JSON output** (only parsed on exit 0): PreToolUse `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny|allow|ask","permissionDecisionReason":"..."}}` [Claude official t=2:17]; PostToolUse/Stop `{"decision":"block","reason":"..."}`; any event `{"continue":false,"stopReason":"..."}` to halt Claude; `additionalContext` inside `hookSpecificOutput` for SessionStart/UserPromptSubmit/PostToolUse.
- **Steer, don't just refuse**: the block message tells Claude what to do instead ("Use bun/bunx instead of npm/npx", "use --force-with-lease"), and Claude self-corrects [Better Stack t=1:32-1:52; Claude official t=2:05].
- **Exit 1 on your own errors** (bad JSON, missing field) unless the hook is a security guard: then decide fail-open vs fail-closed explicitly and say which [Better Stack t=1:45].

## Rules

- Message to Claude goes to **stderr** (`>&2`) with exit 2. stdout with exit 2 is ignored.
- Regexes on commands must catch end-of-line and flag order: the official example `--force[^-]` misses `git push origin main --force`; use `--force($|[^-=])` or `(^|\s)(-f|--force)(\s|$)` [Claude official t=1:54, bug noted in study].
- Command-string blocklists are bypassable (`bash -c`, variables, `python -c`). Say so in one line, and also block the file path with an Edit/Write matcher when protecting files.
- Stop hooks that exit 2 must check `stop_hook_active` and exit 0 when it is `true`, or Claude loops forever.
- PostToolUse formatters: run only on the edited file (`.tool_input.file_path`), skip missing files, never exit 2 on formatter failure unless you want Claude to fix it.
- Require `jq` explicitly (`command -v jq >/dev/null || { echo "jq missing" >&2; exit 1; }`) or write the script in Python.
- Hooks run with the user's full permissions. Quote every variable; never `eval` input.
- Settings edits made outside Claude Code may need review in `/hooks` or a restart before they apply [Better Stack t=0:28, dated 2025; *(current behaviour: snapshot at startup)*].

## Output format

1. One line: which event + matcher and why.
2. The settings.json block (merged form) and the file it goes in.
3. Each script, complete, with shebang.
4. Setup commands (`mkdir -p`, `chmod +x`).
5. Test: `echo '<sample JSON>' | path/to/script; echo "exit=$?"` for one pass case and one block case.
6. Live check: run `/hooks` to confirm it is registered; `claude --debug` to see hook execution.
7. At most one short "check before you use this" list (limits, bypasses).

## Scope and limits

Videos covered: PreToolUse blocking (exit 2 and JSON deny), PostToolUse auto-format, command logging, Notification/Stop sound alerts, phone push via ntfy (UNVERIFIED), `$CLAUDE_PROJECT_DIR`, team sharing. Not covered by the sources (from my own knowledge): PermissionRequest, `updatedInput`, SessionStart context injection, `CLAUDE_ENV_FILE`, prompt-type hooks, plugin `hooks/hooks.json`, hooks in skill/subagent frontmatter, enterprise managed hooks.

## Sources

- Claude (official), "Hooks in Claude Code", 2026-05-07: https://www.youtube.com/watch?v=IkaPHiMDazM - config t=58, auto-format &t=82, exit 2 script &t=114, JSON deny &t=137, project scope &t=146, `$CLAUDE_PROJECT_DIR` &t=161.
- Better Stack, "How Claude Code Hooks Save Me HOURS Daily", 2025-07-12: https://www.youtube.com/watch?v=Q4gsvJvRjCU - `/hooks` &t=20, exit codes &t=54, input JSON &t=73, use-bun exit 2 &t=92, .env guard &t=118, sound on Stop &t=122.
- Skills For AI, "Skills vs Subagents vs MCP vs Hooks vs Plugins", 2026-10-17: https://www.youtube.com/watch?v=qljN6aKRez8 - hook vs CLAUDE.md &t=243, decision rule &t=329.

Built from 3 videos (uploaded 2025-07-12–2026-10-17) on YouTube, 2026-11-22. Date-sensitive rules: event list, `async` flag, MultiEdit tool name, restart/`/hooks` review requirement, 60 s default timeout.
