# How I use Claude Code (Senior Software Engineer Tips) — Maddy Zhang

## Source
- Platform: YouTube. Creator: Maddy Zhang, @maddyzhang, ~102K subscribers; ex-Google SWE and tech-career creator.
- URL: https://www.youtube.com/watch?v=MzhIr7BfpI0
- Format: medium-length horizontal video, 9:46 (586 s). Uploaded 2026-04-05.
- Engagement: 265,055 views, 6,427 likes, 202 comments. 2.42 likes per 100 views (strong); 3.14 comments per 100 likes.

## Opening (0:00–0:30)
Talking head in a pink-lit desk setup. A kinetic caption reads "MOST DEVELOPERS / ARE USING A.I. LIKE A [Google]" next to a fake Google search bar. Spoken: "Most developers are using AI like a slightly better Google search, but as a senior engineer, that's not how you should be using it." That's followed by a credentials roll (Google, Amazon, IBM, Microsoft) and the promise: "by the end of this video, you'll have a concrete workflow you can start using immediately." The framing is about status (how seniors do it), not a specific problem.

## Structure (chapters from the description)
- 0:00 Most developers use AI wrong
- 0:54 What Claude Code is
- 1:38 Setting up CLAUDE.md (`/init`, then a model note at about 2:41)
- 2:59 Plan mode (and the `/clear` habit at 3:30, then custom slash commands at 4:05)
- 4:37 Validation loop (hooks)
- 5:40 Parallel agents (panes, git worktrees, subagents at 6:27, skills at 7:12)
- 7:50 MCP servers
- 8:24 Practical tips (specific prompts, small steps, plan-execute-review) and recap

## Format
Mostly talking head with frequent cuts (1.11 cuts per 10 s), plus motion-graphic text cards and short picture-in-picture screen recordings of a real project ("chess-doge", a chess app). Screen demos: `claude` launching then `/init` exploring; the `/model` picker (Default/Opus 4.6/Sonnet 4.6/Haiku 4.5, plus an effort setting); `/clear`; plan mode on (Shift+Tab) and the plan-approval prompt; a background dev-server verification; `claude --worktree multi-player-mode`; a `.claude/agents/security-reviewer.md` file; and a `SKILL.md` in `.claude/skills/`. Hooks, MCP and the PR-summary command are only talked about, never shown.

