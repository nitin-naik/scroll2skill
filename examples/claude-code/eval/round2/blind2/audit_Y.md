# Claude Code setup review: shopfront-api

**Verdict: Not safe to run unattended yet.** It becomes safe once you apply the fixes below and work through the pre-flight list at the end. The main blockers:

- The repo has no git history, so nothing Claude does overnight can be undone.
- Claude runs in bypass mode with `Bash(*)`, so it can run any command without asking.
- Claude has no way to check its work: there are no hooks, and every check command in the repo either doesn't exist or will fail right now.

Files read: `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/reviewer.md`, `package.json`, `src/**`.
Not present: `.claude/settings.local.json`, `.mcp.json`, `.claude/skills/`, `.claude/commands/`, CI workflow, `tsconfig.json`, ESLint config, `prisma/`, `tests/`, `src/server.ts`, lockfile, `node_modules`. You asked me to leave out `~/.claude`, so I did.
Not measured: `/context` and `/doctor` (you can't run them right now).

## 1. Scorecard

| Section | Status | Reason |
|---|---|---|
| A. CLAUDE.md | ❌ | It names commands that don't exist (`npm run build`) and the wrong package manager (npm instead of pnpm). The rest is persona, shouting, "don't" rules and a folder tour of folders that don't exist. |
| B. Permissions | ❌ | Bypass mode plus `Bash(*)`, no deny rules, no sandbox, no git, and nothing protects `src/legacy` or `db:migrate`. |
| C. Verification hooks | ❌ | There are no hooks. "Run build and tests after every edit" lives in CLAUDE.md as advice, and the commands it names fail. |
| D. Subagents / skills / commands | ⚠️ | `reviewer` is vague and has no `tools:` limit, so under bypass mode it inherits unrestricted Bash. |
| E. Context cost | ⚠️ partial, not measured | Six MCP servers are enabled but there is no `.mcp.json`. I can't see the token cost without `/context`. |
| F. Unattended run | ❌ | There's no branch to work on, no turn cap and no stop rules. Write-capable MCP servers (postgres, slack, notion, linear) are enabled. |

## 2. Findings

| # | Severity | File | Finding | Fix |
|---|---|---|---|---|
| 1 | High | (repo) | Not a git repository (`git rev-parse` fails). Nothing Claude edits overnight can be reverted or reviewed as a diff. | `git init && git add -A && git commit -m "baseline"`, then work on a new branch. |
| 2 | High | `.claude/settings.json` | `"defaultMode": "bypassPermissions"` plus `"allow": ["Bash(*)"]` lets every command run without a prompt, including irreversible ones. | Switch to `acceptEdits` with specific pnpm/git allow rules (diff below). |
| 3 | High | `.claude/settings.json` | There are no deny rules. `pnpm db:migrate` (`prisma migrate deploy`) can reach a real database. `git push`/`reset --hard`, `.env` and `~/.ssh` are all open. | Add a `permissions.deny` list (diff below). Deny rules are checked before anything else. |
| 4 | High | `CLAUDE.md:24-25` | It says to run `npm run build` and "use npm for everything". There is no `build` script, and `package.json` pins `pnpm@9.12.0`. Claude will hit a missing script after every edit and may install a stray `package-lock.json`. | Name the real commands: `pnpm test`, `pnpm lint`, `pnpm typecheck`. `typecheck` is the compile check. |
| 5 | High | `package.json` / repo | None of the check commands can pass yet. There's no `tsconfig.json` (`tsc --noEmit` fails), no ESLint config (`eslint .` fails on ESLint 9), no test files (`vitest run` exits 1 with "No test files found"), and no `node_modules`. `dev` points at a missing `src/server.ts`. Any hook built on these fails every time. | Before going overnight, add `tsconfig.json`, `eslint.config.js` and at least one test, run `pnpm install`, and confirm all three commands pass by hand. |
| 6 | High | `src/legacy/checkout.ts:1`, `CLAUDE.md:19` | Its own comment says `legacyCheckout` is "still used by iOS app v3 checkout", but CLAUDE.md calls `src/legacy` "old code", which invites a cleanup. | Mechanical deny: `"Edit(./src/legacy/**)"`. State the real reason in CLAUDE.md. |
| 7 | High | `.claude/settings.json:6` | `postgres`, `slack`, `notion`, `linear` and `github` can all write or send outside the repo. There's also no `.mcp.json`, so these entries are either stale or depend on config this repo doesn't hold. | For unattended runs, set `"enabledMcpjsonServers": []`. If you do want them, commit a `.mcp.json` and deny their write tools. |
| 8 | High | `.claude/settings.json` | No sandbox. `pnpm test`/`pnpm install` run third-party code from `node_modules` that permission rules never see. | `"sandbox": { "enabled": true }`, and keep `Read(~/.ssh/**)` denied explicitly. |
| 9 | Med | `.claude/settings.json` | No verification hooks. "After every single edit, run…" in CLAUDE.md is only advice, and running the full suite on every edit is slow. | Add a `PostToolUse` lint on the edited file and a `Stop` typecheck plus tests, both exiting 2 on failure (diff below). |
| 10 | Med | `CLAUDE.md:3,5-7,10` | Persona ("world-class senior… 20 years"), "Think hard", "IMPORTANT", "ALWAYS…!!!", "NEVER. NEVER.", "Keep going until the task is completely done". Current models over-apply these and make extra tool calls. In an overnight run, "keep going until done" works against any stop rule. | Delete them. Keep the file short so its rules carry weight on their own. |
| 11 | Med | `CLAUDE.md:7-9` | Rules are phrased as "don't…". | Rephrase them as what to do: "Use named exports", "Keep route handlers thin; put logic in `src/services/`", "Type unknown input as `unknown` and narrow it". |
| 12 | Med | `.claude/agents/reviewer.md` | `description: reviews code`, body "find all the problems. Be thorough." It has no checklist, no output format and no `tools:` line, so it inherits `Bash(*)`. | Give it `tools: Read, Grep, Glob`, a what-to-check list, a read-before-claiming rule and a fixed output format (diff below). |
| 13 | Low | `CLAUDE.md:12-21` | The stack list and folder tour are things Claude can read from `package.json` and the tree. Three of the listed folders (`src/services/`, `prisma/`, `tests/`) don't exist. | Remove both. Keep only the facts the code can't tell Claude (the legacy/iOS one). |
| 14 | Low | `CLAUDE.md:28` | "Write clean code. Follow best practices. Use meaningful names." is generic advice. | Remove it. Add a rule later only when Claude gets something wrong more than once. |

## 3. Diffs (not applied; they need your OK)

### `CLAUDE.md` (full replacement)

```markdown
# shopfront-api

## Commands (pnpm only; version pinned in package.json)
- Install: `pnpm install`
- Dev server: `pnpm dev`
- Tests: `pnpm test` (all), `pnpm test:unit` (src only)
- Lint: `pnpm lint` · Type-check: `pnpm typecheck`
- There is no build script; `pnpm typecheck` is the compile check.
- `pnpm db:migrate` runs `prisma migrate deploy` against a real database. A human runs it.

## Things the code won't tell you
- `src/legacy/` still serves checkout for the iOS app v3. Keep its behavior and exports exactly as they are; put new code elsewhere.
- Route handlers in `src/routes/` stay thin: parse the request, call a service in `src/services/`, return the response.

## Conventions
- Use named exports.
- Type unknown input as `unknown` and narrow it; give everything else a concrete type.
- Add or update a Vitest test with every behavior change.
```

After you replace it, run `/clear` or start a new session. CLAUDE.md is only read when a session starts.

### `.claude/settings.json` (full replacement)

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(pnpm install)",
      "Bash(pnpm test*)",
      "Bash(pnpm lint*)",
      "Bash(pnpm typecheck*)",
      "Bash(pnpm exec eslint*)",
      "Bash(pnpm exec vitest*)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git switch -c*)"
    ],
    "deny": [
      "Bash(git reset --hard*)",
      "Bash(git push*)",
      "Bash(git clean*)",
      "Bash(pnpm db:migrate*)",
      "Bash(*prisma migrate*)",
      "Bash(*prisma db push*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(~/.ssh/**)",
      "Edit(./src/legacy/**)"
    ]
  },
  "sandbox": { "enabled": true },
  "enabledMcpjsonServers": [],
  "hooks": {
    "PostToolUse": [{ "matcher": "Edit|Write|MultiEdit", "hooks": [{ "type": "command",
      "command": "f=$(jq -r '.tool_input.file_path'); case \"$f\" in *.ts|*.tsx|*.js|*.mjs) pnpm exec eslint --fix \"$f\" >&2 || exit 2;; esac" }] }],
    "Stop": [{ "hooks": [{ "type": "command",
      "command": "[ \"$(jq -r '.stop_hook_active')\" = true ] && exit 0; { pnpm typecheck && pnpm test; } >&2 || exit 2" }] }]
  }
}
```

Notes on this diff:
- `Bash(git push*)` blocks every push, which covers force pushes and pushes to `main`. For an overnight run, nothing should leave the machine. If you push during the day, move that rule to `.claude/settings.local.json`.
- Exit code 2 sends Claude back to fix the failure; exit 1 would let it mark the task done. The `stop_hook_active` guard stops a test that can never pass from looping all night.
- These hooks only work once finding 5 is fixed. Until there's an ESLint config, a tsconfig and a test, they block every edit and every stop.
- You can also add a `TaskCompleted` hook that runs `pnpm test:unit` for the area touched. Check that your version supports it first; I left it out of the diff.
- The hooks need `jq` on your PATH.

### `.claude/agents/reviewer.md` (full replacement)

```markdown
---
name: reviewer
description: Reviews a diff or files in shopfront-api for correctness, type-safety and security issues. Use after a change is finished and before committing.
tools: Read, Grep, Glob
---
Review the diff or files you are given.

