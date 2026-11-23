# Hook audit: `.claude/settings.json` + `.claude/hooks/*`

I found what's behind both symptoms, plus a few other problems. Every fix below was tested by piping real hook-input JSON into the old and new scripts.

## Why the rm guard never blocks

There are three separate reasons, and any one of them is enough to turn the guard off:

1. **The matcher `"bash"` never matches.** Matchers are case-sensitive regexes on the tool name, and the tool is called `Bash`, so `guard.sh` never runs at all.
2. **The rm branch exits 1.** Only **exit 2** blocks. Exit 1 is a non-blocking error: the command runs anyway, and the message goes to stdout, so Claude never sees it. (The force-push branch correctly uses `exit 2` + stderr.)
3. **Relative command path `.claude/hooks/guard.sh`.** This only resolves while the shell's cwd is the project root. After Claude `cd`s anywhere else you get exit 127 ("No such file"), which is also non-blocking. Reproduced: `exit=127`.

Even with those fixed, the regex `rm -rf /` was **leaky**. It missed `rm -fr /`, `rm -r -f /`, `rm -rf ~`, `rm -rf $HOME`, `rm -rf "/"`, `rm -rf .`, `rm --recursive /etc`, and `sudo rm -rf --no-preserve-root /`. It also **over-blocked**: `rm -rf /tmp/foo` matched because every absolute path starts with `/`.

## Why Claude sometimes never stops

`keep-going.sh` (Stop hook) returns exit 2 whenever `npm test` fails, and nothing ever lets it give up:

- **It never checks `stop_hook_active`**, and has no retry cap. If the tests can't be fixed, Claude is sent back forever.
- **`npm test` fails for reasons Claude can't fix**, and all of them were treated as "tests failing": no `package.json` in the current dir (the hook runs in whatever dir Claude last `cd`'d into), the `npm init` placeholder `"Error: no test specified" && exit 1`, or `npm` not on PATH. In each case the old hook returned exit 2 every time (reproduced). A Stop hook should **fail open**.
- Claude only gets the message "Tests are failing". It never sees which test failed, so it can't fix anything on purpose.

The `PostToolUse` hook with matcher `"*"` that runs `npm test` makes this worse. It runs your **whole test suite after every tool call**, including every Read and Grep. Its output isn't shown to Claude, so it can't help, and it can't block anything after the fact. It's pure slowdown, and long runs can hit the default timeout.

## Full findings

