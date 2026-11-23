---
name: claude-code-task-loop
description: Turn a coding request into a well-run Claude Code session — explore and plan first, write a "done when" with evidence, build in small committed steps, verify, review in fresh context, and manage context with clear/compact/rewind. Outputs a ready-to-paste kickoff prompt plus a session checklist. Use when someone says "help me prompt Claude Code for this feature", "how should I run this task in Claude Code", "Claude keeps going off the rails", or pastes a task to hand to Claude Code.
---

# Claude Code task loop

Every task runs the same loop: **Explore → Plan → Build → Verify → Commit** (Anthropic calls Build "Code"), then clear and repeat (Anthropic workflow video). The expensive mistakes happen when a step is skipped, most often Plan and Verify.

**This skill adds to your own knowledge; it doesn't limit it.** Answer the user's actual question first and fully. The steps and output format below are the minimum to cover, not a template to squeeze the answer into. Where you know something the sources don't, use it.

## Steps

### 1. Explore + plan (no edits yet)
- Switch to plan mode: **Shift+Tab** until "plan mode on" shows under the input. Claude can read and research but not edit.
- Phrase the request as a research question, not an order. Template (Anthropic):
  > I need to `<goal>`. Figure out where in the `<system>` this should happen, whether we need new dependencies, and how to approach it.
- Name exact files and constraints when you know them (Tab completes paths). When you don't, use clear placeholders (`<path to login route>`) and add "find it if I left this blank".
- List the user's open decisions in the prompt so the plan settles them, not the code (e.g. for rate limiting: fixed vs sliding window, reset on success, behaviour when Redis is down, client IP behind a proxy). A vague prompt makes Claude search on its own and costs more context than two extra sentences (Anthropic context video).

### 2. Make the plan checkable
- The kickoff prompt tells Claude to end its plan with a **Verification** section; you also keep your own list (output item 2) to check the plan against. The plan must end with a **Verification** section of concrete checks (Anthropic; Zhang). Example from the WebP task: upload JPEG/PNG/GIF → saved file is `.webp`; served with `Content-Type: image/webp`; corrupt file → 422 with no orphaned files.
- Put the definition of done in the request itself (Hallie):
  > It's done when `<observable outcome>` and `<thing that must not break>`. Split it into tasks, each with its own test. Show me the test output.
- Edit the plan directly instead of arguing with it: **Ctrl+G** opens the saved plan (`~/.claude/plans/`) in your editor; save, then tell Claude it changed (Zhang; Simon Scrapes).
- Approve with "Yes, clear context and auto-accept edits" when the plan is self-contained; that starts building with a clean window.

### 3. Build in small steps
- Small diffs: a 2-file change that breaks one thing is a 5-minute fix; a 15-file change that breaks three is not (Zhang).
- Ask Claude to commit after each working step; commit messages in the repo's style ("Can you create a commit for this?" makes it read `git log` first) (Anthropic; Baugues).
- If Claude heads the wrong way, press **Esc** immediately (Baugues). Esc twice opens rewind: restore code and/or conversation to an earlier message (Simon Scrapes).
- When it's gone sideways: revert to the last good commit, `/clear`, and retry with sharper instructions. Revert more often than feels natural (Baugues).
- You can queue the next instruction while Claude works; type it and press Enter (Steve, Builder.io).

