# Claude Code setup audit: shopfront-api

**Verdict: don't run this unattended overnight yet.** Right now Claude would run in bypass mode with `Bash(*)` allowed, no deny rules and no sandbox. The directory is also not a git repository, so the "git can revert it" safety net doesn't exist here. Fix the High items first. They're all in the diffs below, and nothing has been applied.

Files read: `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/reviewer.md`, `package.json`, `src/`.
Missing: `.mcp.json`, `.claude/settings.local.json`, any hooks, `.claude/skills/`, `.claude/commands/`, CI workflow, `.git/`.
I couldn't measure token costs because `/context` and `/doctor` weren't available, so there are no token numbers below.

## 1. Scorecard

| Section | Status | Reason |
|---|---|---|
| A. CLAUDE.md | ❌ | It's short (28 lines), but it's mostly persona, shouting, a stack list and a folder tour, and it gives the wrong package manager and a `build` script that doesn't exist. |
| B. Permissions | ❌ | It defaults to `bypassPermissions` with `Bash(*)` allowed, has no deny rules or sandbox, and there's no git to undo with. |
| C. Verification hooks | ❌ | There are no hooks. The only check is an advisory "build + test after every edit" line in CLAUDE.md, and that build command would fail. |
| D. Subagents/skills/commands | ⚠️ | The single `reviewer` agent is one vague line with no checklist, no way of working and no output format. |
| E. Context cost | ⚠️ | 6 MCP servers are enabled but no `.mcp.json` defines them. I couldn't measure their cost without `/context`. |

## 2. Findings

| # | Severity | File | Finding | Fix |
|---|---|---|---|---|
| 1 | High | `.claude/settings.json:3` | `"defaultMode": "bypassPermissions"` is the default way of working, so nothing gets asked, even overnight. | Use auto mode (or `acceptEdits`) plus explicit allow rules (diff 2). |
| 2 | High | `.claude/settings.json:4` | `"allow": ["Bash(*)"]` allows every shell command. | Allow only the real pnpm scripts and read-only git (diff 2). |
| 3 | High | `.claude/settings.json` | There's no `permissions.deny`. `git reset --hard`, force-push, reading `.env` and `~/.ssh`, and `rm -rf` are all reachable. | Add deny rules for irreversible actions (diff 2). |
| 4 | High | `package.json:2` (`db:migrate`) | `prisma migrate deploy` changes a real database. Git can't undo that. | Deny `Bash(pnpm db:migrate*)`, `Bash(*prisma migrate*)` and `Bash(*prisma db push*)` (diff 2). |
| 5 | High | repo root | This isn't a git repository, so even "reversible" edits can't be undone. | Run `git init && git add -A && git commit -m baseline` (or work on a branch of the real repo) before any unattended run. |
| 6 | High | `.claude/settings.json` | There's no sandbox. `pnpm test` / `vitest` run `node_modules` code that permissions never see. | `"sandbox": {"enabled": true}` and deny `Read(~/.ssh/**)` (diff 2). Claude's own file tools, MCP servers and hooks still run outside the sandbox. |
| 7 | High | `CLAUDE.md:24-25` | It says "run npm run build" and "Use npm for everything", but the repo uses `pnpm@9.12.0` and there's **no `build` script**. Every edit would hit a failing command, and an unattended run could loop on it. | Use the real commands: `pnpm dev`, `pnpm test`, `pnpm lint`, `pnpm typecheck` (diff 1). |
| 8 | High | `CLAUDE.md:24` | "After every single edit, run … build and … test" is slow, and it's only advisory. | Move it into hooks (diff 2): typecheck/lint after each edit, full tests on `Stop`, using exit code 2. |
| 9 | Med | `CLAUDE.md:3` | Persona plus "Think hard and be thorough". Current models over-apply these. | Delete it. |
| 10 | Med | `CLAUDE.md:5-7` | "IMPORTANT", "ALWAYS…!!!", "NEVER. NEVER." Shouting makes current models over-apply rules. If a rule is being ignored, the fix is a shorter file, not louder text. | Rewrite as plain, positive rules (diff 1). |
| 11 | Med | `CLAUDE.md:10` | "Keep going until the task is completely done" pushes extra tool calls. It's risky combined with bypass mode overnight. | Delete it. Let the `Stop` hook decide "done". |
| 12 | Med | `CLAUDE.md:8-9` | These are negative rules ("Don't use default exports", "Don't put business logic in routes"). | Rewrite as positive rules: "Use named exports", "Put business logic in `src/services/`; routes only parse input and call a service". |
| 13 | Low | `CLAUDE.md:12-13` | The stack list is something Claude can read from `package.json`. | Delete it. |
| 14 | Low | `CLAUDE.md:15-21` | The folder tour is discoverable, and part of it is wrong: `src/services/`, `prisma/` and `tests/` don't exist. It also calls `src/legacy/` just "old code", which hides the one non-obvious fact. | Replace it with that fact: `src/legacy/checkout.ts` still serves iOS app v3 checkout (diff 1). |
| 15 | Low | `CLAUDE.md:27-28` | "Write clean code. Follow best practices." is generic advice. | Delete it. |
| 16 | Med | `.claude/agents/reviewer.md` | The description is "reviews code" and the body is "find all the problems. Be thorough." There's no checklist, no way of working and no output format. | Replace it with the structured agent (diff 3). |
| 17 | Med | `.claude/settings.json:6` | `enabledMcpjsonServers` lists github, postgres, slack, notion, linear and figma, but there's no `.mcp.json`. Either these come from somewhere I can't see, or they're dead config. slack/notion/linear/figma look unrelated to an API repo. `postgres` can write to a database and `slack` can send data outside. Both are irreversible, and MCP servers run outside the sandbox. | Keep only what overnight work needs (probably none, or `github` read-only). Run `/context` to check cost before removing on cost grounds. |
| 18 | Low | (habit) | Rules should come from corrections. Nothing in CLAUDE.md traces back to a repeated mistake. | When Claude gets something wrong twice, say "Put in CLAUDE.md: …" and ask it to merge the new rule into the existing ones. |
| 19 | Low | `.claude/settings.json` | Sessions are deleted after 30 days by default. | If you use `/resume` to review overnight runs, add `"cleanupPeriodDays": 365` (diff 2). |