What to check:
- Logic errors and unhandled edge cases
- Type holes: `any`, unchecked casts, request input used without validation
- Business logic placed in `src/routes/` instead of a service
- Any change under `src/legacy/` (it serves iOS app v3 checkout; flag every one)
- Auth and session handling in `src/routes/auth.ts`
- Changed behavior without a matching test

How to work: read the relevant source files before making any claim, and report only issues you can point to in the code.

Output, one row per issue, most severe first:
Severity · file:line · Issue · Risk · Fix

If there are no issues, say so in one line. Don't pad the report.
```

### Overnight launch command (replaces an interactive bypass session)

```bash
git switch -c overnight/<task-name>
claude -p "<task>. Done when: pnpm typecheck, pnpm lint and pnpm test pass and the work is committed on this branch.
Rules: commit after each green step; never push or merge. If the same failure happens 3 times, stop and write NOTES-overnight.md explaining it.
If the task needs a Prisma schema change, a new dependency, or any change under src/legacy, stop and write the note instead." \
  --permission-mode acceptEdits --max-turns 60 --output-format json > run.json
```

In `-p` mode, a command outside the allow list is refused instead of waiting for you, so a blocked step fails cleanly and doesn't stall all night. In the morning, review `git diff main...overnight/<task-name>` and `run.json`. Change `--max-turns` to suit the size of the task.

## 4. Verify list

| Item | How to check |
|---|---|
| `acceptEdits`, `sandbox.enabled`, `Edit(...)` deny syntax are valid on your version | `/doctor` (it reports settings errors) and `/config` |
| Your version has auto mode, as an alternative to `acceptEdits`, and what its setting value is | `/config`, `claude --help` |
| `TaskCompleted` hook event exists | `/hooks` |
| `-p`, `--permission-mode`, `--max-turns`, `--output-format` flags | `claude --help` |
| Context cost of agents, skills and MCP servers (section E) | `/context` |
| Whether the six MCP servers come from somewhere other than this repo | `/mcp` |
| `jq` installed for the hooks | `which jq` |

## Pre-flight (do these in order before starting the run)

1. `git init`, then make a baseline commit.
2. Apply the three diffs above, then run `/clear` or start a new session.
3. Add `tsconfig.json`, `eslint.config.js` and at least one Vitest test. Run `pnpm install`, `pnpm typecheck`, `pnpm lint` and `pnpm test`, and confirm all four succeed by hand.
4. Run `/doctor` and `/context`, and fix any settings errors they report.
5. Make sure there's no `.env` with production credentials or `DATABASE_URL` pointing at a shared database in the working copy. Better still, run the job in a container, VM or cloud session that has no `.env` and no SSH keys.
6. Create the overnight branch and launch with the `claude -p … --max-turns … > run.json` command above.
7. In the morning, review the branch diff, `run.json`, and any `NOTES-overnight.md`.
