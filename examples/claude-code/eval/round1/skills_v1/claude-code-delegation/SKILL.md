---
name: claude-code-delegation
description: Decide how to split work in Claude Code — main session, subagent, forked conversation, parallel sessions in git worktrees, or an orchestrator with workers — and write the delegation prompts so nothing important gets lost. Use when someone asks "should I use a subagent for this", "how do I run Claude in parallel", "my subagent ignored my rules", "write an agent definition", or plans a task too big for one session.
---

# Claude Code delegation

Delegation buys a clean context window at the price of lost context. Choose the mode by how much context the side task needs, then brief it so it doesn't need what it can't see.

## 1. Pick the mode

| Work | Mode | Why |
|---|---|---|
| Needs the conversation so far, context-heavy, specific | **Main session** | Context passed to a new window isn't cached and costs again (Simon Scrapes) |
| "Answer without the journey": where is X, how does Y work, wide search, read many files | **Subagent** | Own window, returns only a summary; keeps the main thread clean (Anthropic context video) |
| Side task that needs the full conversation | **Fork** the conversation (verify the command on your version, e.g. `/branch`) | Keeps history; subagents don't get it (Simon Scrapes) |
| Independent features or fixes touching different files | **Parallel sessions, one git worktree each** | No file collisions; review and merge each (Zhang; Steve) |
| One big job splittable into tested tasks | **Orchestrator + workers** | Orchestrator splits, launches, checks and sends back incomplete work; writes no code itself (Hallie) |
| Review before commit | **Reviewer subagent in fresh context** | It judges the diff without your session's assumptions (Anthropic; Simon Scrapes) |

Cost check: agent teams use far more tokens than one session (Simon Scrapes cites Anthropic docs at about 7x for teams). Don't parallelize what one session can do in a few turns.

Parallel worktree sessions: `claude --worktree <name>` (seen on screen in Zhang's video, puts the session in `.claude/worktrees/<name>`; verify with `claude --help`), or `git worktree add ../<name> -b <branch>` and start `claude` there.

## 2. Brief what the subagent can't see

A subagent receives (Anthropic docs, shown by Simon Scrapes): its own system prompt, your task message, the CLAUDE.md hierarchy, a git status snapshot, and skills listed in its definition. It does **not** receive the conversation, files you've already read, output style, or auto-memory. **Built-in Explore and Plan agents skip CLAUDE.md and git status.**

So every delegation prompt states:
1. **Goal** in one sentence, and why it matters.
2. **What's already known**: files, decisions, dead ends, so it doesn't redo them.
3. **Critical rules** from CLAUDE.md that apply, restated (they may not be loaded).
4. **Scope limits**: read-only or allowed to edit; which paths.
5. **Done when** + the exact **return format** (short; file:line references; no file dumps).

## 3. Agent definition template

For a reusable specialist in `.claude/agents/<name>.md`, follow the structure of Zhang's `security-reviewer.md`:

```markdown
---
name: <name>
description: <when Claude should use this agent>
tools: <only what it needs, e.g. Read, Grep, Glob, Bash>
---
## What to check
- <specific item 1> … (a concrete list, not "review for issues")

## How to work
- Read the relevant source files before making any claims.
- <commands to run, patterns to grep for>

## Output format
<fixed schema, e.g. Severity · file:line · Issue · Risk · Fix>
Summarize in a table sorted by severity. If a category has no issues, say so briefly. Don't pad the report.
```

For reviewers, add: "Flag only issues that affect correctness, the stated requirements or the done condition; list anything else as optional" (Simon Scrapes).

## 4. Orchestration (large jobs)

From Hallie's talk (Nov 2026; some features in beta, verify availability):
- The orchestrator writes no code. It splits the job into tasks that each have a test, starts one worker per task, reads results, and sends back anything incomplete.
- Use a strong judging model for the orchestrator and a strong coding model for workers; they are configured separately.
- Run long or unattended work in cloud sessions: fresh machine, clean clone, no local `.env` or SSH keys. Add API keys as secrets the model can't read, allowlist only needed domains, and keep deny rules committed so pushes stay safe.
- Every worker ends in a PR so CI runs the same checks however the session went.

## Output

Given a task, return:
1. **Split**: table of pieces → mode (main / subagent / fork / worktree / worker) → one-line reason.
2. **Prompts**: a complete delegation prompt for each non-main piece, using the 5-part brief in section 2.
3. **Agent files**: any `.claude/agents/*.md` worth creating, in the section 3 template.
4. **Merge plan**: order to integrate results and what to verify after each.

## Sources
- Simon Scrapes, "19 Claude Code Mistakes 'Pro' Users Are Still Making", Aug 2026 — https://www.youtube.com/watch?v=icM0ewXGvAw
- Lydia Hallie (Anthropic), "Rethinking Claude Code Best Practices", Nov 2026 — https://www.youtube.com/watch?v=vlfCjWuv4es
- Maddy Zhang, "How I use Claude Code (Senior Software Engineer Tips)", Apr 2026 — https://www.youtube.com/watch?v=MzhIr7BfpI0
- Anthropic, "Context Management in Claude Code", May 2026 — https://www.youtube.com/watch?v=eW3oTyfeWZ0
- Anthropic, "The Explore → Plan → Code → Commit workflow in Claude Code", May 2026 — https://www.youtube.com/watch?v=xJQuF02NAK8
- Steve (Builder.io), "How I use Claude Code", Jul 2025 — https://www.youtube.com/watch?v=n7iT5r0Sl_Y
