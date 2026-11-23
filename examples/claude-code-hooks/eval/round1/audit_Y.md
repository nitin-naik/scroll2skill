# Hook audit: `.claude/settings.json` + `.claude/hooks/`

## Why your two symptoms happen

**The rm guard never blocks: three separate bugs, any one of them enough to break it.**
1. **It never runs.** `settings.json:4` has `"matcher": "bash"`. Matchers are case-sensitive and the tool is called `Bash`, so `guard.sh` is never called.
2. **If it did run, it still would not block.** `guard.sh:4-5` prints the reason to stdout and does `exit 1`. Only **exit 2** blocks, and Claude reads the reason from **stderr**. With exit 1 the user sees a warning and `rm` runs anyway. I confirmed this: `rm -rf /` returns `exit=1`.
3. **The pattern is too narrow and too broad at once.** `grep 'rm -rf /'` misses `rm -fr ~`, `rm -r -f /`, `rm -rf $HOME` and `rm -rf .`. It also matches harmless commands like `rm -rf /tmp/build`.

There is also a fourth problem. `.claude/hooks/guard.sh` is a relative path, so if Claude has `cd`'d into a subfolder the hook can't be found (exit 127, which does not block either).

**Claude never stops:** the `Stop` hook `keep-going.sh` exits 2 whenever `npm test` fails, and it never checks `stop_hook_active`. While the tests keep failing (or `npm test` can't run at all, for example when there is no `package.json`), every stop attempt gets blocked, forever. I confirmed it: with `{"stop_hook_active":true}` as input it still returns `exit=2`.

## Verdict
4 hooks, 13 findings. Worst: the Stop hook loops forever, and both "guards" are effectively off (the rm guard never fires, and `protect-env.sh` isn't executable).

## Findings

| # | Severity | File:line | Problem | Fix |
|---|---|---|---|---|
| 1 | BROKEN | settings.json:4 | Matcher `bash` never matches tool `Bash`, so guard.sh never runs | `"matcher": "Bash"` |
| 2 | BROKEN | guard.sh:4-5 | rm block uses `exit 1` and stdout, so it only warns and the rm runs | Reason to stderr, `exit 2` |
| 3 | BROKEN | keep-going.sh:2-4 / settings.json:14 | Stop hook blocks with no `stop_hook_active` check, so it loops forever while tests fail | Read stdin and `exit 0` when `stop_hook_active` is true |
| 4 | BROKEN | protect-env.sh (mode 644) | Not executable: exit 126, which doesn't block, so the .env guard is silently off | `chmod +x .claude/hooks/*.sh` |
| 5 | BROKEN | settings.json:5 | Relative path `.claude/hooks/guard.sh` fails (127) when cwd isn't the project root | `"\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.sh"` |
| 6 | UNSAFE | guard.sh:3 | `rm -rf /` regex misses `-fr`, `-r -f`, `-Rf`, `--recursive`, `~`, `$HOME`, `.`, `*`, and over-matches any absolute path (`/tmp/build`) | Flag-order-independent check plus a dangerous-target list (below) |
| 7 | UNSAFE | guard.sh:7 | `--force[^-]` misses a trailing `--force` (`git push origin main --force` returns exit 0), `-f`, and `+refspec` | Match `--force`/`-f` as whole words and `+ref`; still allow `--force-with-lease` |
| 8 | UNSAFE | protect-env.sh:5-6 | JSON `deny` printed with `exit 2` is ignored. It blocks only because of the exit code, and the reason is lost (empty stderr) | Print the JSON and `exit 0` (or use stderr and exit 2, but not both) |
| 9 | UNSAFE | protect-env.sh:4 | `*.env*` blocks `.env.example`/`.env.sample` and also matches `.envrc` | Match on basename: `.env` / `.env.*`, with an explicit allow for `.env.example\|.sample\|.template` |
| 10 | UNSAFE | settings.json:6 | `Edit\|Write` misses `MultiEdit` and `NotebookEdit` | `Edit\|Write\|MultiEdit\|NotebookEdit` |
| 11 | SLOW | settings.json:10-11 | `npm test` on PostToolUse with matcher `*` and no timeout runs the whole suite after **every** tool call (including Read/Grep), and it duplicates the Stop hook | Remove it (the Stop hook already gates on tests), or see the alternative below |
| 12 | STYLE | protect-env.sh:2-3 | Reads stdin twice, so `TOOL` is always empty (proved with `bash -x`) | `INPUT=$(cat)` once, then `jq` on `$INPUT` |
| 13 | STYLE | settings.json:7; guard.sh:2; protect-env.sh:2 | Unquoted `$CLAUDE_PROJECT_DIR` breaks on paths with spaces. If `jq` is missing, both guards fail **open** (empty input, so exit 0) | Quote the path. The guards check for `jq` and fail **closed** (exit 2) |

## Fixed files

### `.claude/settings.json`
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.sh", "timeout": 10 } ] },
      { "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-env.sh", "timeout": 10 } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/keep-going.sh", "timeout": 300 } ] }
    ]
  }
}
```
(The PostToolUse `npm test` is removed on purpose; see finding 11. If you want tests after each edit, use `{"matcher":"Edit|Write|MultiEdit","hooks":[{"type":"command","command":"cd \"$CLAUDE_PROJECT_DIR\" && npm test","timeout":120,"async":true}]}`. `async` depends on your Claude Code version, and an async hook's result doesn't reach Claude.)

### `.claude/hooks/guard.sh`
```bash
#!/bin/bash
# PreToolUse guard for Bash. Blocks with exit 2 + reason on stderr.
# Security guard: fails CLOSED if jq is missing.
command -v jq >/dev/null 2>&1 || { echo "guard.sh: jq not installed; blocking Bash until it is" >&2; exit 2; }

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# 1. Recursive rm (any flag order/spelling, any rm path) aimed at /, ~, $HOME, ., .., or *
if printf '%s' "$CMD" | grep -qE '(^|[^[:alnum:]_.-])rm[[:space:]]' &&
   printf '%s' "$CMD" | grep -qE '[[:space:]](-[[:alpha:]]*[rR][[:alpha:]]*|--recursive)([[:space:]]|$)' &&
   printf '%s' "$CMD" | grep -qE '[[:space:]]"?(/\*?|~/?\*?|\$HOME/?\*?|\$\{HOME\}/?\*?|\*|\./?\*?|\.\./?)"?([[:space:]]|[;&|)]|$)'; then
  echo "Blocked: recursive rm on /, ~, \$HOME, ., .. or *. Delete a specific path instead." >&2
  exit 2
