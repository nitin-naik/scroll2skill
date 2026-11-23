# How I use Claude Code (+ my best tips) — Steve (Builder.io)

## Source
- Platform: YouTube. Creator: Steve (Builder.io), @Steve8708, ~141K subscribers.
- URL: https://www.youtube.com/watch?v=n7iT5r0Sl_Y
- Format: medium-length horizontal video, 12:43 (763 s). Uploaded 2025-07-11.
- Engagement: 349,207 views, 5,936 likes, 365 comments. 1.70 likes per 100 views; 6.15 comments per 100 likes (high discussion, likely because of the `--dangerously-skip-permissions` advice and the Cursor comparison).
- Last 2 minutes are a product plug for Builder.io / Fusion.

## Opening (0:00–0:30)
Talking head over his Cursor IDE, with a Claude Code diff visible. He opens with a credibility claim and a switch story: "for the last several weeks [I] switched over from Cursor's agent to Claude Code and I'm not looking back... Here's how I use Claude Code and my best tips." By 0:07 he's into tip 1 (install the IDE extension). No hook graphic. The promise is a practitioner's personal tip list from someone who left a competing tool.

## Structure (YouTube chapters)
- 0:00 Introduction
- 0:08 Setup and terminal UI (IDE extension, multiple panes, file auto-context)
- 0:51 Model selection (`/model`, Opus vs Sonnet)
- 1:46 Agent permissions (`/clear`, up arrow, `--dangerously-skip-permissions`)
- 2:42 Automated PR reviews (`/install-github-app`)
- 3:45 Terminal tricks (`/terminal-setup`, shift-drag, Ctrl+V images)
- 4:24 Navigation and stopping (Esc, Esc Esc)
- 4:56 Large codebases (18,000-line file)
- 5:41 Claude Code vs Cursor agent (whiteboard)
- 7:10 Pricing (Max plan)
- 7:44 Queuing messages
- 8:48 Custom commands, hooks, and memory (`#`, CLAUDE.md hierarchy)
- 10:28 Visual interface with Builder (plug)
- 12:27 Conclusion

## Format
Mostly a single take: webcam bottom-left over a live Cursor window with Claude Code in two side panes. Demos are real but brief: the `/model` picker, `/install-github-app` and the generated `claude-code-review.yml`, `/terminal-setup`, the queued-message demo, and a generated `CLAUDE.md` plus `.claude/commands`. There are Excalidraw-style whiteboard slides for the Cursor vs Anthropic argument, plus anthropic.com/pricing. The Builder.io Fusion web UI shows up at the end. Cut rate is low (0.17 cuts per 10 s).