Section E has no findings beyond #17. Token cost can't be assessed without `/context`.

## 3. Diffs (not applied; say the word and I'll apply them)

### Diff 1: `CLAUDE.md` (full replacement, 15 lines)

```markdown
# shopfront-api

## Commands (pnpm only)
- Dev: `pnpm dev`
- Tests: `pnpm test` (all), `pnpm test:unit` (src only)
- Lint: `pnpm lint` (zero warnings allowed)
- Types: `pnpm typecheck`
- Leave `pnpm db:migrate` to a human; it changes the real database.

## Rules
- Use explicit types; reach for `unknown` plus narrowing where a type is truly open.
- Use named exports.
- Put business logic in services; routes only parse input and call a service.
- Add or update a Vitest test for every behaviour change.
- Treat `src/legacy/checkout.ts` as live: it still serves iOS app v3 checkout. Keep its exports and behaviour stable.
```

Edits to CLAUDE.md take effect only in a new session, so run `/clear` or restart after applying.

### Diff 2: `.claude/settings.json` (full replacement)

```json
{
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "Bash(pnpm test*)",
      "Bash(pnpm lint*)",
      "Bash(pnpm typecheck*)",
      "Bash(pnpm dev*)",
      "Bash(pnpm exec vitest*)",
      "Bash(pnpm exec eslint*)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)"
    ],
    "deny": [
      "Bash(git reset --hard *)",
      "Bash(git push --force*)",
      "Bash(git push -f*)",
      "Bash(git clean *)",
      "Bash(rm -rf *)",
      "Bash(pnpm db:migrate*)",
      "Bash(*prisma migrate*)",
      "Bash(*prisma db push*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(~/.ssh/**)"
    ]
  },
  "sandbox": { "enabled": true },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "pnpm -s typecheck && pnpm -s lint || exit 2" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "pnpm -s test || exit 2" }
        ]
      }
    ]
  },
  "enabledMcpjsonServers": [],
  "cleanupPeriodDays": 365
}
```

Notes:
- The hooks use **exit code 2**. With exit 1, Claude can still mark the task done. With exit 2, it goes back and fixes the problem.
- The per-edit hook runs a whole-project typecheck and lint because there's no per-file script. If that's slow, swap in `pnpm exec eslint "$FILE"` once you've wired the changed-file path from the hook input.
- A `TaskCompleted` hook running `pnpm test:unit` would add the middle tier (tests per task). Add it only after confirming your version supports that event (see the verify list).
- `enabledMcpjsonServers` is emptied because no `.mcp.json` exists. Re-add only servers you actually define and need overnight.
- If auto mode prompts too often, describe trusted repos and domains in plain language under `"autoMode": {"environment": [...], "allow": [...], "hard_deny": [...]}`. Verify this on your version first.

### Diff 3: `.claude/agents/reviewer.md` (full replacement)

```markdown
---
name: reviewer
description: Reviews changed TypeScript/Express code in shopfront-api for correctness, type safety, layering and legacy-checkout breakage. Use after a feature or fix is complete.
---
## What to check
- Type safety: no `any`, unchecked casts, or unhandled promise rejections
- Layering: business logic in services, routes only parse input and call a service
- `src/legacy/checkout.ts`: exports and behaviour unchanged (iOS app v3 depends on it)
- Tests: each behaviour change has a Vitest test that would fail without it
- Security: input validation on routes, auth checks in `src/routes/auth.ts`, no secrets in code

## How to work
Read the relevant source files and the diff before making any claim. Cite file:line for every finding.

## Output format
One row per finding: Severity · file:line · Issue · Risk · Fix.
If there are no findings, say "No findings." Don't pad the report.
```

## 4. Verify on your version

| Setting | Why | Check with |
|---|---|---|
| `"defaultMode": "auto"` | Auto mode's name and availability vary by version. Fall back to `"acceptEdits"` if it isn't accepted. | `/config`, `claude --help` |
| `TaskCompleted` hook event (suggested, not in diff 2) | It may not exist on older versions. | `/doctor`, `/hooks` |
| `autoMode` block (`environment` / `allow` / `hard_deny`) | It's newer, and the schema may differ. | `/doctor` (reports invalid settings) |
| `sandbox.enabled` | Confirm the sandbox is supported on your OS and active. | `/sandbox`, `/doctor` |
| Where the 6 MCP servers come from, and what they cost | There's no `.mcp.json` in the repo. | `/mcp`, `/context` |
| Settings file is valid after edits | It catches typos in the new JSON. | `/doctor` |

**Before the overnight run:** apply diffs 1 and 2, run `git init` and commit a baseline, restart the session, then run `/doctor` and `/context` once to confirm everything is clean.