| # | Where | Severity | Problem | Fix |
|---|---|---|---|---|
| 1 | settings: `"matcher": "bash"` | BROKEN | Case-sensitive, so it never matches `Bash` | `"Bash"` |
| 2 | settings: `.claude/hooks/guard.sh` | BROKEN | Relative path, so exit 127 after a `cd` | `"$CLAUDE_PROJECT_DIR"/.claude/hooks/guard.sh` |
| 3 | guard.sh rm branch | BROKEN | `exit 1` + stdout doesn't block | `exit 2` + reason on stderr |
| 4 | guard.sh rm regex | LEAKY + OVER-BLOCKS | Misses `-fr`, `-r -f`, `~`, `$HOME`, `.`, quotes, `--recursive`, `--no-preserve-root`; blocks `/tmp/foo` | Parses flags and targets per sub-command |
| 5 | guard.sh force-push regex `--force[^-]` | LEAKY | Misses `--force` at the end of the command (the most common form), `-f`, `-uf`, `+branch` refspecs | Checks each arg after `push` |
| 6 | guard.sh with no `jq` | UNSAFE | `jq: command not found` makes CMD empty, then exit 0, so the guard fails open | Checks for jq and exits 2 if it's missing (fail closed) |
| 7 | protect-env.sh mode `-rw-r--r--` | BROKEN | Not executable: exit 126 (reproduced), non-blocking, so the .env guard is silently off | `chmod +x` |
| 8 | settings: `$CLAUDE_PROJECT_DIR/...` unquoted | BROKEN on paths with spaces | Word-splits | `"$CLAUDE_PROJECT_DIR"/...` |
| 9 | settings: matcher `Edit\|Write` | LEAKY | `MultiEdit` and `NotebookEdit` bypass it | `Edit\|MultiEdit\|Write\|NotebookEdit` (+ read `.tool_input.notebook_path`) |
| 10 | protect-env.sh: JSON deny + `exit 2` | BROKEN (reason lost) | On exit 2 the stdout JSON is ignored and stderr is empty, so Claude is blocked with no reason | JSON `deny` on **exit 0** (built with `jq -n --arg`) |
| 11 | protect-env.sh: two `jq` calls on stdin | BROKEN (latent) | The first `jq` consumes stdin, so `TOOL` is always empty | Read stdin once into `INPUT` |
| 12 | protect-env.sh: `*.env*` glob | OVER-BLOCKS | Blocks `.env.example`, `.envrc`, `dev.env.md` | Match basename `.env` / `.env.*`; allow `.example`, `.sample`, `.template` |
| 13 | keep-going.sh | OVER-BLOCKS (infinite loop) | No `stop_hook_active` / retry cap; unfixable failures cause exit 2 forever | Cap at 3 consecutive retries, fail open when tests can't run, `cd` to project root |
| 14 | keep-going.sh | STYLE | Claude only sees "Tests are failing" | Passes the last 30 lines of `npm test` on stderr |
| 15 | PostToolUse `"*"` -> `npm test` | SLOW | Full test suite after every tool call, output unused | Removed (the Stop hook already covers it) |
| 16 | `.claude/settings.json` is the committed file | Note | These hooks run for every teammate who clones the repo | Fine if intended; personal hooks go in `.claude/settings.local.json` |

## Fixed files

### `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.sh", "timeout": 10 } ] },
      { "matcher": "Edit|MultiEdit|Write|NotebookEdit",
        "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-env.sh", "timeout": 10 } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/keep-going.sh", "timeout": 600 } ] }
    ]
  }
}
```

(If you want a per-edit check back, use a `PostToolUse` hook with matcher `Edit|MultiEdit|Write` that runs a fast linter or formatter on just `.tool_input.file_path`, not the whole test suite.)

### `.claude/hooks/guard.sh`

```bash
#!/bin/bash
# PreToolUse guard for Bash: blocks recursive rm of dangerous targets and git force-push.
# Blocks with exit 2 + reason on stderr. Fails CLOSED if input can't be read.
set -f   # never glob-expand anything taken from the command

INPUT=$(cat)
if ! command -v jq >/dev/null 2>&1; then
  echo "guard.sh: jq not installed, blocking Bash call to be safe (brew install jq)" >&2
  exit 2
fi
if ! CMD=$(jq -r '.tool_input.command // ""' <<<"$INPUT" 2>/dev/null); then
  echo "guard.sh: could not parse hook input, blocking to be safe" >&2
  exit 2
fi

block() { echo "Blocked by guard.sh: $1" >&2; exit 2; }

