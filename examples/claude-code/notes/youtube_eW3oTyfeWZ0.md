# Context Management in Claude Code

**Source:** YouTube, official Claude channel (@claude, 766K subscribers). https://www.youtube.com/watch?v=eW3oTyfeWZ0. Horizontal, 3:30, uploaded 2026-05-18. Part of the claude.com/courses series. 469,769 views, 2,651 likes, 76 comments. Likes per 100 views: 0.56. Comments per 100 likes: 2.87. Views are 0.61x the subscriber count.

**Opening (0-30s):** A title card, then: "Context is Claude's working memory. Every file it reads, every command it runs, every message you send, it all takes up space in the context window." An animation shows the window filling up. Because the window is finite, "it becomes extremely important to optimize this." It frames context as a budget you manage.

**Structure (no chapters; inferred):**
- 0:00 What context is
- 0:39 Auto-compaction, `/compact`, `/clear`
- 1:21 `/context` to inspect
- 1:34 "Compaction vs Clearing": when to use which
- 2:07 "Tips on saving context space": be specific, MCP, skills, subagents
- 3:06 Recap

**Format:** Presenter on camera, Claude Code terminal clips (TaskFlow security fixes), beige title cards, and a pixel-art crab animation comparing a big and a small context.

**Teaching:**
1. Context holds everything: prompts, file reads, tool calls and tool results. It is finite.
2. Near the limit Claude **auto-compacts**: it summarizes key details and drops stale tool results. That can lose detail.
3. Run `/compact` yourself to summarize the session so far while keeping some memory of it. The on-screen menu adds "Clear conversation history but keep a summary in context. Optional: ...", meaning you can pass focus instructions after `/compact`.
4. `/clear` wipes the conversation completely ("Clear conversation history and free up context").
5. `/context` shows total usage, the categories using the most, and a graphic. On screen, its lower section lists token costs per item: custom agents (`code-reviewer: 335 tokens`), skills (`doc-helper: 48`, `pr-description: 37`, `documentation: 36`, `commit-message: 32`, `debugging: 29`), and MCP tools (`mcp__claude_ai_Notion__notion-create-comment`, and others).
6. Rule of thumb:
   - Still on the same feature and running out of room: **compact**.
   - Plan finished and starting a new feature: **clear**, so the old conversation doesn't bias new work.
7. Anything that should outlive sessions goes in CLAUDE.md, so Claude doesn't rediscover it.
8. Be specific. A shorter, vaguer prompt costs more context overall, because Claude has to search the codebase and reason on its own. One or two extra sentences save space.
9. MCP servers load all their tools into context by default. Turn off servers unrelated to the current project.
10. Prefer skills where possible. They work like MCP tools but load only a short description until used (on screen: about 30-50 tokens each).
11. Delegate "answer without the journey" questions to subagents. Each has its own context window and returns only a summary. Example: "where are the authentication endpoints located".
12. **Wording to check:** "subagents run in parallel with your main agent". They can run in the background or in parallel, but by default the main agent waits for them. The key benefit is the separate context.

**Demonstrated vs. said:**
- The demo session is a workflow chain: after a commit, the prompt "Any other items needing fixed?" brings up the code-review backlog (High: over-permissive CORS `origin: '*'`, empty catch blocks, missing input validation; Medium: hardcoded JWT secret fallback, no request correlation IDs, orphaned avatar files). Then `/compact` or `/clear` runs at that natural boundary.
- He compacts or clears right after a commit, which is the "checkpoint at commits" habit, never stated.
- The `/` menu shows `/copy`, `/color` and `/chrome` in passing.

**Packaging:**
- The title is literal and searchable.
- The caption promises "when to use /compact vs /clear" and delivers.
- It has the lowest like rate of the set, and the content overlaps with the Greg Baugues video.
- The `/context` per-item token breakdown is the most concrete thing in it, and it appears only on screen.

**Verdict:** USEFUL. It gives a clear compact-vs-clear rule and the `/context` audit habit (MCP and skills token cost). It is introductory, and the MCP/skills/subagent tips are one line each.
