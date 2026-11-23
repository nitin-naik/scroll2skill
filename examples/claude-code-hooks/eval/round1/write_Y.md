# Two hooks: protect `.env` + `migrations/`, auto-ruff Python edits

**Hook 1:** `PreToolUse`, matcher `Edit|MultiEdit|Write|NotebookEdit|Bash`. It runs before Claude touches a file, and exit 2 cancels the call. It also covers `Bash`, so Claude can't get around it with `echo >> .env` or `sed -i`.
**Hook 2:** `PostToolUse`, matcher `Edit|MultiEdit|Write`. It runs after a successful edit and only on that file. Any lint errors ruff can't fix are sent back to Claude so it fixes them.

Both scripts are Python 3 (stdlib only, so you don't need `jq`). They go in the project so your whole team gets them when you commit.

## 1. Setup

```bash
mkdir -p .claude/hooks
# paste the two scripts below into these files, then:
chmod +x .claude/hooks/protect_files.py .claude/hooks/ruff_after_edit.py
```

## 2. `.claude/settings.json` (project scope; commit it)

If the file already has a `"hooks"` key, add these two event arrays to it. Don't replace your existing entries.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write|NotebookEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect_files.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff_after_edit.py",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## 3. `.claude/hooks/protect_files.py`

```python
#!/usr/bin/env python3
"""PreToolUse guard: block edits to .env files and anything under migrations/.

Fail-closed: if the hook input can't be parsed, the tool call is blocked.
"""
from __future__ import annotations

import json
import os
import re
import sys

# .env, .env.local, .env.production ... but NOT the committed templates.
ALLOWED_ENV_TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist"}


def is_protected(path: str, cwd: str) -> str | None:
    if not path:
        return None
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    path = os.path.normpath(path)
    parts = path.split(os.sep)
    name = parts[-1]
    if (name == ".env" or name.startswith(".env.")) and name not in ALLOWED_ENV_TEMPLATES:
        return f"{name} is an environment/secrets file"
    if "migrations" in parts[:-1]:
        return "files under migrations/ are generated and must not be hand-edited"
    return None


# Bash: block shell commands that WRITE to a protected path (reads like `cat .env` are allowed).
ENV_RE = r"(^|[\s/'\"=])\.env(\.(?!example|sample|template|dist)\w+)?($|[\s'\";|&)])"
MIG_RE = r"(^|[\s/'\"=])migrations/"
WRITE_RE = r"(>|\btee\b|\bsed\s+(-\w*\s+)*-i|\bperl\s+-\w*i|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bdd\b|\bchmod\b|\bln\b|\binstall\b|\bopen\(|write_text|\bpatch\b|\bgit\s+(checkout|restore|apply|rm|mv))"


def bash_hits(cmd: str) -> str | None:
    if not re.search(WRITE_RE, cmd):
        return None
    if re.search(ENV_RE, cmd):
        return "this command looks like it writes to a .env file"
    if re.search(MIG_RE, cmd):
        return "this command looks like it writes under migrations/"
    return None


def block(reason: str) -> None:
    print(
        f"BLOCKED by protect_files hook: {reason}. "
        "Do not modify .env files or anything in migrations/. "
        "If a config value or schema change is needed, tell the user exactly what to change "
        "(for schema changes: edit the models and ask the user to generate the migration).",
        file=sys.stderr,
    )
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except Exception as e:  # fail closed: a guard that can't read its input blocks
    block(f"hook could not parse its input ({e})")

tool = data.get("tool_name", "")
ti = data.get("tool_input") or {}
cwd = data.get("cwd") or os.getcwd()

if tool == "Bash":
    reason = bash_hits(ti.get("command", ""))
else:  # Edit, MultiEdit, Write, NotebookEdit
    reason = is_protected(ti.get("file_path") or ti.get("notebook_path") or "", cwd)

if reason:
    block(reason)
sys.exit(0)
```

What it blocks: `.env` and `.env.*` (for example `.env.local` and `.env.production`), and any file with a `migrations` directory anywhere in its path. It still allows `.env.example`, `.env.sample`, `.env.template` and `.env.dist`, because those are committed templates. If you want those locked too, empty `ALLOWED_ENV_TEMPLATES` and remove the `(?!example|...)` lookahead. It allows reads (`cat .env`) and `python manage.py makemigrations` / `alembic revision`, because those commands don't name the protected path. If you want Claude never to create migrations, add those commands to the Bash check.

## 4. `.claude/hooks/ruff_after_edit.py`

```python
#!/usr/bin/env python3
"""PostToolUse: run `ruff check --fix` then `ruff format` on the Python file Claude just edited.

Lint errors ruff can't auto-fix are fed back to Claude (exit 2) so it fixes them.
Ruff missing or crashing never blocks Claude (exit 1 = warning shown to you only).
"""
import json
import os
import shutil
import subprocess
import sys

try:
    data = json.load(sys.stdin)
except Exception as e:
    print(f"ruff hook: bad input JSON: {e}", file=sys.stderr)
    sys.exit(1)

ti = data.get("tool_input") or {}
path = ti.get("file_path") or ""
if not path.endswith((".py", ".pyi")):
    sys.exit(0)
project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
if not os.path.isabs(path):
    path = os.path.join(project, path)
if not os.path.isfile(path):
    sys.exit(0)

# Prefer the project's own ruff (pinned version), then PATH, then uvx.
venv_ruff = os.path.join(project, ".venv", "bin", "ruff")
if os.access(venv_ruff, os.X_OK):
    ruff = [venv_ruff]
elif shutil.which("ruff"):
    ruff = ["ruff"]
elif shutil.which("uvx"):
    ruff = ["uvx", "ruff"]
else:
    print("ruff hook: ruff not found (.venv/bin, PATH, or uvx); skipping", file=sys.stderr)
    sys.exit(1)

# --force-exclude: honour `exclude` in pyproject/ruff.toml even though we pass a path explicitly.
run = lambda *args: subprocess.run(
    [*ruff, *args, "--force-exclude", path], cwd=project, capture_output=True, text=True
)
check = run("check", "--fix", "--quiet")
fmt = run("format", "--quiet")

if fmt.returncode != 0:  # usually a syntax error; Claude should see it
    print(f"ruff format failed on {path}:\n{fmt.stderr or fmt.stdout}", file=sys.stderr)
    sys.exit(2)
if check.returncode == 1:  # violations remain that --fix couldn't fix
    print(
        f"ruff check found issues it could not auto-fix in {path}. Fix these:\n{check.stdout}",
        file=sys.stderr,
    )
    sys.exit(2)
if check.returncode not in (0, 1):  # ruff itself errored (bad config etc.) - tell the user, don't block
    print(f"ruff check error: {check.stderr}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
```

The order is `check --fix` first, then `format`. That's the order ruff recommends, because some fixes leave code that needs reformatting. Your `pyproject.toml` / `ruff.toml` settings still apply, including `exclude` (because of `--force-exclude`). If you'd rather have it fix silently and never interrupt Claude, change the `sys.exit(2)` under "could not auto-fix" to `sys.exit(0)`.

## 5. Test without starting Claude

Run these from the repo root:

```bash
export CLAUDE_PROJECT_DIR="$PWD"
G=.claude/hooks/protect_files.py

# pass -> exit=0
echo '{"tool_name":"Edit","cwd":"'"$PWD"'","tool_input":{"file_path":"'"$PWD"'/app/models.py"}}' | $G; echo "exit=$?"
echo '{"tool_name":"Bash","cwd":"'"$PWD"'","tool_input":{"command":"cat .env"}}' | $G; echo "exit=$?"

# block -> exit=2 plus a BLOCKED message
echo '{"tool_name":"Write","cwd":"'"$PWD"'","tool_input":{"file_path":"'"$PWD"'/.env"}}' | $G; echo "exit=$?"
echo '{"tool_name":"Edit","cwd":"'"$PWD"'","tool_input":{"file_path":"app/migrations/0001_initial.py"}}' | $G; echo "exit=$?"
echo '{"tool_name":"Bash","cwd":"'"$PWD"'","tool_input":{"command":"echo X=1 >> .env"}}' | $G; echo "exit=$?"

# ruff: make a messy file; expect exit=0 and the file fixed + reformatted
printf 'import os,sys\nx = {  "a":1 }\n' > ruff_hook_demo.py
echo '{"tool_name":"Write","tool_input":{"file_path":"'"$PWD"'/ruff_hook_demo.py"}}' | .claude/hooks/ruff_after_edit.py; echo "exit=$?"
cat ruff_hook_demo.py   # unused imports gone (F401 fix), dict reformatted
# unfixable lint error -> exit=2 with the diagnostic Claude would receive
printf 'print(undefined_name)\n' > ruff_hook_demo.py
echo '{"tool_name":"Write","tool_input":{"file_path":"'"$PWD"'/ruff_hook_demo.py"}}' | .claude/hooks/ruff_after_edit.py; echo "exit=$?"
rm ruff_hook_demo.py
```

I ran all the protect-file cases above (plus `.env.example`, `migrations_helper.py` and bad JSON) and got the expected exit codes. I checked the ruff hook's control flow against a stub `ruff`, but not against the real binary.

## 6. Check it live

- Restart Claude Code in the repo. Hook settings are read at startup. Then run `/hooks`: you should see both entries under PreToolUse and PostToolUse.
- Ask Claude to add a line to `.env`. It should report the block and suggest the change to you instead.
- Ask Claude to write a badly formatted `.py` file, then open it: it will already be formatted. Run `claude --debug` to watch each hook fire and see its exit code.

## Check before you use this

- **Not a security boundary.** The Bash check is a heuristic. `python -c "open('.env','w')"`, building the path from variables, or running a script that writes the file can all get past it. The Edit/Write block is reliable. The Bash block is best-effort. If `.env` holds real secrets, also add `"permissions": {"deny": ["Read(./.env)", "Read(./.env.*)"]}` if you don't want Claude reading them either.
- **ruff has to be findable from the hook.** It looks in `.venv/bin/ruff`, then `PATH`, then `uvx ruff`. If none of those work, it prints a warning and lets the edit through unformatted.
- Requires Python 3.7+ on `PATH` as `python3`. Windows users would need `python …` in `command` (the shebang is ignored there).
- When ruff rewrites a file after an edit, Claude's next `Edit` on that file works against the new contents. Claude Code handles this, but expect an occasional "file changed since read" re-read.
- `MultiEdit` doesn't exist in some Claude Code versions. Leaving it in the matcher is harmless.