# Split into simple commands on ; & | ( ) ` and newlines, then check each one.
SEGMENTS=${CMD//[;&|()\`]/$'\n'}
while IFS= read -r seg; do
  seg=${seg//\"/}; seg=${seg//\'/}          # drop quotes: "rm" -rf "/" -> rm -rf /
  read -ra w <<<"$seg"
  n=${#w[@]}

  # ---- rm -------------------------------------------------------------
  for ((i = 0; i < n; i++)); do
    [[ "${w[i]##*/}" == "rm" ]] || continue  # rm, /bin/rm, sudo rm, xargs rm, bash -c "rm ..."
    [[ $i -gt 0 && "${w[i-1]##*/}" == "git" ]] && continue   # git rm is recoverable
    recursive=0; opts_done=0; targets=()
    for ((j = i + 1; j < n; j++)); do
      a=${w[j]}
      if [[ $opts_done == 0 && "$a" == "--" ]]; then opts_done=1; continue; fi
      if [[ $opts_done == 0 && "$a" == --* ]]; then
        [[ "$a" == "--recursive" ]] && recursive=1
        [[ "$a" == "--no-preserve-root" ]] && block "rm --no-preserve-root"
        continue
      fi
      if [[ $opts_done == 0 && "$a" == -?* ]]; then
        [[ "$a" == *[rR]* ]] && recursive=1
        continue
      fi
      targets+=("$a")
    done
    [[ $recursive == 1 ]] || continue
    for t in "${targets[@]}"; do
      norm=$t
      while [[ "$norm" == //* ]]; do norm=${norm#/}; done           # //x -> /x
      while [[ "$norm" == ?*/ ]]; do norm=${norm%/}; done            # x/ -> x (keeps "/")
      case "$norm" in
        /|/.|'/*'|'~'|'~/*'|'$HOME'|'${HOME}'|'$HOME/*'|'${HOME}/*'|.|..|'*'|'./*'|'.*'|'../*')
          block "recursive rm of '$t'" ;;
        /bin|/boot|/dev|/etc|/home|/lib|/lib64|/opt|/private|/proc|/root|/sbin|/sys|/usr|/var|/System|/Library|/Applications|/Users|/Volumes)
          block "recursive rm of system directory '$t'" ;;
      esac
    done
  done

  # ---- git push --force -----------------------------------------------
  git_at=-1; push_at=-1
  for ((i = 0; i < n; i++)); do
    [[ $git_at -lt 0 && "${w[i]##*/}" == "git" ]] && git_at=$i
    [[ $git_at -ge 0 && $push_at -lt 0 && "${w[i]}" == "push" ]] && push_at=$i
  done
  if [[ $push_at -ge 0 ]]; then
    for ((i = push_at + 1; i < n; i++)); do
      a=${w[i]}
      [[ "$a" == "--force" ]] && block "git push --force (use --force-with-lease, or run it yourself)"
      [[ "$a" =~ ^-[a-zA-Z]*f[a-zA-Z]*$ ]] && block "git push $a (force push)"
      [[ "$a" == +?* ]] && block "git push $a (+refspec is a force push)"
    done
  fi
done <<<"$SEGMENTS"

exit 0
```

### `.claude/hooks/protect-env.sh`

```bash
#!/bin/bash
# PreToolUse guard for Edit/MultiEdit/Write/NotebookEdit: deny edits to .env and .env.* files
# (templates like .env.example / .env.sample / .env.template stay editable).
# Denies via JSON on exit 0 so Claude sees the reason. Fails CLOSED if input can't be read.

INPUT=$(cat)                                   # read stdin ONCE
if ! command -v jq >/dev/null 2>&1; then
  echo "protect-env.sh: jq not installed, blocking file edit to be safe (brew install jq)" >&2
  exit 2
fi
if ! FILE=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' <<<"$INPUT" 2>/dev/null); then
  echo "protect-env.sh: could not parse hook input, blocking to be safe" >&2
  exit 2
fi

BASE=${FILE##*/}
case "$BASE" in
  .env.example|.env.sample|.env.template) exit 0 ;;
  .env|.env.*)
    jq -n --arg reason "Editing $BASE is blocked by protect-env.sh (secrets file). Ask the user to change it." \
      '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$reason}}'
    exit 0 ;;
esac
exit 0
```

### `.claude/hooks/keep-going.sh`

```bash
#!/bin/bash
# Stop hook: if the project's tests fail, send Claude back to fix them, at most MAX_RETRIES
# times in a row, then let it stop. Fails OPEN (exit 0) whenever tests can't be run at all,
# so a missing tool or missing test script can never trap Claude in a loop.
MAX_RETRIES=3

INPUT=$(cat)
command -v jq  >/dev/null 2>&1 || exit 0
command -v npm >/dev/null 2>&1 || exit 0

ACTIVE=$(jq -r '.stop_hook_active // false' <<<"$INPUT" 2>/dev/null)
SID=$(jq -r '.session_id // "nosession"' <<<"$INPUT" 2>/dev/null | tr -cd 'A-Za-z0-9_-')
COUNT_FILE="${TMPDIR:-/tmp}/claude-keep-going-${SID:-nosession}"

# Always test the project root, not wherever Claude last cd'd to.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
[ -f package.json ] || exit 0
TEST_SCRIPT=$(jq -r '.scripts.test // ""' package.json 2>/dev/null)
[ -n "$TEST_SCRIPT" ] || exit 0
[[ "$TEST_SCRIPT" == *"no test specified"* ]] && exit 0   # npm init placeholder always fails

# A fresh stop (not caused by this hook) resets the retry counter.
[ "$ACTIVE" = "true" ] || rm -f "$COUNT_FILE"
COUNT=$(cat "$COUNT_FILE" 2>/dev/null); [[ "$COUNT" =~ ^[0-9]+$ ]] || COUNT=0

if [ "$COUNT" -ge "$MAX_RETRIES" ]; then
  rm -f "$COUNT_FILE"
  echo "keep-going.sh: tests still failing after $MAX_RETRIES attempts; letting Claude stop." 
  exit 0
fi

if OUT=$(npm test 2>&1); then
  rm -f "$COUNT_FILE"
  exit 0
fi

echo $((COUNT + 1)) > "$COUNT_FILE"
{
  echo "Tests are failing (attempt $((COUNT + 1))/$MAX_RETRIES). Fix them before stopping. Last 30 lines of npm test:"
  tail -n 30 <<<"$OUT"
} >&2
exit 2
```

Then make all three scripts executable (this is what fixes #7):

```bash
chmod +x .claude/hooks/*.sh
```

Restart Claude Code, or open `/hooks`, so it picks up the new settings.

## What I tested (old -> new exit code; 2 = blocked)

| Input | Old | New |
|---|---|---|
| `rm -rf /` | 1 (not blocked) | **2** |
| `rm -fr /`, `rm -r -f /`, `rm -rf ~`, `rm -rf $HOME`, `rm -rf "/"`, `cd x && rm -rf .`, `rm -Rf /usr`, `rm --recursive --force /etc/`, `sudo rm -rf --no-preserve-root /` | 0 | **2** |
| `rm -rf /tmp/foo` | 1 (false positive) | 0 |
| `rm -rf ./build`, `rm -rf node_modules`, `rm file.txt`, `git rm -r --cached .` | 0 | 0 |
| `git push --force`, `git push origin main --force` | 0 (missed) | **2** |
| `git push -f origin main`, `git push origin +main`, `echo hi; git push -uf origin x` | 0 | **2** |
| `git push --force-with-lease`, `git push origin main` | 0 | 0 |
| guard.sh with `jq` missing, `rm -rf /` | 0 (fail open) | **2** (fail closed) |
| Write `.env`, `.env.local`, `config/.env.production`; NotebookEdit `.env` | blocked, no reason shown | deny JSON with reason |
| Write `.env.example`, `src/.envrc`, `notes/dev.env.md` | blocked (false positive) | allowed |
| Stop, tests failing, 4 stops in a row | 2, 2, 2, 2... forever | 2, 2, 2, then **0** (Claude stops) |
| Stop, no `package.json` / `npm` missing / placeholder test script | 2 forever | **0** |
| Stop, tests pass | 0 | 0 |

## Caveats

- A regex or parser guard on Bash is a speed bump, not a sandbox. `bash -c "$(echo cm0gLXJmIC8= | base64 -d)"`, a script file, or a variable like `T=/; rm -rf $T` will still get past it. For hard guarantees, add `permissions.deny` rules (for example `"Bash(rm -rf /*)"`, `"Bash(git push --force*)"`) alongside the hook, and run risky sessions in a container.
- `keep-going.sh` keeps its retry counter in `$TMPDIR/claude-keep-going-<session_id>`. Change `MAX_RETRIES` at the top of the file if 3 is too few or too many.
- The guard blocks on targets it can see in the command text. It allows recursive deletes of ordinary paths (`/tmp/x`, `./build`, `/Users/you/proj/dist`) on purpose, so normal cleanup still works.
