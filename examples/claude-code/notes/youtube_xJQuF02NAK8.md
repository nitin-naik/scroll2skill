# The Explore -> Plan -> Code -> Commit workflow in Claude Code

**Source:** YouTube, official Claude channel (@claude, 766K subscribers). https://www.youtube.com/watch?v=xJQuF02NAK8. Horizontal, 3:11, uploaded 2026-05-17. It is one lesson from the claude.com/courses course. 539,833 views, 3,381 likes, 95 comments. Likes per 100 views: 0.63 (low; typical of a channel push). Comments per 100 likes: 2.81. Views are 0.70x the subscriber count.

**Opening (0-30s):** A title card, then: "If you take one thing away from Claude Code, let it be this workflow: explore, plan, code, and commit." Then the problem: "most people jump straight to ... write code, which means more course correcting later." It frames the video as the single highest-leverage habit. Plan mode is introduced by 0:21.

**Structure (no chapters; inferred):**
- 0:00 Hook and the four steps
- 0:21 Explore and Plan with plan mode (WebP upload example)
- 0:59 Course-correct at the plan; approve options
- 1:10 "Code" card: success criteria and verification tools
- 2:17 Tip: save recurring fixes to CLAUDE.md
- 2:25 Commit: subagent review, then commit message
- 2:43 Recap

**Format:**
- Presenter on camera (Lewis), intercut with Claude Code terminal recordings on a beige background.
- Title cards in serif type with the pixel crab mascot.
- Demo app: "TaskFlow", an Express/TS API with a frontend.
- Recent Claude Code UI (v2.1.x, Opus 4.6, Claude Max, `/remote-control` active).

**Teaching:**
1. Default to four phases: Explore, then Plan, then Code, then Commit. Don't open with "write the code".
2. Do Explore and Plan in **plan mode**, where Claude only reads files and researches and cannot edit. Press **Shift+Tab** until "plan mode on" appears under the input.
3. Write the plan prompt as a research question. Prompt verbatim: `I need to add WebP conversion to our image upload pipeline. Figure out where in the pipeline it should happen, whether we need new dependencies, and how to approach it.` Claude reads files, may web search, and returns a plan.
4. Review the plan against your criteria and ask for revisions. Before any code exists is the cheapest point to course-correct.
5. You can also explore without plan mode by asking Claude to "explore the codebase". On screen, plan mode spawned "Running 2 Explore agents" (project structure; existing color palette), plus a "ctrl+b to run in background" hint.
6. Approval options, shown on screen only:
   - "1. Yes, clear context (12% used) and auto-accept edits"
   - "2. Yes, auto-accept edits"
   - "3. Yes, manually approve edits"
   - "4. Type here to tell Claude what to change"

   Plans are saved to `~/.claude/plans/<random-name>.md`, and **Ctrl+G** opens one in your editor (VS Code). Option 1 is worth knowing: it starts implementation with a clean context that holds just the plan.
7. A plan can open a feedback interview (on screen: "What would you like to change about the plan before proceeding?" with options such as "Different toggle style", "Different dark colors", "Shared header component", "Skip interview and plan immediately").
8. Make success criteria explicit in the plan. On screen, the plan's "Verification" list:
   - `npm install` succeeds with sharp
   - upload JPEG/PNG/GIF and confirm the saved file is `.webp`
   - `avatar_url` ends with `.webp`
   - served with `Content-Type: image/webp`
   - the old `.webp` is deleted on re-upload
   - a corrupt file returns 422 with no orphaned files
9. Give Claude tools to check itself:
   - for web UI, install the **Claude in Chrome** extension so Claude can drive a tab and test the UI (on screen: a TaskFlow sign-in page with a "Stop Claude" button)
   - keep a test suite Claude can run continuously (on screen: `Can you run my tests to see if everything works fine?` leads to `npm test` and vitest)
   - Claude can write tests, but first make sure they are a trusted source of truth, or you get false positives
10. If Claude keeps hitting the same issue, ask it to save the fix to CLAUDE.md.
11. Before committing, run a code-review **subagent**. Prompt on screen: `Spawn the code reviewer subagent to review the code we last created`, which runs a `code-reviewer` agent. This assumes you have defined a custom agent of that name in `/agents`. It is not built in under that name.
12. Have Claude write the commit message "in your style". On screen: `Can you create a commit for this?` makes Claude run `git diff` and `git log --oneline -5` first, so it matches existing message style. Then repeat the loop for the next feature.

**Demonstrated vs. said:**
- Claude reads `git log` to copy your commit style before committing. Not named.
- Plan mode spawns parallel Explore subagents, which keep the main context small. Not explained.
- "Clear context and auto-accept" separates research from implementation. Not explained.
- The `/effort` (medium) indicator and the "PR #1" status line appear without mention.
- The tip "Use `--agent <agent_name>` to directly start a conversation with a subagent" flashes on screen.
- A second, unrelated prompt (dark-mode toggle across the app) shows plan mode on a UI-wide change.

**Packaging:**
- The title names the exact workflow and the arrows make it scannable.
- The caption calls it "the single most important workflow", which is a strong but credible claim from the vendor.
- It ends with a course CTA.
- The low like rate suggests mostly passive or recommended views.

**Verdict:** USEFUL. It is the canonical vendor workflow, and on-screen-only details carry it: approval options, the plans folder, Ctrl+G, the verification list, the review subagent.
