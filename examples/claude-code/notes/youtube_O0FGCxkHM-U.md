# The CLAUDE.md file

**Source:** YouTube, official Claude channel (@claude, 766K subscribers). https://www.youtube.com/watch?v=O0FGCxkHM-U. Horizontal, 3:01, uploaded 2026-05-10. Part of the claude.com/courses series. 628,507 views, 6,033 likes, 183 comments. Likes per 100 views: 0.96. Comments per 100 likes: 3.03. Views are 0.82x the subscriber count, the best of the three channel videos here.

**Opening (0-30s):** A title card, then: "One of the most useful parts of Claude Code is the CLAUDE.md file. It gives Claude Code persistent memory about your project." Then the pain point: without it, Claude "has to start fresh every single time", re-exploring the codebase and making assumptions. The screen shows `Create a date picker component` with Claude searching and reading files first. It frames CLAUDE.md as removing the cost of rediscovery.

**Structure (no chapters; inferred):**
- 0:00 Hook, and what CLAUDE.md is
- 0:32 How it works: appended to the prompt, root of the project, `/init`
- 0:55 Example file walkthrough
- 1:35 Sharing and hierarchy (project vs user)
- 2:01 Three tips
- 2:39 Recap

**Format:** Presenter on camera, VS Code with CLAUDE.md open, short Claude Code terminal clips, and beige title cards ("Sharing your CLAUDE.md file", "Project / User").

**Teaching:**
1. Put `CLAUDE.md` in the project root. Claude Code reads it at the start of every session and its contents are appended to your prompt. Think of it as an onboarding script for the codebase.
2. Run `/init` to have Claude generate a first draft from the codebase.
3. The example structure shown on screen (keep it this short):
   ```
   # Project
   This is a Next.js 15 app using the App Router, Tailwind and Drizzle ORM.
   # Commands
   - Dev Server: `pnpm dev`
   - Run tests: `pnpm test`
   - Lint: `pnpm lint`
   # Code Style
   - Use 2 space indentation
   - Prefer named exports
   - All API routes go in app/api
   - Use server actions instead of API routes where possible
   ```
   Another example, on screen only: a `**IMPORTANT** Run the test suite EVERY TIME you finished` line, with backend and frontend command sections split by directory (`npm run seed`, `npm run dev` for Vite, `npm run build`, `npm run lint`).
4. Commit the project CLAUDE.md to version control so the team shares it.
5. The hierarchy:
   - **project** level, in the repo root
   - **user** level, in your config folder (`~/.claude/CLAUDE.md`; the path is not spoken), applied across all projects. Put personal preferences there, such as how you write code comments.

   The video skips other levels such as subdirectory CLAUDE.md files and local or untracked variants (see official docs).
6. Tip 1: when you have to correct Claude, tell it to save the correction to memory. Prompt on screen: `Ok, put in the CLAUDE.md file to only use server actions instead of API routes`. The result is the line "Always use server actions (`src/actions/`) instead of API routes".
7. Tip 2: point to existing project docs with `@path` instead of copying them in (on screen: `Database Connection Info @docs/d...` inside CLAUDE.md, with `docs/architecture.md`, `database.md` and `server-actions.md` in the tree).
8. Tip 3: start a project **without** a CLAUDE.md. Add rules only where you notice yourself repeatedly correcting the model. This keeps the file compact.
9. Build order: stack, then preferences, then commands. Grow it from there.

**Demonstrated vs. said:**
- In the save-to-memory demo, Claude does not just append. The diff on screen reads "Added 1 line, removed 2 lines": it deleted "All API routes go in app/api" and "Use server actions ... where possible", then replaced them with one stricter rule. The lesson is to have Claude reconcile contradicting rules when it updates CLAUDE.md, not stack them up. The video never says this.
- The date-picker demo shows Claude reading existing components to infer the design language. A `style-guide.md` beside CLAUDE.md in the file tree hints at keeping separate docs that are referenced, not inlined.
- Using **IMPORTANT** in caps for must-follow rules is shown but not discussed.

**Packaging:**
- The plain title "The CLAUDE.md file" pulled the most views of the three channel videos, which suggests strong search demand for the term.
- The caption lists the three topics covered.
- No tags.
- It is thin on the hierarchy and leaves out things like keeping the file short.

**Verdict:** USEFUL. It is short and accurate, and the "start empty, add only rules you keep correcting" approach plus the reconcile-on-update demo are worth taking. Basic if you already use CLAUDE.md.