## Teaching
1. **Run `/init` before your first real prompt** in any new codebase. It generates `CLAUDE.md`. (She says "backslash init"; it's a slash command.)
2. **What CLAUDE.md should cover:** what the project does, where things live, and how work gets done. That means stack, conventions, key file paths and the real dev commands for test, build and lint. Examples on screen: "build command is `npm run dev` and not yarn", "which folder holds your API routes", "you use functional components with hooks". She also suggests describing yourself so it codes like you.
3. **Keep CLAUDE.md lean: about 100–200 lines max.** More context dilutes the signal. This is her rule of thumb, not a published number.
4. **Model:** Opus by default for complex work. Sonnet if you hit limits (she says Claude switches automatically). Haiku for lightweight tasks. On screen, the `/model` picker also shows an **effort** setting (Medium effort by default, adjusted with arrow keys) that she never mentions.
5. **Use plan mode before writing any code.** Toggle it with **Shift+Tab** (on screen: "plan mode on (shift+tab to cycle)"). Review the plan, push back on it, or edit it directly. On screen, the plan file is saved at `~/.claude/plans/<name>.md`, **Ctrl+G opens it in your editor (Vim)**, and the approval options are "Yes, auto-accept edits / Yes, manually approve edits / Tell Claude what to change (shift+tab to approve with this feedback)". Her demo plan ends with a **Verification** section listing concrete checks (for example "Bar shows 50/50 at game start", "Responsive: works on different window sizes"). Copy that pattern.
6. **`/clear` between tasks.** The context window is finite, quality drops as it fills, and auto-summarizing stale history wastes compute. One task per clean session. The up arrow recalls past sessions or prompts. (`/resume` is the more precise tool; she doesn't name it.)
7. **Custom slash commands:** saved prompts in `.claude/commands/` as plain markdown. Her example is a PR-summary command that covers what changed, why, risks and how to test it. Her rule: **anything you do more than once a week gets a command.**
8. **Validation loop:** wire build, tests and type-check into **hooks** so they run after every change Claude makes, and failures feed back to Claude. Or put it in CLAUDE.md: "After every edit, run the build, run the test, run the type check. If anything fails, treat it as a blocker and [solve] it before moving on." She estimates 20 minutes of setup. FLAG: no hook config is shown. Running a full build and test suite after *every* edit is slow on real projects; the usual pattern is a fast type-check or lint on PostToolUse and the full suite on Stop. Instructions in CLAUDE.md are advisory, while hooks are enforced.
9. **Parallel work, level 1:** several Claude Code panes in the IDE, each on a different problem, as long as they touch separate files.
10. **Parallel work, level 2: git worktrees.** One worktree and one session per feature or fix branch, then review and merge. **On screen only:** she uses the built-in flag `claude --worktree multi-player-mode`, and the session's working directory becomes `.claude/worktrees/multi-player-mode`. That's simpler than running `git worktree add` by hand, but she doesn't say so.
11. **Subagents:** define them in `.claude/agents/` (she says ".claude.agents"). Each has a name, allowed tools ("rules" in the transcript is likely "tools") and a focused instruction set. Each runs in an isolated context and returns a result, which keeps the main session clean. **On screen:** `code-reviewer.md`, `db-specialist.md`, `security-reviewer.md` and `test-writer.md`. The security reviewer body has these sections:
    - **What to check:** injection, auth, data exposure, dependency risks (`npm audit`), missing input validation, hardcoded secrets, path traversal.
    - **How to work:** "Read the relevant source files thoroughly before making any claims", check `package-lock.json` and `.env` handling, grep for `eval`, `innerHTML`, `dangerouslySetInnerHTML`.
    - **Output format:** Severity Critical/High/Medium/Low/Info, Location file:line, Issue, Risk, Fix. Ends with "Summarize with a table of findings sorted by severity. If no issues are found in a category, say so briefly — don't pad the report."
12. **Skills:** a markdown playbook (`SKILL.md`; on screen there's a `.claude/skills/.../SKILL.md` and a `pr-summary` entry) for multi-step workflows such as code review, refactor or release. Unlike a command it can reference other files, include multi-step logic and be used by subagents. She calls it "institutional knowledge that travels with your codebase".
13. **MCP servers:** connect GitHub, Slack, databases or Perplexity once, then prompts like "pull comments from this PR and address them" or "check Slack for the latest design feedback before writing code" just work. No setup commands are shown (for example `claude mcp add`).
14. **Rules for prompting:** (a) be specific: which files, constraints, expected behaviour. (b) Make small steps, because a 2-file diff that breaks one thing is about a 5-minute fix and a 15-file diff that breaks three is not. (c) Always **plan, then execute, then review**. Every feature maps onto one of those three phases.

## Demonstrated vs. said
- **The `--worktree` flag** (`claude --worktree <name>`) is the most useful thing in the video, and it's shown, never named.
- **A verification checklist inside the plan.** Her plan includes explicit acceptance checks, and Claude then ran background dev-server commands to verify (on screen: "Start dev server for verification... completed"). That's the "validation loop" actually happening, but she presents it as plan mode.
- The **Ctrl+G edit-plan-in-editor** shortcut and the plan file path `~/.claude/plans/`.
- The **effort setting** in `/model`.
- The subagent file is a full reusable template: scope checklist, then working method, then strict output schema, then a "don't pad" instruction.
- The `/clear` before `/model` in the demo shows the reset-per-task habit.

## Packaging
- Title: "How I use Claude Code (Senior Software Engineer Tips)". The same "How I use" formula as many in the niche, with a seniority hook. Strong click-through for career-minded developers.
- Description: a pain-point opener, a checklist of covered topics, chapter timestamps, and 17 hashtags plus 29 tags (including "#chatgpt" and "claude vs chatgpt" for reach). Good for search, but the tags somewhat over-promise.
- What works: a clean progression from setup to planning to verification to scaling (parallel work, subagents, skills, MCP), a memorable rule ("more than once a week = slash command"), and a recap card.
- What doesn't: broad and shallow. Hooks, MCP and commands are described but never configured, and most screen time is talking head. Small transcript slips ("backslash", ".claude.agents") would confuse beginners.

## Verdict
USEFUL. It's a well-ordered, current (2026) overview, and the screen recordings show real artifacts worth copying: the subagent template, plan verification checklists and `claude --worktree`. The spoken advice is mostly standard, and hooks and MCP need other sources for the actual setup.
