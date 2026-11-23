# Friction log: claude-code-setup-audit skill (cold run)

1. **"If the user can run commands, ask for the output of `/context` … Do not guess token numbers."** The skill doesn't say what to do when the user *can't* run them, or whether to stop and wait for the output. I guessed: go ahead without them, mark section E as partial, and put `/context` and `/doctor` in the verify list.

2. **"Read whichever exist; note missing ones as findings."** This conflicts with "Say 'none' for clean sections; don't pad." Missing `.claude/skills/`, `commands/`, CI and `settings.local.json` are normal, not problems. I guessed: list missing files in one header line and only raise a finding where the absence matters (for example, `.mcp.json` missing while servers are enabled).

3. **Section B table: "anything git can revert → Yes".** The skill assumes git exists. It doesn't cover a repo that isn't under git, where nothing is reversible. I guessed: rate that High and recommend `git init` plus a baseline commit.

4. **Deny-rule list (check 9).** It covers git, `.env` and `~/.ssh` only. Database migrations (`prisma migrate deploy`) and MCP servers that write or send data (postgres, slack) are irreversible under the skill's own "Can I take it back?" test, but they're not listed. I guessed: extend the deny rules to migrations and flag the risky MCP servers.

5. **Check 8: "Recommend auto mode or accept-edits".** The skill doesn't give the settings.json value for auto mode (`"defaultMode": "auto"`?), and it marks only check 11 as "verify on your version". I guessed `"auto"`, offered `acceptEdits` as the fallback, and added it to the verify list.

6. **Check 12: "`PostToolUse` (Edit/Write) | formatter + lint/type-check on the changed file".** The skill gives no hook JSON shape and doesn't say how to get the changed file path into the command. I guessed the standard `hooks` / `matcher` / `type: command` shape and used whole-project typecheck and lint, noting the per-file option.

7. **Check 12: "`TaskCompleted` (verify exists on your version)".** The skill doesn't say whether to include the hook in the ready-to-apply diff or only suggest it. I guessed: leave it out of the diff and mention it with a verify entry, so the diff stays safe to apply.

8. **Output item 2: "High = irreversible risk … or rules being ignored".** The skill doesn't say where a wrong or nonexistent command in CLAUDE.md fits (npm vs pnpm, a `build` script that doesn't exist). For unattended work it can cause loops. I guessed High.

9. **Check 2's shouting list.** It includes "keep going until done" but doesn't give a severity for persona and shouting. I guessed Med, and stack/folder/generic-advice clutter as Low.

10. **Check 16: "Anything done more than once a week should be a skill or command".** From a static repo I can't know how often things happen. I guessed: skip it, with no finding.

11. **Check 17: "From `/context`: flag MCP servers unrelated to this project".** The skill doesn't cover the case where there's no `/context` output and no `.mcp.json` but `enabledMcpjsonServers` is set. I guessed: flag it as possibly dead config and a risk (outside the sandbox), not as a cost issue.

12. **Output item 3: "unified diff or full replacement blocks".** The skill doesn't say which to use. I picked full replacements because the files are small.

13. **Scorecard.** The skill doesn't say whether to give an overall verdict, but the user's actual question was "safe to run overnight?" I guessed: add a one-line verdict at the top and a short pre-flight list at the end. Neither is part of the skill's output template.

14. **Check 7 ("Edits need a reload").** This is a fact to tell the user, not something to check, and the output template has no place for it. I put it as a note under diff 1.