### 4. Verify (don't be the verification loop yourself)
These levels stack, weakest first; use every one that applies (Simon Scrapes; Hallie):
1. The done-criteria and "show me the test output" from step 2.
2. A test suite Claude can run. If Claude writes the tests, check they test the real requirement first, or you get false passes (Anthropic workflow video).
3. A `Stop` hook that blocks finishing until tests pass. It must exit 2 on failure (exit 1 lets Claude finish anyway). In `.claude/settings.json`:
   `"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "[ \"$(jq -r .stop_hook_active)\" = true ] && exit 0; pnpm test >&2 || exit 2"}]}]}` (use the repo's real test command). The `stop_hook_active` guard stops it looping forever on a test that can't pass. **Add this hook only after the failing tests are committed** — during the tests-first step the suite is supposed to fail, and the hook would block it.
4. For UI: let Claude drive a browser (Claude in Chrome or a Playwright MCP) and look at screenshots of its own work (Anthropic; Baugues).

### 5. Review in fresh context, then commit
- Before the final commit, spawn a reviewer subagent that sees only the whole feature's diff (`git diff <base>...HEAD`, across all step commits) and the plan, e.g. "Use a subagent to review the diff against the plan" (Anthropic; Simon Scrapes). A named agent like `code-reviewer` must be defined in `/agents` first.
- Tell the reviewer to flag only issues affecting correctness, stated requirements or the done condition; everything else is optional. Otherwise it never runs out of findings (Simon Scrapes).
- If Claude hit the same problem twice, have it add the fix to CLAUDE.md (Anthropic).

### 6. Context between tasks
| Situation | Do |
|---|---|
| Same feature, running out of room | `/compact`, ideally at a natural break like right after a commit (Baugues) |
| Starting a new feature | `/clear` so old conversation doesn't bias new work (Anthropic context video) |
| Only the early part is stale | Esc Esc → pick a message → "Summarize up to here" (Simon Scrapes) |
| Side question mid-task | Hand it to a subagent ("use a subagent to find…") so the answer comes back without the search cluttering the main thread |
| Want a cheaper model | Delegate to a subagent; don't switch the session's model mid-task, since the prompt cache is per model and gets rebuilt (Simon Scrapes) |

For work that spans sessions, keep the plan in a file or issue so a fresh session can pick it up (Baugues).

## Output

When given a task, produce at least:
1. **Paste-ready prompts for every phase**, not just the first: (a) plan-mode kickoff — goal as a research question, known files/constraints, open decisions, "done when…" with evidence, "end the plan with a Verification section"; (b) tests first — "write failing tests for these cases, don't change them to make code pass"; (c) build; (d) fresh-context review with the specific risks to check.
2. **Test spec**: the concrete cases the tests must cover, including edge cases and abuse cases for this domain (e.g. for rate limiting: correct password while locked still gets 429, Retry-After counts down, TTL set only on first failure, malformed requests don't count, response doesn't reveal whether the account exists, header spoofing).
3. **Session checklist** (short): numbered steps trimmed to what applies (e.g. skip browser checks for a CLI change); mark commit points with **COMMIT**.
4. **Risks**: anything irreversible the task touches (migrations, deletes, deploys) and how to gate it; if nothing is irreversible, say so and list the top 1-3 high-impact risks instead.

## Sources
- Anthropic, "The Explore → Plan → Code → Commit workflow in Claude Code", May 2026 — https://www.youtube.com/watch?v=xJQuF02NAK8
- Anthropic, "Context Management in Claude Code", May 2026 — https://www.youtube.com/watch?v=eW3oTyfeWZ0
- Lydia Hallie (Anthropic), "Rethinking Claude Code Best Practices", Nov 2026 — https://www.youtube.com/watch?v=vlfCjWuv4es
- Simon Scrapes, "19 Claude Code Mistakes 'Pro' Users Are Still Making", Aug 2026 — https://www.youtube.com/watch?v=icM0ewXGvAw
- Maddy Zhang, "How I use Claude Code (Senior Software Engineer Tips)", Apr 2026 — https://www.youtube.com/watch?v=MzhIr7BfpI0
- Greg Baugues, "Claude Code - 47 PRO TIPS in 9 minutes", May 2025 — https://www.youtube.com/watch?v=TiNpzxoBPz0 (outdated tips such as the `#` memory shortcut and Puppeteer MCP left out)
- Steve (Builder.io), "How I use Claude Code", Jul 2025 — https://www.youtube.com/watch?v=n7iT5r0Sl_Y
