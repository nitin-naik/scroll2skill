# Hook review: `.claude/` in audit-fixture

## Why the rm guard never blocks

Three separate bugs stack up. Fixing only one of them wouldn't be enough.

1. **The matcher is `"bash"`, but the tool is called `Bash`.** Matchers are case-sensitive, so `guard.sh` never runs at all. This is the main cause.
2. **The rm branch exits 1 and prints to stdout.** Only **exit 2** blocks a PreToolUse call, and the reason has to go to **stderr**. Exit 1 is a "non-blocking error": the command runs anyway. (The force-push branch got this right.)
3. **The pattern is too narrow.** `rm -rf /` as a literal substring misses `rm -fr /`, `rm -rf ~`, `rm -r -f x`, `rm --recursive --force`, `sudo rm -Rf`.

A smaller one: the command is the relative path `.claude/hooks/guard.sh`, which breaks as soon as Claude `cd`s into a subdirectory. Use `"$CLAUDE_PROJECT_DIR"/...`.

Also in guard.sh: `git push.*--force[^-]` needs a character *after* `--force`, so a plain `git push --force` (end of string) and `git push -f` both get through. I confirmed this by piping test inputs into your script: `rm -fr /`, `rm -rf ~`, `git push --force` and `git push -f` all exited 0, and `rm -rf /` exited 1 (not blocked).

## Why Claude sometimes never stops

`keep-going.sh` (Stop hook) exits 2 whenever `npm test` fails. Exit 2 on Stop means "don't stop, keep working". If Claude can't make the tests pass (flaky test, broken env, test needs a service that's down), every attempt to stop is refused again, **forever**.

It also:
- never reads stdin, so it can't check **`stop_hook_active`**. That field is `true` when Claude is already continuing because of a Stop hook, and it exists precisely to break this loop.
- throws away the test output (`>/dev/null 2>&1`), so Claude is told "tests are failing" but not *which* tests, which makes the loop more likely.
- has no `timeout`, and runs from whatever the current directory is.

## Other problems found

| File | Problem | Effect |
|---|---|---|
| `hooks/protect-env.sh` | **Not executable** (mode 644; the other two are 755) | Hook fails with "permission denied", which is non-blocking, so **.env edits are never blocked** either |
| `hooks/protect-env.sh` | Calls `jq` on stdin twice; the first call consumes it all | `TOOL` is always empty (unused, but a latent bug) |
| `hooks/protect-env.sh` | Prints the JSON `deny` decision **and** exits 2 | Claude Code only parses JSON on exit 0. With exit 2 it uses stderr (empty here), so the block works but Claude gets no reason. Pick one: JSON + exit 0, or stderr + exit 2 |
| `hooks/protect-env.sh` | `*.env*` glob on the full path | Over-matches (`my.environment.py`, `.env.example`, `config.env.d/...`) |
| `settings.json` | `Edit\|Write` matcher | Skips `MultiEdit` |
| `settings.json` | `$CLAUDE_PROJECT_DIR` unquoted for protect-env | Breaks on paths with spaces |
| `settings.json` | **PostToolUse `"*"` → `npm test`** | Runs the full test suite after *every* tool call, including every Read, Grep, Glob and ls. Very slow, uses up the default 60s timeout, and its output/exit code does nothing useful (a failing `npm test` exits 1, which is non-blocking). The Stop hook already runs the tests at the end, so I removed this. If you want per-edit feedback, scope it to `"Edit\|Write\|MultiEdit"` and run a fast targeted test command instead |

## Fixed files

Drop these in to replace the existing files, then run `chmod +x .claude/hooks/*.sh` (that also fixes protect-env.sh), and restart Claude Code or check `/hooks`.

### `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.sh" }
        ]
      },
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-env.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/keep-going.sh", "timeout": 300 }
        ]
      }
    ]
  }
}
```

### `.claude/hooks/guard.sh`

```bash
#!/usr/bin/env bash
# PreToolUse guard for Bash: block recursive-force rm and force pushes.
# Exit 2 + message on stderr = block the call and tell Claude why.
CMD=$(jq -r '.tool_input.command // empty')