fi

# 2. Force push (--force or -f anywhere, or +refspec); --force-with-lease is allowed
if printf '%s' "$CMD" | grep -qE '(^|[^[:alnum:]_-])git[[:space:]].*push' &&
   printf '%s' "$CMD" | grep -qE '[[:space:]](--force|-f)([[:space:]]|$)|[[:space:]]\+[^[:space:]]+'; then
  echo "Blocked: force push. Use --force-with-lease if you really mean it." >&2
  exit 2
fi
exit 0
```

### `.claude/hooks/protect-env.sh`
```bash
#!/bin/bash
# PreToolUse guard for Edit/Write/MultiEdit/NotebookEdit: no edits to real .env files.
# Uses JSON deny on exit 0 (JSON is ignored on exit 2). Fails CLOSED without jq.
command -v jq >/dev/null 2>&1 || { echo "protect-env.sh: jq not installed; blocking file edits until it is" >&2; exit 2; }

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
NAME=$(basename -- "$FILE" 2>/dev/null)

case "$NAME" in
  .env.example|.env.sample|.env.template) exit 0 ;;
  .env|.env.*)
    jq -n --arg f "$FILE" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Editing secrets file \($f) is not allowed; edit .env.example instead")}}'
    exit 0 ;;
esac
exit 0
```

### `.claude/hooks/keep-going.sh`
```bash
#!/bin/bash
# Stop hook: if tests fail, send Claude back to fix them ONCE per stop attempt.
# Fails OPEN (lets Claude stop) on any setup problem, so it can never trap the session.
command -v jq >/dev/null 2>&1 || exit 0
INPUT=$(cat)