## Teaching
1. **Install the Claude Code IDE extension** (VS Code, Cursor, Windsurf). It mostly gives you a quick launcher, and **the file open in the editor is pulled into context automatically**. On screen at 0:09, the Marketplace page notes the extension requires the Claude Code CLI to be installed separately.
2. **Run several Claude Code panes in parallel**, but only on tasks that touch different files or different parts of the codebase. On screen, the CLI's own tip line says "Use git worktrees to run multiple Claude sessions in parallel" (about 3:46, not spoken).
3. **Model:** `/model`. He uses Opus and falls back to Sonnet when Opus has issues. The default at the time was Opus until 50% of the usage limit, then Sonnet. Flag as outdated: the default behaviour and the model lineup have changed since July 2025 (the 2026 video shows Opus 4.6, Sonnet 4.6, Haiku 4.5 and an effort setting).
4. **`/clear` every time you start something new.** Don't let the chat build up and auto-compact, because compaction is another LLM call that costs time and tokens.
5. **Up arrow** recalls past prompts, including ones from earlier sessions.
6. **Skip permission prompts:** quit, then start with `claude --dangerously-skip-permissions` (he calls it "YOLO mode"). FLAG: this is risky. "I've never seen [a destructive command] happen" is one person's experience. Safer options exist: an allowlist in `/permissions` or `settings.json`, accept-edits mode (Shift+Tab), or a sandbox or container. His claim that "there's no way to globally say just edit files" is wrong even for that era; accept-edits mode and permission allow rules existed.
7. **Automated PR review:** run `/install-github-app`. It adds `.github/workflows/claude-code-review.yml`, which uses `anthropics/claude-code-action@beta` with `${{ secrets.ANTHROPIC_API_KEY }}`. **Replace the default prompt to cut verbosity.** On screen, his `direct_prompt` is: "Please review this pull request and look for bugs and security issues. Only report on bugs and potential vulnerabilities you find. Be concise." Flag: the action name, `@beta` tag and `direct_prompt` key may have changed in later action versions; check the current docs.
8. Other built-in GitHub commands he mentions: `/pr-comments` (pull PR comments in and address them) and `/review` (shown in the slash menu on screen).
9. **`/terminal-setup`** makes Shift+Enter insert a newline. He says it doesn't work out of the box. That depends on the terminal; newer versions and terminals often support it natively.
10. **Drag files into the prompt:** in Cursor or VS Code, **hold Shift while dragging** so the file becomes a reference instead of opening in a new tab.
11. **Paste images with Ctrl+V, not Cmd+V** (macOS).
12. **Stop Claude with Esc.** Ctrl+C twice exits the whole session. **Esc Esc** opens a list of earlier messages so you can jump back to one.
13. Vim mode exists (`/vim`). He doesn't use it.
14. **Large files:** he says it reliably edits an 18,000-line React component where Cursor's agent struggled to apply patches. This is an anecdote from his codebase, not a benchmark.
15. **Queue prompts while Claude is working:** type the next message and press Enter. It holds queued messages if it needs your input and runs them once the current task is done. Check in now and then. Demo prompts: "add more comments", then queued "also add comments to the main chunks of the JSX" and "and to the computed values".
16. **Ask Claude to scaffold its own config:** "add a couple default hooks, commands, and settings". It produced a settings file, a `CLAUDE.md` with a project overview and key commands (build, lint, so it doesn't rediscover them each session), and hooks such as running Prettier on the edited file and running a type check after edits. He says "before edits are accepted"; in practice formatters usually go on PostToolUse. Flag as loosely described: he shows no hook JSON, so check the hook event names yourself.
17. **Custom slash commands:** add `.claude/commands/<name>.md`, written in natural language. Use `$ARGUMENTS` for the argument. Subfolders become namespaces, so `.claude/commands/builder/plugin.md` is invoked as `/builder:plugin`. Note: commands have since been folded into skills (`.claude/skills/`), but `.claude/commands/` still works.
18. **Quick memory with `#`:** for example `# always use MUI components for new stuff`. It asks which memory file to save to: project `CLAUDE.md`, a nested `CLAUDE.md` (more specific files take priority), user-global memory, or local project memory (git-ignored). Flag: the `#` shortcut has since changed or been removed in newer versions; the current route is `/memory` or asking Claude to edit CLAUDE.md.
19. Pricing: he recommends the Max plan (from $100/mo) and compares it with what an engineer costs per hour. This is opinion.
20. Plug (10:28 onward): the Builder.io Fusion visual UI, which "reverse engineered" Claude Code. It's a product pitch, not Claude Code technique.

## Demonstrated vs. said
- **Shown, not spoken:** the CLI's tip "Use git worktrees to run multiple Claude sessions in parallel" and its link to the common-workflows docs. Also the "Bypassing Permissions" status label in every pane, which shows he works permanently in YOLO mode.
- He runs two Claude panes side by side next to the editor the whole time: parallel sessions as a default layout, not just a tip.
- The generated CLAUDE.md (about 9:13) has sections such as "Development Tips", "Common Gotchas" (MobX observables, Firebase in try-catch) and "Performance Considerations". That's a template for codebase-specific pitfalls, though he never explains it.
- He "fixes" the review bot by changing one prompt line, an example of tuning the default prompt instead of accepting it.
- The comment-adding task he queues is deliberately low-risk while he multitasks.

## Packaging
- Title: "How I use Claude Code (+ my best tips)". First person and practitioner-framed, which works with his credibility as Builder.io CEO. The vague title is carried by the creator's name.
- Caption: one line linking his blog post. No hashtags or tags, category "Entertainment" (a mismatch). Chapters do the discovery work.
- What works: dense, concrete keyboard tips (Ctrl+V, shift-drag, Esc Esc, queuing) that people don't find on their own. A low-friction single-take format.
- What doesn't: about 1:20 of Cursor-vs-Anthropic economics and about 2 minutes of product plug. Unsafe advice (`--dangerously-skip-permissions`) is delivered as the main permissions tip with no safer alternative.

## Verdict
USEFUL, despite its age. The keyboard and terminal tips, `/clear` discipline, queuing, the trimmed PR-review prompt and the custom-command format still apply. Check version-sensitive items (`#` memory, model defaults, action config) and swap the permissions tip for allowlists.
