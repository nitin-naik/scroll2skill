# youtube_Q4gsvJvRjCU: "How Claude Code Hooks Save Me HOURS Daily" (Better Stack)

## Source
- Platform: YouTube. Creator: Better Stack, 264,000 followers. The presenter appears to be Richard Bray: his dotfiles are linked and his username shows in the terminal paths.
- URL: https://www.youtube.com/watch?v=Q4gsvJvRjCU
- Format: horizontal, 2:43 (163 s).
- Chapters: Intro 0:00, Hooks 0:19, Editing Hooks 0:55, Outro 2:08.
- Cuts: 1.29 per 10 s; first cut at 4.3 s.
- Engagement: 46,502 views, 896 likes (1.93% of views), 18 comments (0.039%). Views are 0.18x followers.
- Uploaded 2025-07-12. The terminal shows Claude Code v1.2.17-era tooling [t=00:22].

## Opening (0-3 s)
- Presenter talks to camera. A dark card with the hooks docs page ("Hooks ... Introduction") pops in at the top left at 0.5-1 s [youtube_Q4gsvJvRjCU t=00:00-00:02]. OCR read "HOOKS" from that card.
- Exact words: "Hooks are hands down one of the best features in Claude Code and for some reason a lot of people don't know about them."
- It frames hooks as an underused feature and contrasts them with subagents ("spawning parallel sub agents is cool, but creating a custom hook ... is so much cooler"). A subscribe CTA follows at [t=00:16].

## Structure
- 0:00-0:19: hook line, list of payoffs (linting, notifications, blocking), subscribe CTA, Better Stack sting.
- 0:20-0:55: the `/hooks` menu, its security warning and the 5 events; adding a PreToolUse Bash hook with `ls`.
- 0:55-2:08:
  - editing in settings.json;
  - logging commands, then a Python JSON audit log;
  - exit code 2 and the use-bun demo;
  - a .env-protection script;
  - Notification/Stop audio, phone notifications.
- 2:08-2:43: outro and a Better Stack ad.

The pace is fast and dense. Terminal close-ups are interleaved with a meme cutaway (a toddler walking off) at exit code 2 [t=01:39] and the presenter reacting to his phone [t=02:11].

## Format
- Talking head against a teal background with shelves.
- Terminal and Neovim screen recordings on a dark purple theme. Anthropic docs browser captures.
- Black title card ".claude/settings.json" [t=00:56].
- Orange hand-drawn circle annotation on code [t=01:58].
- Big white "LINK IN DESCRIPTION" caption [t=02:24].
- TTS audio sample "Task completed successfully" [t=02:06].
- CTAs: subscribe at 0:16 and 2:24; Better Stack sponsor at the end (2:29+).

## Teaching
1. **Create a hook with the `/hooks` slash command.** It shows a warning because hooks "run without confirmation" [t=00:20-00:29]. Weight: core. VERIFIED (`/hooks` exists).
   - The screen text adds: "Hooks execute arbitrary shell commands with YOUR full user permissions without confirmation"; "Multiple hooks can be registered per event, executed in parallel"; "Any changes to hooks outside of /hooks require a restart"; "Timeout: 60 seconds" [t=00:28-00:41].
   - The restart and 60 s default timeout are date-sensitive (July 2025). Current behavior is UNVERIFIED.
2. **"There are five types of hooks":** PreToolUse, PostToolUse, Notification, Stop, SubagentStop [t=00:33-00:38]. Weight: incidental. The screen confirms these 5 for that 2025 version [t=00:35]. Fact-check: **outdated.** UserPromptSubmit, SessionStart, PreCompact, SessionEnd and more now exist.
3. **Choose a matcher (Bash), write the command, save to user settings** [t=00:41-00:52]. The screen shows "PreToolUse - Matcher: Bash" and "Add new hook" saved to "User settings" [t=00:54]. Weight: supporting.
   - Minor disagreement: the title card says ".claude/settings.json" [t=00:56] while speech says user settings. The file edited lives in `~/.claude/`, i.e. user scope.
