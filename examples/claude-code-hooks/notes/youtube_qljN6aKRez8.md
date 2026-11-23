# youtube_qljN6aKRez8: "Skills vs Subagents vs MCP vs Hooks vs Plugins in Claude Code: Which One, When" (Skills For AI)

## Source
- Platform: YouTube. Creator: Skills For AI (@skillsforaidotpro), 49 followers.
- URL: https://www.youtube.com/watch?v=qljN6aKRez8
- Format: horizontal, 6:14 (374 s). Animated explainer, no presenter. The voice is an AI-generated clone of Alessio Marcone, disclosed in the description and by an "AI voice" corner tag.
- Chapters: Intro 0:00, base layer 0:30, skills 1:04, subagents 1:44, MCP 2:39, hooks 3:23, plugins 4:20, which one 5:03, recap 5:55.
- Cuts: 0.0 per 10 s. There are no hard cuts; it uses animated transitions throughout.
- Engagement: 257 views, 3 likes (1.17% of views), 2 comments (0.78%). Views are 5.2x followers.
- Uploaded 2026-10-17. The description says facts were "checked 15 October 2026" against code.claude.com docs.

## Opening (first 30 s)
- 0.0 s: blank off-white slide with "skillsforai.pro" and the "AI voice" tag.
- 0.5 s: burned-in caption appears.
- 1.0 s: "CLAUDE CODE / Which one, when" headline [youtube_qljN6aKRez8 t=00:00-00:01].
- Words: "Claude Code has five ways to extend it: skills, sub-agents, MCP, hooks, and plugin. They sound alike, but each one solves a different problem."
- The promise is a 3-question frame per feature (what it does / context cost / who starts it) [t=00:10-00:17], plus a trust claim ("checked against Anthropic's documentation") and a quiz engagement hook ("leave your score in the comments") [t=00:18-00:28].

## Structure
Seven numbered parts with chapter cards (big circled number + title). Each feature runs through the same three questions. Quizzes at 2:31 (1/3) and 4:15 (2/3); the questions are not legible in the sampled frames.

The hooks segment is only 3:24-4:20 (about 56 s). Attention is held by a consistent repeated template, the quizzes and progressive-reveal diagrams.

## Format
- Off-white slides, black sans-serif headings, lime-green underline accents.
- Burned-in two-line captions at bottom center.
- Header bar with site and "PART N · TOPIC".
- Icon cards for the five features, a lifecycle timeline diagram (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop) [t=03:30], and a "Cost: zero / 0 tokens" context-window bar [t=03:45].
- Hook vs Skill card: hook shows six identical checkmarks ("event fires it"), skill shows "Claude interprets it" [t=04:00].
- Soft music bed. CTA: "Subscribe for videos like this every day" at the very end [t=06:09], plus the quiz-score comment request near the start.

## Teaching
Hooks-relevant items are marked core; items on the other features are incidental for this job.

1. **CLAUDE.md loads in full every session; keep it under 200 lines (Anthropic's advice)** [t=00:34-00:52]. Weight: incidental. VERIFIED (matches the docs' guidance).
2. **What a hook is.** "A command that Claude Code runs at a fixed moment. Before a tool runs, after a file edit, or when Claude finishes answering" [t=03:27-03:34]. The lifecycle diagram shows SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop [t=03:30]. Weight: supporting. VERIFIED, but the diagram's list is partial.
3. **Prettier after every edit is a PostToolUse hook "matched to edit and write" in your settings file** [t=03:36-03:43]. Weight: supporting. Matches the official video's `Edit|MultiEdit|Write`.
4. **Context cost is zero: "Hooks run outside the conversation. Claude only sees something if the hook returns output."** [t=03:44-03:50] Weight: core. Mostly VERIFIED. Caveat: stdout from SessionStart and UserPromptSubmit hooks, and `additionalContext`, IS injected into context, so "returns output" is the key condition.
5. **Who starts it: "Nobody. The event does. It fires every time the same way."** Unlike a skill, which Claude interprets, so the outcome can vary [t=03:51-04:00]. Weight: core.
6. **Guardrails belong in hooks.** "Writing 'Never edit the [X] file' in CLAUDE.md is a request. A PreToolUse hook that exits with code two blocks the edit." [t=04:03-04:11] Weight: core. VERIFIED (exit 2 blocks PreToolUse).
   - The spoken file name is garbled in the transcript ("the M file"), possibly ".env". The screen frame doesn't show it, so it is UNVERIFIED.
   - The description words this as "a rule in CLAUDE.md is a request, a hook is enforcement".
7. **Plugins bundle hooks too.** An enabled plugin's "hooks fire" every session, and "it runs code as you, so read it before you install it" [t=04:44-04:57]. Weight: supporting. VERIFIED (plugins can ship hooks). This is a security point relevant to hook distribution.
8. **The decision rule:** "Something must happen every time without asking? Write a hook." [t=05:29-05:33] Other rules:
   - same convention wrong twice: CLAUDE.md;
   - same procedure a third time: skill;
   - data from a tab Claude can't see: MCP;
   - side task floods chat: subagent;
   - second repo: plugin.
   - Weight: core (for deciding when a hook is the right tool).
9. **"A hook can call an MCP tool"** [t=05:44]. Weight: incidental. Hooks can match MCP tools (`mcp__server__tool` matchers). Whether a hook can *invoke* an MCP tool directly as a hook type is UNVERIFIED. Not shown.
10. **Other features covered** (skills cost, `disable-model-invocation: true`, subagents, MCP tool-name loading, `/mcp`, `/plugin`, namespacing `/my-plugin:review`) [t=01:05-04:42]. Weight: incidental, off-subject for writing hooks.

## Scores
- Specificity: **L** for hooks (no JSON, no script, no exit-code detail beyond "code two", no stdin/stdout schema). M overall.
- Evidence: **L**. Diagrams only; nothing is run on screen.
- Currency: uploaded 2026-10-17, the most current of the three. The decision heuristics are durable. Feature names and context-loading behavior are date-sensitive.

## Demonstrated vs. said
- **One frame for every feature:** "what it does / cost / who starts it" is applied to each. That frame is a usable checklist for deciding whether a behavior belongs in a hook.
- **Request vs enforcement:** the hook-vs-skill checkmark visual dramatizes determinism without saying "deterministic".
- **Comprehension check:** the quizzes act as retrieval practice.

## Packaging
- Title: long "X vs Y vs Z ... Which One, When", keyword-stuffed for search.
- Description: excellent. Chapters, a key-facts list with sources and a check date, and an AI-voice disclosure.
- Hashtags: #ClaudeCode #AgentSkills #MCP. Tags cover each feature name.
- Works: transparency and sourcing. Doesn't: tiny channel and low reach (257 views); an AI voice; hooks get under a minute.

## Verdict
**SKIP** for this job. It is an accurate but shallow overview. Its only hooks takeaway ("guarantee goes in a hook; exit 2 blocks; zero context cost unless output") is covered more concretely by the official video. `untrusted_flags`: none.
