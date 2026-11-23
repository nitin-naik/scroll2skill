# 19 Claude Code Mistakes "Pro" Users Are Still Making — Simon Scrapes

## Source
- **Platform:** YouTube, Simon Scrapes (@simonscrapes, ~108K subscribers)
- **URL:** https://www.youtube.com/watch?v=icM0ewXGvAw
- **Format:** talking head with screen inserts and a numbered list (16:9, about 20.2 min / 1212 s). About 0.45 cuts per 10 s.
- **Uploaded:** 2026-08-22
- **Engagement:** 129,738 views · 2,337 likes · 93 comments. Likes are 1.80 per 100 views and comments are 3.98 per 100 likes. Views are above the subscriber count and engagement is healthy.
- **Caveat:** the transcript is a machine Spanish dub or translation track. Commands and settings were cross-checked against on-screen terminal and doc frames.

## Opening (0:00–0:30)
The cold open is a prompt typed in the Claude desktop app: "you are a senior copywriter with 20 yrs experience who writes all my marketing copy. take a deep breath. This task is very important". He claims someone tested 162 personas across 2,500 prompts and found persona prompts did no better than asking directly. He adds that the Claude Code team cut its own system prompt by about 80% and no longer recommends packing it with examples. The framing promise: "every rule you learned for Claude has been rewritten in the last 6 months, and most people still use the old ones."

## Structure (chapters from the description)
0:00 #1 persona lines are wasted words · 2:05 #2 "don't do X" · 2:21 #3 routines get full tool access · 2:58 #4 connectors preloaded · 3:32 #5 MCP no longer eats context · 4:18 #6 skills not shared between Code and Cowork · 5:26 #7 subagents/agent teams cost about 7x · 6:39 #8 fast mode billing · 7:53 #9 CLAUDE.md edits mid-session are ignored · 8:51 #10 long CLAUDE.md · 10:37 #11 what subagents receive · 11:57 #12 auto-compact window · 13:08 #13 1M context retrieval drop · 14:05 #14 partial compact via rewind · 14:48 #15 Ctrl+G to edit the plan · 15:42 #16 switching to a cheaper model costs more · 16:30 #17 verification ladder · 17:56 #18 history auto-deletes after 30 days · 18:52 #19 /doctor, /insights, /btw, /branch

## Format
A face-cam presenter alternates with full-screen inserts: the Claude desktop app (Chat/Cowork, Routines, Connectors, Skills customization), the VS Code terminal running Claude Code (`/context`, `/fast on`, `/doctor` output, rewind menu, `/resume` list, `/insights`, `/btw`), and screenshots of Anthropic docs (CLAUDE.md best practices, subagent context list, Opus long-context table, the "Don't change models mid-session" caching note, "Claude Code power user tips", "Add an adversarial review step"). Numbered lower-third badges mark each mistake.

## Teaching
1. **Drop persona and "deep breath / very important" lines.** Spend those words on three things, as his example prompt shows (on screen):
   - *where to look*: "the client's notes are in the onboarding folder"
   - *definition of done*: "a one-page proposal covering their three pain points, with price listed at the bottom"
   - *self-check*: "before you finish, check every number against the notes and flag anything you couldn't back up"

   *The 162-persona / 2,500-prompt study is unsourced in the video. The "system prompt cut about 80%" claim is also UNVERIFIED.*