# Split on ; & | and check every "rm ..." segment for both a recursive and a force flag.
while IFS= read -r seg; do
  set -f; set -- $seg; set +f
  [ "$1" = "sudo" ] && shift
  [ "$1" = "rm" ] || continue
  shift; r=0; f=0
  for a in "$@"; do
    case "$a" in
      --recursive) r=1 ;; --force) f=1 ;;
      --*) ;;
      -*) [[ $a == *[rR]* ]] && r=1; [[ $a == *f* ]] && f=1 ;;
    esac
  done
  if [ $r = 1 ] && [ $f = 1 ]; then
    echo "Blocked: recursive force rm ('$seg'). Delete specific paths without -rf, or ask the user to run it." >&2
    exit 2
  fi
done < <(printf '%s\n' "$CMD" | tr ';&|' '\n\n\n')

# git push --force / -f  (--force-with-lease is allowed)
if printf '%s' "$CMD" | grep -qE 'git[[:space:]]+push.*[[:space:]](--force|-f)([[:space:]]|$)'; then
  echo "Blocked: force push. Use --force-with-lease or ask the user." >&2
  exit 2
fi
exit 0
```

### `.claude/hooks/protect-env.sh`

```bash
#!/usr/bin/env bash
# PreToolUse guard for Edit/Write/MultiEdit: never touch .env files.
INPUT=$(cat)                                   # read stdin ONCE
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
NAME=$(basename -- "$FILE")
case "$NAME" in
  .env.example|.env.sample|.env.template) exit 0 ;;   # allow committed templates
  .env|.env.*|*.env)
    # JSON decisions are only read on exit 0
    jq -n --arg f "$FILE" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("Editing env files is not allowed: " + $f)}}'
    exit 0 ;;
esac
exit 0
```

### `.claude/hooks/keep-going.sh`

```bash
#!/usr/bin/env bash
# Stop hook: if tests fail, send Claude back once to fix them - but never loop forever.
INPUT=$(cat)
# If Claude is already continuing because of this hook, let it stop.
if [ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
if ! OUT=$(npm test 2>&1); then
  { echo "Tests are failing. Fix them before finishing:"; printf '%s\n' "$OUT" | tail -n 40; } >&2
  exit 2
fi
exit 0
```

With `stop_hook_active`, Claude gets **one** extra round to fix failing tests (with the last 40 lines of test output). If they still fail, it's allowed to stop and report back to you instead of looping.

## Verification

I ran these against a copy of the hooks (your folder was not modified) by piping hook JSON into each script:

| Input | Before | After |
|---|---|---|
| `rm -rf /` | exit 1 (not blocked), and the hook never ran anyway because of the matcher | **exit 2, blocked** |
| `rm -fr build`, `rm -r -f x`, `rm --recursive --force x`, `ls && rm -Rf x`, `sudo rm -rf /`, `rm -rf ~` | allowed | **blocked** |
| `rm file.txt`, `rm -r dir`, `rm *.log`, `grep -rf pat file`, `echo "rm -rf"` | allowed | allowed |
| `git push --force`, `git push -f origin main` | allowed | **blocked** |
| `git push --force-with-lease`, `git push origin main` | allowed | allowed |
| Edit `.env`, `.env.local`, `prod.env` | (hook not executable) | **deny with reason** |
| Edit `.env.example`, `environment.py`, `settings.py` | – | allowed |
| Stop with `stop_hook_active: true` | exit 2 again → loop | **exit 0, stops** |

`settings.json` validated with `jq`.

## Notes

- The new guard blocks **any** recursive-force `rm` (e.g. `rm -rf node_modules`), not just `/`. That matches what your original regex was trying to do (`rm -rf /tmp/x` contained `rm -rf /`). If that's too strict, add an allowlist check before the `exit 2` (for example, allow when every path is under `./build` or `./node_modules`).
- Hooks are a guardrail, not a sandbox. `bash -c "$(echo cm0gLXJmIC8= | base64 -d)"` will get past any regex. For hard guarantees, also add `permissions.deny` rules such as `"Bash(rm -rf:*)"` and `"Edit(./.env)"`, and run risky sessions in a container.
