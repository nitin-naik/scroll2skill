# Claude Code setup review: shopfront-api

**Verdict: don't run this unattended yet.** The current config gives Claude unrestricted shell access with no prompts, and CLAUDE.md tells it to run a command that doesn't exist and to use the wrong package manager. Overnight, that means it will either loop on a failing `npm run build` or do something you can't undo. Fix the five blockers below first (about 20 minutes), then run it in a sandboxed, scoped way.

What I reviewed: `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/reviewer.md`, `package.json`, `src/`. Nothing was modified.

---

## Blockers (fix before any unattended run)

### 1. `bypassPermissions` + `Bash(*)` means there are no guardrails at all
`.claude/settings.json`:
```json
"defaultMode": "bypassPermissions",
"allow": ["Bash(*)"]
```
Claude can run anything without asking: `rm -rf`, `git push --force`, `curl … | sh`, and **`pnpm db:migrate`** (`prisma migrate deploy`), which applies migrations to whatever `DATABASE_URL` points at. Also, `Bash(*)` is redundant under bypass mode. Bypass mode skips the allow list completely.

Also note: **this directory is not a git repository.** If Claude makes a bad edit overnight, you have no history to diff or revert. Run `git init && git add -A && git commit -m baseline` (or work from your real clone) before you start anything.