2. **Say what to do, not what not to do.** Replace "do not return it as markdown text" with "write it as flowing prose paragraphs".
3. **Routines (desktop app → Code → Routines) attach all connectors by default.** Remove the ones a routine doesn't need, both when creating it and afterwards. This is safer and uses less context.
4. **Desktop/Chat connectors:** under + → Connectors → Tool access, set tools to **load when needed** instead of preloaded. *Applies to the claude.ai and desktop chat surface, not the CLI.*
5. **In Claude Code, MCP servers no longer cost much up front.** Tool search is on by default, so only tool names load (he says about 120 tokens) and schemas are fetched on demand. Check with `/context`. On screen, the "MCP tools" section reads "/mcp loaded on-demand". The old advice to remove rarely used MCP servers is outdated (he corrects his own earlier video).
6. **Skills don't carry over from Claude Code to Cowork.** CLI skills live in `.claude/skills/<name>`. Cowork can't use them even with folder access. Re-add them via Customize → Skills (upload a zip or create one there). Cowork loads skills at session start, so restart after adding one. *Specific to one surface, and may change.*
7. **Subagents and agent teams are not free.** He cites Anthropic docs saying agent teams use about 7x the tokens of a standard session. He mixes "subagents" with "agent teams", and the 7x figure is for teams. Use subagents for reading, wide searches and parallel research that need little context. Keep context-heavy, specific tasks in the main session, because passed context is not cached in the new window.
8. **Fast mode** (`/fast on`; the screen shows "Fast mode ON - model set to Opus 4.8 - $18/$50 per Mtok") is billed to **API usage credits, not your subscription**. It turned itself off in his demo because he had no credits enabled. It stays on across sessions until `/fast off`. Turning it on mid-conversation re-bills all existing context at the full uncached fast-mode input rate. *Pricing and model are as of the Aug 2026 recording.*
9. **CLAUDE.md edits mid-session are not picked up.** Project-root and user CLAUDE.md files are read once at session start. After an edit, use `/clear`, `/compact` or start a new session (he demos an "always return bullet points" rule being ignored).
10. **Keep CLAUDE.md short.** Anthropic docs (on screen): "If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long and the rule is getting lost." Numbers he gives: Claude Code's system prompt has about 50 instructions, models reliably follow about 150–200, and the best instruction files are about 300–350 *words*. Aim for under 100 lines (200 at most). Move detail into separate files Claude reads when needed (`@path/to/import` syntax is on screen). *These numbers are unsourced.* Note that the doc shown still says emphasis like "IMPORTANT" helps. He says shortening is the real fix.
11. **Ask `/doctor` to suggest cuts in plain language:** "/doctor propose trims to my CLAUDE.md that won't affect performance". His run found 7 sections across AGENTS.md and CLAUDE.md, saving about 4–5K tokens per session (terminal on screen).
12. **What a subagent receives** (on-screen docs): its own system prompt, the task message, the CLAUDE.md hierarchy, a git status snapshot, preloaded skills from its `skills` field, and a sibling roster. It does **not** get conversation history, output style, auto-memory, or files already read. **Built-in Explore and Plan agents skip CLAUDE.md and git status.** So restate critical CLAUDE.md rules in the delegation prompt. For side tasks that need full context, **fork** the conversation instead.
13. **Auto-compact is no longer a percentage.** He corrects his old "95%" advice. With no window set, Claude Code compacts near the model's context limit. Set a fixed auto-compact window (e.g. 50k or 100k tokens) in settings, because quality drops well before the window is full. *The exact setting key isn't shown clearly. Check `/config`.*
14. **A bigger context window is not more memory.** Opus 4.6 MRCR v2 8-needle results, as he states them: about 93% at 256K and about 76% at 1M (an on-screen table from Anthropic's model card, not fully legible in OCR).
15. **Partial compaction:** press **Esc Esc** to open rewind, pick a message, and choose among "Restore code and conversation / Restore conversation / Restore code / Summarize from here / Summarize up to here" (on screen). "Summarize up to here" compacts only the earlier part and keeps recent turns exactly.
16. **Edit plans directly:** in plan mode, press **Ctrl+G** to open the plan in your editor. He says browser or VS Code, but Ctrl+G opens it in your configured editor. Edit it, then tell Claude it was updated. This saves the back-and-forth of asking for a re-plan.
17. **Don't switch to a cheaper model mid-session.** Prompt caches are per model, so with 100K tokens in context, switching Opus → Haiku (and back) rebuilds the cache each time. That is more expensive than letting Opus answer. To use a cheaper model, hand off through a subagent (Anthropic doc on screen: Explore agents use Haiku).
18. **Stop being the verification loop.** Four levels: (1) ask for verification in the prompt; (2) `/goal`, a separate evaluator that re-checks a condition after every turn; (3) **Stop hooks**, which block the end of the turn until your script passes; (4) an **adversarial review subagent** in fresh context (on screen: the bundled `/code-review` skill, or your own prompt such as "Use a subagent to review the rate limiter diff against PLAN.md..."). Tell the reviewer to flag only issues that affect correctness, stated requirements or the done condition, and to treat the rest as optional. Otherwise it keeps finding problems.
19. **History deletes itself after 30 days by default** (`/resume` showed only 13 sessions). Set `"cleanupPeriodDays": 365` in settings.json. Setting it to `0` does **not** mean unlimited (he says it deletes everything). Auto-memory files are exempt from the cleanup.
20. **Lesser-known commands:** `/doctor` (setup health check: unused skills, MCP and plugins, context cost, CLAUDE.md duplicates, proposed trims); `/insights` (an HTML report analyzing up to 200 recent sessions, which needs the history kept per item 19); `/btw` (side question without interrupting the main thread; close with Esc); `/branch` (fork the current conversation at this point, leaving the original unchanged).

**Flags:** He mentions an "Ultra Code" built-in delegation mode (UNVERIFIED name). Tips 3, 4 and 6 apply to the desktop app or Cowork, not the CLI. Model names and prices date from Aug 2026. The Spanish translation garbles some command names. The ones above are confirmed on screen except `/branch` and the auto-compact window key.

## Demonstrated vs. said
- He makes every claim credible by showing the Anthropic doc page on screen. A useful habit is citing the docs over folklore, and he corrects his own earlier videos (#5, #12).
- `/context` is used as a measuring tool before deciding what to cut. That is measure-before-optimizing, though he never names it.
- His `/doctor` call takes a free-text request, treating a slash command as a prompt.
- The terminal footer shows him running in bypass-permissions mode ("Bypass permissions on (shift+tab to cycle)"), which he never mentions or warns about.

## Packaging
- **Title:** "19 Claude Code Mistakes 'Pro' Users Are Still Making". It combines a number, a slight to the viewer's ego, and fear of missing out. It works for clicks.
- **Caption:** promotes a Skool community and an affiliate link, then gives full chapter timestamps (good). Hashtags: #claudecode #claudecodetutorial #claudeai. There are no tags.
- **What works:** quick pace, each tip backed by a doc screenshot or terminal, several real cost and context gotchas.
- **What doesn't:** it mixes CLI, desktop and Cowork surfaces. Several numbers are unsourced. The subscribe plea mid-video breaks the flow. "19" is padded: #3, #4 and #6 are app-UI specific.

## Verdict
**USEFUL.** It is dense with concrete, verifiable Claude Code gotchas (CLAUDE.md read once per session, subagent context gaps, cache cost of switching models, `cleanupPeriodDays`, Esc Esc partial summarize, Ctrl+G plan edit). A few claims are unsourced or not about the CLI.
