---
name: claude-code-setup-audit
description: Audit and fix a project's Claude Code setup — CLAUDE.md, permissions (auto mode, deny rules, sandbox), verification hooks, subagent definitions and context cost — and output a scored findings table plus ready-to-apply diffs. Use when someone says "review my Claude Code setup", "audit my CLAUDE.md", "Claude keeps ignoring my rules", "set up hooks/permissions for this repo", or before handing a repo to Claude for long or unattended work.
---

# Claude Code setup audit

Inspect a repo's Claude Code configuration and turn it into a short list of concrete fixes. Built from 8 videos (Anthropic talks plus practitioners, 2025-2026); newer Anthropic guidance wins where sources disagree.

## Inputs to read

Read whichever exist; note missing ones as findings:
- `CLAUDE.md` (root and subfolders), `~/.claude/CLAUDE.md`, any `@path` files they import
- `.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json`
- `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/commands/*.md`
- `.mcp.json`
- The repo's real build/test/lint commands (`package.json` scripts, `Makefile`, `pyproject.toml`, CI workflow)

If the user can run commands, ask for the output of `/context` (token cost per agent, skill and MCP tool) and `/doctor`. Do not guess token numbers.

## Checks

### A. CLAUDE.md (target: under ~100 lines; 200 is the ceiling)
1. **Only what the code can't tell Claude.** Flag stack descriptions ("We're on Node 18"), folder tours Claude can discover, and generic advice. Keep non-obvious facts like "`src/legacy` still serves our mobile apps" (Hallie).
2. **No shouting or persona.** Flag "IMPORTANT", "ALWAYS/NEVER!", "think hard", "keep going until done", "you are an expert…". Current models over-apply these and make more tool calls (Hallie, Nov 2026). *Clash:* Anthropic's May 2026 CLAUDE.md video still shows `**IMPORTANT**`; follow the newer guidance and replace emphasis with a shorter file, since a rule ignored despite being written down usually means the file is too long (Anthropic docs, shown in Simon Scrapes' video).
3. **Positive instructions.** Rewrite "don't X" as "do Y" ("write flowing prose paragraphs", not "don't use markdown") (Simon Scrapes).
4. **Exact commands present.** Dev, test, lint, build, with the real package manager ("`npm run dev`, not yarn") (Maddy Zhang; Anthropic CLAUDE.md video).
5. **Detail lives in imported files.** Long docs referenced with `@docs/architecture.md`, not pasted in (Anthropic CLAUDE.md video).
6. **Rules grow from corrections.** Rules should trace to something Claude got wrong more than once. Suggest the habit: "Put in CLAUDE.md: always use server actions instead of API routes", and ask Claude to merge it with existing rules rather than append (Anthropic CLAUDE.md video).
7. **Edits need a reload.** CLAUDE.md is read at session start; after editing, `/clear` or start a new session (Simon Scrapes).

### B. Permissions — decide by "Can I take it back?" (Hallie)
| Action | Reversible? | Handle with |
|---|---|---|
| Edit code, tests, docs; anything git can revert | Yes | Model judgment / auto mode |
| `git reset --hard`, force-push, deleting data, reading secrets, sending data outside | No | `permissions.deny` rule |

8. **Mode.** Flag `--dangerously-skip-permissions` / bypass mode as a default way of working (seen in two of the videos as a habit). Recommend auto mode or accept-edits plus allow rules instead.
9. **Deny rules for irreversible actions** — they are checked before any classifier:
   ```json
   "permissions": { "deny": ["Bash(git reset --hard *)", "Bash(git push --force*)", "Read(./.env)", "Read(~/.ssh/**)"] }
   ```
10. **Sandbox for code you didn't write.** `npm test` runs `node_modules` code that permissions never see. Enable `"sandbox": { "enabled": true }` (or `/sandbox`) and deny `Read(~/.ssh/**)` explicitly, since the sandbox can read most of the disk by default. Claude's own file tools, MCP servers and hooks run outside it (Hallie).
11. **Auto-mode tuning (verify on your version).** If auto mode prompts too often, describe trusted repos, buckets and domains in plain language under `"autoMode": {"environment": [...], "allow": [...], "hard_deny": [...]}` (Hallie, Nov 2026).

### C. Verification hooks (enforced, unlike CLAUDE.md text)
12. Fast check per edit, real check per task, full check at the end (Hallie; Zhang):
    | Event | Run |
    |---|---|
    | `PostToolUse` (Edit/Write) | formatter + lint/type-check on the changed file |
    | `TaskCompleted` (verify exists on your version) | tests for the area touched |
    | `Stop` | full test suite |
13. **Exit code 2, not 1.** A hook that fails with exit 1 lets Claude mark the task done; exit 2 sends it back to fix it. Wrap test runners: `npm test || exit 2` (Hallie).
14. Flag "run the build and all tests after every edit" written in CLAUDE.md: slow, and advisory only. Move it into hooks.

### D. Subagents, skills, commands
15. Reviewer/specialist agents in `.claude/agents/` follow this shape (Zhang's `security-reviewer.md`): **what to check** (a list), **how to work** ("read the relevant source files before making any claims"), **fixed output format** (Severity · file:line · Issue · Risk · Fix), and "don't pad the report".
16. Anything done more than once a week should be a skill or command (Zhang). `.claude/commands/` still works; new ones belong in `.claude/skills/`.

### E. Context cost
17. From `/context`: flag MCP servers unrelated to this project and oversized skills/agents. Tool search loads MCP schemas on demand in recent versions, so the cost of an idle server is now small; check before recommending removal (Simon Scrapes corrects his own older advice; Anthropic context video).
18. History: sessions are deleted after 30 days by default. Suggest `"cleanupPeriodDays": 365` if they use `/resume`. Do not suggest `0` (Simon Scrapes).

## Output

1. **Scorecard**: one line per section A-E: ✅ / ⚠️ / ❌ + one-sentence reason.
2. **Findings table**: `# | Severity (High/Med/Low) | File | Finding | Fix`. High = irreversible risk (no deny rules, bypass mode, secrets readable) or rules being ignored. Sort by severity. Say "none" for clean sections; don't pad.
3. **Diffs**: ready-to-apply edits for CLAUDE.md and settings.json (unified diff or full replacement blocks). Never apply them without the user's OK.
4. **Verify list**: any recommended setting marked "verify on your version", with the command to check it (`/doctor`, `/config`, `claude --help`).

## Sources
- Lydia Hallie (Anthropic), "Rethinking Claude Code Best Practices", Nov 2026 — https://www.youtube.com/watch?v=vlfCjWuv4es
- Simon Scrapes, "19 Claude Code Mistakes 'Pro' Users Are Still Making", Aug 2026 — https://www.youtube.com/watch?v=icM0ewXGvAw
- Anthropic, "The CLAUDE.md file", May 2026 — https://www.youtube.com/watch?v=O0FGCxkHM-U
- Anthropic, "Context Management in Claude Code", May 2026 — https://www.youtube.com/watch?v=eW3oTyfeWZ0
- Maddy Zhang, "How I use Claude Code (Senior Software Engineer Tips)", Apr 2026 — https://www.youtube.com/watch?v=MzhIr7BfpI0
- Steve (Builder.io), "How I use Claude Code", Jul 2025 — https://www.youtube.com/watch?v=n7iT5r0Sl_Y (bypass-mode habit flagged, not adopted)
