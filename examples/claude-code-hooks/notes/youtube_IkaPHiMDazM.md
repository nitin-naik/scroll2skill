# youtube_IkaPHiMDazM: "Hooks in Claude Code" (Claude, official)

## Source
- Platform: YouTube. Creator: Claude (@claude, official Anthropic channel), 770,000 followers.
- URL: https://www.youtube.com/watch?v=IkaPHiMDazM
- Format: horizontal, medium length, 3:21 (201 s). No chapters. It is a lesson from a course ("Take the full course: claude.com/courses").
- Cuts: 1.34 per 10 s; first cut at 6.3 s.
- Engagement: 416,926 views, 2,924 likes (0.70% of views), 56 comments (0.013%). Views are 0.54x followers.
- Uploaded 2026-05-07.

## Opening (0-3 s)
- At 0.0 s the screen is blank beige. From 0.5 s the serif title card "Claude Code / Hooks" fades in, with a pixel-art Claude mascot walking in at bottom left [youtube_IkaPHiMDazM t=00:00-00:02].
- First words [t=00:02]: "Hooks let you run commands at different points in Claude code's life cycle."
- The promise comes at [t=00:09-00:16]: "hooks are deterministic. They always run."

## Structure
1. 0:00-0:16: definition (deterministic).
2. 0:18-0:50: "Why use hooks" title card, then the CLAUDE.md vs hook contrast, then use cases. B-roll of CLAUDE.md, settings.json and a command log.
3. 0:50-1:20: "How they work": settings.json anatomy (event, matcher, command), and 5 events shown as a list card with mini screenshots.
4. 1:22-2:25: "A practical example": the auto-format PostToolUse hook, then a block-dangerous-commands.sh walkthrough.
5. 2:25-2:45: "Sharing hooks with your team": project-level settings and `$CLAUDE_PROJECT_DIR`.
6. 2:45-3:21: talking-head recap.

Attention is held by alternating presenter, title card and code close-up about every 6-8 s. Each section opens with a beige serif title card.

## Format
- Presenter is framed mid-shot in a warm, dim room.
- Section cards use a beige background, black serif type and the pixel mascot.
- Code is shown as VS Code screen recordings (dark theme), zoomed and cropped, with the cursor typing live, e.g. autocomplete after `$CLAUDE_PROJECT_DIR/` [t=02:41].
- No burned-in captions. Soft music under the recap. No subscribe CTA in the video; the only CTA is the course link in the description.

## Teaching
1. **Hooks are deterministic; a CLAUDE.md instruction is not.** If you tell Claude in CLAUDE.md to run prettier after every edit, "most of the time it will do that, but sometimes it won't". A hook "makes it happen every single time" [t=00:07-00:34]. Weight: core.
2. **Common use cases:** auto-format after edits, log every executed command for compliance, block dangerous operations (such as modifying production files), and notify yourself when Claude finishes [t=00:37-00:49]. Weight: supporting.
3. **Where and how they are configured.** Hooks live in settings.json: "pick an event, optionally set a matcher for which tool it applies to, and provide a command". On screen: `"hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-commands.sh" } ] } ] }` [t=00:52-01:00, t=00:58]. Weight: core. VERIFIED.
4. **The events it names:** UserPromptSubmit (before Claude processes the prompt), PreToolUse, PostToolUse, Notification, Stop (when Claude finishes responding) [t=01:03-01:18]. Weight: supporting. Fact-check: incomplete. Current Claude Code also has SessionStart, SessionEnd, SubagentStop, PreCompact, PermissionRequest and others.
5. **Auto-format recipe.** A PostToolUse hook; the script checks the file extension and runs the matching formatter: prettier for TS, gofmt for Go, Ruff for Python [t=01:22-01:45]. Weight: core.
   - Speech says the matcher is "edit or multi-edit". The screen shows `"matcher": "Edit|MultiEdit|Write"` [t=01:38]; an earlier frame shows `"Edit|Write"` [t=00:58]. The screen wins: include Write.
   - The matcher is a regex with alternation (`|`). VERIFIED.
   - MultiEdit: UNVERIFIED whether the tool still exists in current Claude Code. It is harmless to keep in the regex.
6. **Async logging hook (on screen only).** `"matcher": "Bash"`, command `"$CLAUDE_PROJECT_DIR"/.claude/hooks/log-commands.sh`, `"async": true`, `"timeout": 10` [t=01:30, t=02:49]. The log output is JSON lines with `timestamp` and `command` [t=00:42]. Weight: supporting.
   - `timeout` is in seconds. VERIFIED.
   - `async`: UNVERIFIED here (I believe it was added in 2026). The video does not explain it.