Replace the settings with an explicit allow/deny list and the default mode:
```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(pnpm test*)",
      "Bash(pnpm test:unit*)",
      "Bash(pnpm lint*)",
      "Bash(pnpm typecheck*)",
      "Bash(pnpm exec vitest*)",
      "Bash(pnpm exec eslint*)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git checkout -b*)",
      "Bash(git switch*)"
    ],
    "deny": [
      "Bash(pnpm db:migrate*)",
      "Bash(*prisma migrate*)",
      "Bash(*prisma db push*)",
      "Bash(git push*)",
      "Bash(git reset --hard*)",
      "Bash(rm -rf*)",
      "Bash(curl*)",
      "Bash(wget*)",
      "Read(./.env*)",
      "Edit(./.env*)"
    ]
  }
}
```
For an unattended run, launch headless so a blocked tool fails cleanly instead of waiting for you all night:
```bash
claude -p "<task>" --permission-mode acceptEdits --max-turns 60 --output-format json > overnight.json
```
If you really want bypass mode, only use it inside a throwaway container or VM with no production credentials and no network access beyond the package registry (Anthropic's devcontainer reference setup does this). On your laptop, with your shell env, it isn't safe.

### 2. CLAUDE.md's workflow commands are wrong, so Claude will spin
- `npm run build`: **there is no `build` script** in `package.json`. Claude will fail on every edit and then try to "fix" it by inventing a build script or changing tsconfig.
- "Use npm for everything" contradicts `"packageManager": "pnpm@9.12.0"`. With npm, Claude will create a `package-lock.json` and may install a different dependency tree.
- "After every single edit, run build and test" means a full `vitest run` after each one-line change. Over a whole night that wastes most of the turn and token budget.

Replace the section with:
```markdown
## Commands (pnpm only, never npm or yarn)
- Typecheck: `pnpm typecheck`
- Lint: `pnpm lint`  (zero warnings allowed)
- Unit tests: `pnpm test:unit`; run a single file with `pnpm exec vitest run path/to/file.test.ts`
- Full suite: `pnpm test`
- There is no build step. Do not add one.

## Workflow
Run the relevant test file while iterating. Before you call a task done, run `pnpm typecheck && pnpm lint && pnpm test` and make sure all three pass.
```

### 3. Nothing protects the code that must not change
`src/legacy/checkout.ts` has a comment saying `// still used by iOS app v3 checkout`, but CLAUDE.md just calls `src/legacy/` "old code". If you also tell it "keep going until completely done" and "follow best practices", a cleanup pass may delete or "modernize" it. Add a rule:
```markdown
## Do not touch
- `src/legacy/**`: still called by iOS app v3. Don't edit, rename, or delete it unless the task says to.
- `prisma/migrations/**`: never edit existing migrations, and never run migrate commands.
- `.env*`: never read or edit.
```
You can also enforce this mechanically with `"deny": ["Edit(./src/legacy/**)"]`.

### 4. MCP servers listed with no config, and too many
`enabledMcpjsonServers` auto-approves `github, postgres, slack, notion, linear, figma`, but there's **no `.mcp.json`** in the repo. Right now they either don't load or they come from somewhere you aren't tracking. If they do load:
- `postgres` and `github` combined with bypass mode let Claude write to a database or push/comment on GitHub without asking.
- `slack` lets it post messages while you're asleep.
- Every server's tool definitions take up context in every turn.

For an overnight coding task, enable none of them, or at most read-only `github`. Remove the line, or set it to `[]`.

### 5. "Keep going until the task is completely done" with no stopping rule
Unattended, this encourages scope creep and endless retry loops. Replace it with explicit stop conditions:
```markdown
## When to stop
- Stop and write up your findings in `NOTES.md` if the same check fails 3 times in a row with the same error, if the task needs a schema or migration change, or if it needs a new dependency.
- Work on a branch named `claude/<task>`. Commit after each green step. Never push.
```

---

## Should fix (quality, not safety)

| Issue | Why it matters | Fix |
|---|---|---|
| "World-class senior engineer with 20 years…", "Think hard", "Write clean code. Follow best practices. Use meaningful names." | Spends tokens on every turn and changes nothing. Claude already does these things. | Delete. |
| `IMPORTANT`, `ALWAYS`, `!!!`, `NEVER. NEVER.` | When everything is shouted, nothing stands out. Overemphasis can also make Claude over-apply rules, for example writing tests for config changes. | Use plain imperatives. Keep emphasis for the one or two rules that would really hurt to break, such as the legacy and migration rules. |
| "NEVER use any" | Fine as a rule, but it isn't enforced. | Turn on `@typescript-eslint/no-explicit-any` as an error. `pnpm lint` then enforces it, and the CLAUDE.md line can stay as a one-line reminder. |
| Project structure lists `src/services/`, `prisma/`, `tests/` | None of them exist in this checkout. Claude will hunt for them or create `tests/` while your Vitest setup expects something else. | List only real paths and say where tests go, e.g. "Tests are colocated as `*.test.ts` next to the source" (or whatever is true). |
| "Don't put business logic in routes" | Good rule, but there is no services layer to point to. | Add "Put logic in `src/services/<domain>.ts` and keep route handlers to parse, call, respond." |
| Stack line | Mostly fine. | Keep it. Add Express 4 error-handling conventions if you have any. |

## `.claude/agents/reviewer.md`
```yaml
name: reviewer
description: reviews code
```
- Claude uses the `description` to decide when to invoke an agent automatically. "reviews code" is too vague to trigger reliably. Say when to use it, for example: "Use after finishing a change to review the diff against main for bugs, missing tests, and CLAUDE.md violations. Read-only."
- No `tools:` line, so it inherits **every** tool, including Edit and Bash under bypass mode. A reviewer should be read-only: `tools: Read, Grep, Glob, Bash(git diff*)`.
- "Find all the problems. Be thorough." produces long nitpick lists. Give it scope and an output format:
```markdown
Review `git diff main...HEAD` only.
Report only real issues: bugs, security problems, missing or weak tests, broken CLAUDE.md rules.
For each one, give file:line, the problem, and a suggested fix. Sort by severity. Skip style issues that lint already catches.
If you find nothing, say so.
```

---

## Recommended overnight setup (once the above is fixed)
1. Make sure it's a git repo with a clean baseline commit, then `git switch -c claude/<task>`.
2. Use the settings above (`acceptEdits` + allow/deny lists). Leave MCP off.
3. Run it headless with a turn cap, and give it a scoped task with a concrete done condition:
   ```bash
   claude -p "Task: <one specific thing>. Done when pnpm typecheck, pnpm lint and pnpm test all pass and the new behaviour has tests. Commit on this branch after each green step. Don't push. If blocked, write the reason in NOTES.md and stop." \
     --permission-mode acceptEdits --max-turns 60 --output-format json > overnight.json
   ```
4. In the morning, review `git log`, `git diff main...`, `NOTES.md` and `overnight.json`, then run the `reviewer` agent on the diff.

I couldn't check your user-level `~/.claude` settings, plugins, or hooks, or run `/context` and `/doctor`. When you can, run `/doctor` and `/context` once to confirm which MCP servers actually load and how much context CLAUDE.md and the tools use.