# Already continuing because of this hook -> let Claude stop (prevents infinite loop)
[ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -f package.json ] || exit 0

if ! OUT=$(npm test 2>&1); then
  { echo "Tests are failing; fix them before stopping. Last output:"; printf '%s\n' "$OUT" | tail -n 30; } >&2
  exit 2
fi
exit 0
```

Then run: `chmod +x .claude/hooks/*.sh`

## Proof (run from the project root)

Before the fix (your current scripts):
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | .claude/hooks/guard.sh; echo "exit=$?"                       # exit=1  (doesn't block)
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main --force"}}' | .claude/hooks/guard.sh; echo "exit=$?"   # exit=0  (missed)
echo '{"tool_name":"Write","tool_input":{"file_path":".env"}}' | .claude/hooks/protect-env.sh; echo "exit=$?"                 # exit=126 (not executable)
echo '{"stop_hook_active":true}' | .claude/hooks/keep-going.sh; echo "exit=$?"                                                # exit=2  (loops forever)
```

After the fix:
```bash
export CLAUDE_PROJECT_DIR="$PWD"
for c in 'rm -rf /' 'rm -fr ~' 'rm -r -f /' '/bin/rm -rf /' 'sudo rm -Rf /*' 'rm -rf $HOME' 'cd x && rm -rf *' \
         'git push origin main --force' 'git push -f origin main' 'git push origin +main'; do
  jq -nc --arg c "$c" '{tool_name:"Bash",tool_input:{command:$c}}' | .claude/hooks/guard.sh 2>/dev/null; echo "$c -> exit=$?"   # all exit=2
done
for c in 'rm -rf /tmp/build' 'rm -rf node_modules' 'git push --force-with-lease origin main' 'git push origin main'; do
  jq -nc --arg c "$c" '{tool_name:"Bash",tool_input:{command:$c}}' | .claude/hooks/guard.sh; echo "$c -> exit=$?"              # all exit=0
done
echo '{"tool_name":"Write","tool_input":{"file_path":"/p/.env"}}'         | .claude/hooks/protect-env.sh; echo "exit=$?"  # deny JSON, exit=0
echo '{"tool_name":"Write","tool_input":{"file_path":"/p/.env.example"}}' | .claude/hooks/protect-env.sh; echo "exit=$?"  # no output, exit=0
echo '{"stop_hook_active":false}' | .claude/hooks/keep-going.sh; echo "exit=$?"   # exit=2 only if npm test fails
echo '{"stop_hook_active":true}'  | .claude/hooks/keep-going.sh; echo "exit=$?"   # exit=0: Claude is allowed to stop
```
I ran all of these against copies of the scripts and every result matched the comments.

## Check before you use this
- **Behaviour change:** the old rm pattern (if it had ever run) also caught `rm -rf /some/specific/path`. The new one blocks recursive rm only on `/`, `~`, `$HOME`, `.`, `..` and `*`. If you want *every* `rm -rf` blocked, remove the third `grep` condition. The checks look at the whole command line, so `ls -r . ; rm foo` is a (harmless) false positive.
- **Text blocklists can be bypassed:** `bash -c "..."`, `eval`, `python -c 'shutil.rmtree(...)'`, or a script file get past both guards. Likewise, `protect-env.sh` doesn't stop `echo x > .env` via Bash. For real protection, also add `permissions.deny` rules (e.g. `"Edit(./.env)"`, `"Bash(rm -rf:*)"`) and run risky work in a sandbox.
- **The Stop hook now pushes back once per stop:** after one "keep fixing" round, Claude may stop even if the tests still fail. If you want more rounds, keep a retry counter in a temp file keyed by `session_id`, but always cap it.
- **This hook runs for everyone:** `.claude/settings.json` is committed, so these hooks (and `npm test` at every stop) run for every teammate. Put personal preferences in `.claude/settings.local.json`. Also check `~/.claude/settings.json` for duplicate hooks, because all matching hooks from all scopes run. I only had this project folder to look at.
