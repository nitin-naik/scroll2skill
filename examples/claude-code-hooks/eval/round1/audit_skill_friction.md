# Friction log: auditing-claude-code-hooks (draft1) on audit-fixture

## Friction items (quoted line, then what I guessed)

1. "Read every settings file in play: `~/.claude/settings.json`, ..." The task forbade reading outside the fixture, and the skill gives no fallback for when the user scope isn't available. Guess: audit the project scope only, and add a "check ~/.claude/settings.json for duplicates" note to the answer.
2. "If a script is missing or not executable, that is finding #1." Should it literally be row #1 of the table? That conflicts with "Answer the user's actual question first", and here the not-executable script (protect-env.sh) is unrelated to either symptom. Guess: put the symptom causes first and list the non-executable script as finding 4.
3. "Where possible, run each script with a crafted stdin". The skill doesn't say whether to run the scripts in place or on a copy, or how to set `CLAUDE_PROJECT_DIR`. Running in place could run `npm test` in the user's repo. Guess: run on a temp copy with `export CLAUDE_PROJECT_DIR=$copy`.
4. "Where possible ...". A matcher bug (`bash` vs `Bash`) can't be proved by running the script. The skill doesn't say how to show a config-level bug. Guess: state it as documented behaviour, without a proof command.
5. "Matcher on Stop/Notification is ignored [Better Stack t=1:58]". The cited timestamp t=1:58 is the same one used for the `.env` guard. It looks like a wrong citation, and I couldn't verify it. Guess: treat it as true, since it didn't matter here.
6. "Blocking requires exit 2 ... exit 1 (or any other code) only warns the user". It is unclear whether exit 126 or 127 (not executable or not found) count as "any other code". The robustness section says yes for 126. Guess: yes, they don't block.
7. "JSON output ... is only read on exit 0; JSON printed with exit 2 is ignored". protect-env.sh still *blocks* (exit 2 works) and only loses the reason. The skill's wording suggests the whole hook fails. Guess: rate it UNSAFE (wrong or missing reason), not BROKEN.
8. "Stop/SubagentStop hook that exits 2 ... without checking `stop_hook_active` loops forever." The skill gives no fix template and doesn't say what checking it means in practice. Does it allow one continuation or N? Guess: exit 0 when the flag is true (one push-back per stop) and mention a capped counter.
9. "Slow commands ... Narrow the matcher, set `timeout`, or mark logging hooks async". The skill gives no rule for picking among these options or for deleting the hook. Here the hook duplicates the Stop hook. Guess: delete it and give a narrowed async alternative.
10. "`rm -rf` checks miss `rm -fr`, `rm -r -f`, `/bin/rm`". The skill lists misses but gives no corrected pattern, and doesn't cover over-matching (`rm -rf /tmp/x`) or what the target set should be. Guess: write my own flag-order-independent check plus a dangerous-target list. Getting it right took two iterations (`sudo rm -Rf /*` and `git -C repo push -f` were missed at first).
11. "Missing jq / python3: decide fail-open (exit 1 + message) or fail-closed (exit 2) explicitly". For a Stop hook, which should it be? Failing closed there would cause the very loop the skill warns about. Guess: guards fail closed and the Stop hook fails open, with comments saying so.
12. "Return corrected settings and scripts in full." vs "Fixed files in full". The skill doesn't say whether to keep the user's file names and structure or how to handle a hook I recommend removing. Guess: keep the names, remove the PostToolUse hook, and show the alternative inline.
13. "Proof commands: the `echo ... | script; echo exit=$?` lines that show each fix". It doesn't say whether to show before *and* after. Guess: both.
14. Severity scale "BROKEN = never works / UNSAFE = wrong block or security hole". A guard that works in some cases but misses some patterns (force-push regex) could be BROKEN or UNSAFE. Guess: UNSAFE. The guard does run, but it misses cases.
15. "`hooks.<Event>` is an array ... [Claude official t=0:58]" plus "`Edit|Write` misses `MultiEdit` where it exists". The phrase "where it exists" leaves it unclear whether to add MultiEdit by default. Guess: add `MultiEdit|NotebookEdit`.
16. "check current docs (code.claude.com/docs, "Hooks reference")". This conflicts with environments where outside fetches aren't allowed. There's no guidance on writing claims you can't verify. Guess: use the skill's claims as given and mark version-dependent items (async).

## Coverage gaps (what a complete answer needed that the skill never asked for)

1. Mapping each user symptom to its *chain* of causes. The rm guard had 3 or 4 independent reasons it never blocked (matcher case, exit 1, relative path, narrow regex). The skill tells you to lead with *the* cause, singular.
2. Not-found command (exit 127) from a relative path, shown as also non-blocking. The skill mentions relative paths only as "break"; it doesn't say what the outcome is.
3. Stop hook dependencies: `npm test` failing because there is no package.json, or the wrong cwd, makes the loop permanent. The skill doesn't ask you to check that a gating command can succeed at all, or to `cd "$CLAUDE_PROJECT_DIR"`.
4. Passing test output back to Claude on a Stop block (stderr content). The original sent output to /dev/null, so Claude was told "keep fixing" with no information.
5. Over-blocking and false positives as a finding class (`*.env*` catching `.envrc`, `rm -rf /` catching any absolute path). The checklist only covers misses.
6. Behaviour changes caused by the fix. The user has to be told when the fixed guard allows something the old one (nominally) blocked.
7. Cross-tool bypass: the .env guard on Edit/Write doesn't stop Bash redirection. The skill mentions the reverse direction but doesn't recommend `permissions.deny` as the real control.
8. Recommending `permissions.deny` and sandboxing as defence in depth beyond string-matching hooks.
9. `chmod +x` as an explicit step in the fixed-files output (the files alone don't carry the mode).
10. Syntax-checking the fixed files (`jq .` on settings, `bash -n` on scripts) before returning them.
11. Testing the *fixed* scripts against a negative set (things that must still be allowed: `--force-with-lease`, `rm -rf node_modules`, `.env.example`), not just positives.
12. Committed vs local scope advice (`settings.local.json` for personal hooks). The skill notes the team impact but doesn't suggest a fix.
13. A Stop-hook retry design: one push-back per stop vs a capped counter keyed by `session_id`.
14. Per-hook `timeout` values for guards (short) vs test runners (long). The skill only mentions timeout for slow hooks.
15. Building JSON output with `jq -n --arg` instead of echoing a hand-written string. This prevents broken JSON when the reason contains a file path.