7. **The hook input arrives as JSON on stdin.** A PreToolUse hook "receives a tool name and input as JSON on stdin" [t=01:49-01:55]. Weight: core. VERIFIED.
8. **Exit codes.** "Exit code zero means proceed. Exit code two means block". On exit 2, stderr "gets fed back to Claude as feedback so Claude knows why it was blocked and can adjust" [t=01:57-02:10]. The script header on screen says: `# Exit 2 = block (stderr feeds back to Claude), Exit 0 = allow` [t=01:54]. Weight: core. VERIFIED.
   - The video omits that other non-zero exit codes are non-blocking errors whose stderr goes to the user, not to Claude.
9. **Example blocking script (on screen)** [t=01:54-02:09]:
   - `COMMAND=$(jq -r '.tool_input.command')`
   - Blocks `rm` with `-rf`/`-f` flags aimed at `/`, `.` or `~`, with the message "Blocked: destructive rm command" sent to stderr (`>&2`), then `exit 2`.
   - Blocks `git\s+push\s+.*--force[^-]` with "Blocked: force push - use --force-with-lease instead" and `exit 2`.
   - Ends with `exit 0`.
   - Weight: core. **Bug found:** `--force[^-]` requires a character after `--force`, so a plain `git push origin main --force` at the end of the line is NOT blocked. Use `--force($|[^-])` instead. Spoken examples: block writes to a production config dir, `rm -rf`, commits to main [t=02:12-02:21].
10. **Structured JSON deny instead of exit 2 (on screen only)** [t=02:17]. The script runs `if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'`, then `jq -n '{ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: "DROP TABLE blocked by hook. Use a migration..." } }'`, then `exit 0`. Weight: core.
    - VERIFIED: this is the current PreToolUse decision format.
    - The JSON is only parsed on exit 0, so the `exit 0` is required. The video shows this but never says it.
11. **Sharing with a team.** Hooks in `.claude/settings.json` are project-level and can be checked into the repo, so "your entire team gets the same hooks automatically" [t=02:26-02:34]. Weight: core. VERIFIED.
12. **Use `$CLAUDE_PROJECT_DIR`** so script paths work whatever Claude's current working directory is. On screen it is quoted with escaped quotes: `"\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/..."` [t=02:36, t=02:41]. Weight: core. VERIFIED.
13. **Configure via `/hooks` or settings.json** [t=03:00]. Weight: supporting. VERIFIED (the `/hooks` command exists).
14. **The rule to remember:** "If something needs to happen every time without fail, don't put it in a prompt. Put it in a hook." [t=03:10]. Weight: core.

## Scores
- Specificity: **H**. Real JSON, real scripts, regexes and exit codes on screen.
- Evidence: **M/H**. The config and scripts are shown in full and the log output is shown. A hook actually blocking a live command is not demonstrated.
- Currency: uploaded 2026-05-07, recent, official. The event list is incomplete. MultiEdit and `async` are version-dependent and date-sensitive.

## Demonstrated vs. said
- **Quoting:** the command path is wrapped in escaped quotes to survive spaces. Shown, not explained.
- **stderr:** block messages are sent to stderr with `>&2`.
- **Two ways to block:** exit 2 with stderr, or exit 0 with `permissionDecision: "deny"` JSON. Both are shown; only exit 2 is explained.
- **One script per concern:** separate scripts in `.claude/hooks/` (auto-format.sh, log-commands.sh, block-dangerous-commands.sh).
- **Async logging:** the non-blocking logger is marked async with a short timeout so it never slows the agent.
- **Redirect, don't just refuse:** the block messages tell Claude what to do instead ("use --force-with-lease", "use a migration").

## Packaging
- Title: "Hooks in Claude Code". Plain and searchable. The official channel carries the authority.
- Caption: one-sentence promise ("deterministic control ... at key lifecycle events") plus three outcomes (auto-format, block dangerous ops, share with team). No hashtags or tags.
- Works: authority, and a clean three-benefit caption. Doesn't: a bland title with no hook. That is fine for a course lesson.

## Verdict
**USEFUL.** It is the most precise source here. It covers both blocking mechanisms (exit 2 and JSON `permissionDecision`), the `$CLAUDE_PROJECT_DIR` pattern and async logging, from the official channel. Watch for the force-push regex bug. `untrusted_flags`: none.