4. **Exit codes summary on screen in `/hooks` (only shown, never spoken):** "Exit code 0 - stdout/stderr not shown; Exit code 2 - show stderr to model and block tool call; Other exit codes - show stderr to user only but continue with tool call" [t=00:54]. Weight: core. VERIFIED.
5. **Hand-edit the hook in settings.json:** `"PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "..." } ] } ]` [t=00:56-01:00]. Weight: supporting. VERIFIED.
6. **Hook input is JSON**, which you can parse "in any language like Python" [t=01:10-01:22]. Docs on screen show PostToolUse input fields: `session_id`, `transcript_path`, `hook_event_name`, `tool_name`, `tool_input`, `tool_response` [t=01:13]. Weight: core. VERIFIED.
7. **Python audit log run via `uv run`.** Command `uv run ~/.claude/hooks/log_pre_tool_use.py` [t=01:19]. Output `bash_commands.json` has entries with `timestamp`, `session_id`, `tool_name`, `command`, `description` [t=01:26]. Weight: supporting. Tip: running hooks with `uv run` lets Python scripts carry their own dependencies.
8. **Exit code 2 feeds the error back to the model, "meaning it can adjust its process"** [t=01:32-01:39]. Weight: core. VERIFIED.
9. **Use-bun redirect hook.** Claude tries `npm init -y`. The hook prints `Error: Use 'bun/bunx' instead of 'npm/npx'` to `sys.stderr` and calls `sys.exit(2)`; Claude then runs `bun init -y` [t=01:32-01:52]. Weight: core, and it is the clearest demo of the three videos.
   - The terminal shows "Error: Bash operation blocked by hook: [uv run ~/.claude/hooks/use_bun.py]: Error: Use 'bun/bunx' instead of 'npm/npx'" [t=01:52].
   - The script fails open: JSON parse errors and exceptions call `sys.exit(1)` [t=01:32, t=01:45]. That is non-blocking, so a broken hook never blocks Claude.
10. **Block sensitive files (on screen only).** `is_env_file_access(tool_name, tool_input)`:
    - For tools Read/Edit/MultiEdit/Write it blocks a `file_path` containing `.env` unless it ends with `.env.sample`.
    - For Bash it uses regex patterns for `cat`, `echo >`, `touch`, `cp`, `mv` on `.env` [t=01:58].
    - Weight: supporting. Spoken: "block it from accessing sensitive files" [t=01:55].
11. **Show lint errors to Claude** [t=01:53]. Weight: incidental. Spoken only; no code shown.
12. **Matchers are optional** (e.g. Notification and Stop hooks) [t=01:58-02:04]. Weight: supporting. VERIFIED.
13. **Audio cue on Notification/Stop** ("plays audio whenever it needs my input"; TTS says "Task completed successfully") [t=02:02-02:06]. Weight: supporting.
14. **Phone notifications "with notify"** [t=02:08]. Weight: incidental. Probably **ntfy** (ntfy.sh); the caption mis-transcribes it and no screen confirms. UNVERIFIED.
15. **Hooks with MCP tools are mentioned, not shown** [t=02:18]. Weight: incidental. The video never shows it.

## Scores
- Specificity: **M/H**. Real scripts and outputs are shown, but scrolled quickly. Several claims are spoken only.
- Evidence: **H**. The npm-to-bun block-and-redirect is shown live end to end.
- Currency: **dated, July 2025.** The 5-event list, the restart requirement, the 60 s timeout and the `docs.anthropic.com` URL (now code.claude.com/docs) are date-sensitive. Exit-code semantics are still current.

## Demonstrated vs. said
- **Fail-open error handling:** exit 1 on parse error; never accidentally block.
- **Global hooks:** in user scope (`~/.claude/hooks/`), applied across all projects.
- **Steer, don't just block:** the stderr message tells Claude the alternative command, and Claude self-corrects without user input.
- **Allowlist exceptions:** `.env.sample` inside a blocklist.
- **Global audit logging:** a JSON log of every Bash command, with a `description` field, doubles as a learning/audit trail.

## Packaging
- Title: "How Claude Code Hooks Save Me HOURS Daily". A personal-benefit claim with caps emphasis; the "hours" claim is never substantiated.
- Description: dense keyword summary, docs link and creator's dotfiles link (useful for real examples). No hashtags or tags.
- Works: concrete demo, short runtime. Doesn't: hyperbolic title; the sponsor ad takes the last 15 s.

## Verdict
**USEFUL.** It has the best live proof that exit 2 + stderr makes Claude self-correct (npm to bun), plus fail-open script structure. Ignore its outdated 5-event list. `untrusted_flags`: none.
