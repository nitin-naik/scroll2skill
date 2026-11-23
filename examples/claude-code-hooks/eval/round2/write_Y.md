# Two Claude Code hooks for your Python repo

**What you get**

1. **PreToolUse**, matcher `Edit|MultiEdit|Write|NotebookEdit|Bash`, runs `protect_files.py`. It blocks any edit to `.env` / `.env.*` and anything under a `migrations/` directory before the edit happens. The Bash check catches shell writes like `echo X >> .env`, `sed -i ... migrations/...` and `rm -rf app/migrations`.
2. **PostToolUse**, matcher `Edit|MultiEdit|Write`, runs `ruff_after_edit.py`. After Claude edits a `.py`/`.pyi` file, it runs `ruff check --fix` and then `ruff format` on that one file. Any lint errors ruff can't fix go back to Claude so it fixes them.

A `permissions.deny` rule backs up the guard. The hook adds the explanation and the smarter matching, and the deny rule still holds if the hook can't run.

Defaults I chose (change them if they're wrong for you):
- `.env.example`, `.env.sample` and `.env.template` **can** be edited. That's where Claude should put new settings.
- Claude **can** still read `.env` and migrations, and it can still run `makemigrations` / `alembic revision` through Bash. Generated migrations aren't hand edits.
- Ruff runs `check --fix` **before** `format`. You asked for format then check, but fixes such as removing an import can leave code that needs reformatting, so formatting last gives a clean file.

---

## 1. Settings: `.claude/settings.json` (in the repo root, committed, so the whole team gets it)

If you only want this for yourself, put it in `.claude/settings.local.json` instead. **If the file already has a `hooks` or `permissions` key, merge these entries in. Don't replace what's there.**

```json
{
  "permissions": {
    "deny": [
      "Edit(**/.env)",
      "Edit(**/migrations/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write|NotebookEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect_files.py",
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
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff_after_edit.py",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

The command calls `python3` explicitly. If a hook script lost its execute bit, Claude Code would treat the failure (exit 126) as non-blocking, so the guard would quietly let edits through. Calling `python3` directly avoids that.

---

## 2. `.claude/hooks/protect_files.py`

```python
#!/usr/bin/env python3
"""PreToolUse guard: block Claude from editing .env files or anything under migrations/.

Fail policy: fails CLOSED. If the hook input can't be parsed, the tool call is blocked.
Allowed on purpose: .env.example / .env.sample / .env.template, reading protected files,
and tool-generated migrations (makemigrations, alembic revision) run via Bash.
"""
import json
import os
import re
import shlex
import sys

ALLOWED_ENV = {".env.example", ".env.sample", ".env.template"}

# Commands whose (non-flag) arguments may be written, moved or deleted.
WRITE_CMDS = {
    "rm", "mv", "cp", "tee", "truncate", "touch", "ln", "chmod", "chown",
    "dd", "install", "rsync", "unlink", "shred",
}
INPLACE_CMDS = {"sed", "gsed", "perl"}  # only when called with -i / --in-place
PREFIXES = {"sudo", "command", "env", "nohup", "time"}

ENV_MSG = (
    "Blocked: {rel} is a secrets/environment file and must not be edited by Claude. "
    "If a new setting is needed, add it to .env.example with a placeholder value "
    "and tell the user which value to set in their own .env."
)
MIG_MSG = (
    "Blocked: {rel} is under migrations/ and must not be hand-edited. "
    "Change the models instead, then ask the user to generate the migration "
    "(e.g. `python manage.py makemigrations` or `alembic revision --autogenerate`)."
)


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def check_path(path, base, project):
    """Return a block message if path is protected, else None."""
    if not path:
        return None
    path = path.strip("'\"")
    if path.startswith("of="):  # dd of=FILE
        path = path[3:]
    full = os.path.normpath(os.path.join(base, os.path.expanduser(path)))
    rel = os.path.relpath(full, project)
    parts = rel.replace("\\", "/").split("/")
    name = parts[-1]
    if (name == ".env" or name.startswith(".env.")) and name not in ALLOWED_ENV:
        return ENV_MSG.format(rel=rel)
    if "migrations" in parts:  # whole path segment (the dir or anything in it), not migrations_helper.py
        return MIG_MSG.format(rel=rel)
    return None


def bash_write_targets(cmd):
    """Best-effort list of paths a shell command may write to."""
    targets = []
    # Redirections: >, >>, 2>, &>, >|
    for m in re.finditer(r"(?:\d|&)?>>?\|?\s*([^\s;&|<>()]+)", cmd):
        targets.append(m.group(1))
    for seg in re.split(r"&&|\|\||[;|\n]", cmd):
        try:
            toks = shlex.split(seg)
        except ValueError:
            toks = seg.split()
        # skip VAR=value assignments and wrappers like sudo/env
        while toks and (re.match(r"^\w+=", toks[0]) or toks[0] in PREFIXES):
            toks = toks[1:]
        if not toks:
            continue
        prog = os.path.basename(toks[0])
        args = [t for t in toks[1:] if not t.startswith("-")]
        if prog in WRITE_CMDS:
            targets += args
        elif prog in INPLACE_CMDS and any(
            re.match(r"^(-[A-Za-z]*i|--in-place)", t) for t in toks[1:]
        ):
            targets += args
    return targets


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:  # fail closed
        block(f"protect_files hook could not parse its input ({e}); blocking to be safe.")

    project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}

    if tool == "Bash":
        base = data.get("cwd") or project  # relative paths in commands resolve from the shell cwd
        paths = bash_write_targets(tool_input.get("command", ""))
    else:
        base = project
        paths = [tool_input.get("file_path") or tool_input.get("notebook_path")]

    for p in paths:
        msg = check_path(p, base, project)
        if msg:
            block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

The path check matches whole path segments. That means `app/migrations/0002.py` and `rm -rf app/migrations` are blocked, but `migrations_helper.py` isn't. Exit 2 sends the "do this instead" message to Claude, so it changes course instead of retrying.

---

## 3. `.claude/hooks/ruff_after_edit.py`

```python
#!/usr/bin/env python3
"""PostToolUse: run `ruff check --fix` then `ruff format` on the Python file Claude just edited.

Fail policy: fails OPEN. If ruff is missing, misconfigured or crashes, the edit stands
and nothing is sent to Claude. Only lint errors ruff could NOT auto-fix go back to
Claude (exit 2) so it fixes them; pure formatting changes exit 0 silently.
"""
import json
import os
import shutil
import subprocess
import sys


def find_ruff(project):
    for venv in (".venv", "venv"):
        cand = os.path.join(project, venv, "bin", "ruff")
        if os.access(cand, os.X_OK):
            return [cand]
    if shutil.which("ruff"):
        return [shutil.which("ruff")]
    if shutil.which("uvx"):
        return ["uvx", "ruff"]
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith((".py", ".pyi")) or not os.path.isfile(path):
        sys.exit(0)

    project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    ruff = find_ruff(project)
    if not ruff:
        print("ruff hook: ruff not found in .venv, PATH or via uvx; skipped.", file=sys.stderr)
        sys.exit(0)

    def run(*args):
        try:
            return subprocess.run(
                ruff + list(args), cwd=project, capture_output=True, text=True, timeout=25
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            print(f"ruff hook: {e}; skipped.", file=sys.stderr)
            sys.exit(0)

    # --force-exclude: respect the project's exclude settings even for explicit paths.
    run("check", "--fix", "--force-exclude", "--quiet", path)
    run("format", "--force-exclude", "--quiet", path)
    res = run("check", "--force-exclude", "--output-format", "concise", path)

    if res.returncode == 1:  # violations remain that --fix couldn't handle
        lines = (res.stdout + res.stderr).strip().splitlines()[:40]
        print(
            f"ruff auto-fixed and formatted {path}, but these lint errors remain. Fix them:\n"
            + "\n".join(lines),
            file=sys.stderr,
        )
        sys.exit(2)
    if res.returncode >= 2:  # ruff itself errored (bad config etc.): tell the user, don't block
        print("ruff hook: ruff error:\n" + res.stderr.strip()[:2000], file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

The script looks for ruff in this order: `.venv/bin/ruff`, then `ruff` on PATH, then `uvx ruff`, so it uses your project's pinned ruff when there is one. `--force-exclude` makes ruff honour the `exclude` settings in `pyproject.toml`, even though the hook passes it an explicit file path. Ruff reads your existing `[tool.ruff]` config as usual.

---

## 4. Setup

From the repo root:

```bash
mkdir -p .claude/hooks
# save the two scripts above into .claude/hooks/, then:
chmod +x .claude/hooks/protect_files.py .claude/hooks/ruff_after_edit.py
```

Restart Claude Code after you add or change the settings, because hooks load when a session starts.

---

## 5. Test without Claude

Run these from the repo root:

```bash
export CLAUDE_PROJECT_DIR="$PWD"
G=.claude/hooks/protect_files.py

# Should BLOCK (exit=2, message on stderr)
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/.env\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$PWD/.env.production\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/app/migrations/0001_initial.py\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Bash\",\"cwd\":\"$PWD\",\"tool_input\":{\"command\":\"echo SECRET=1 >> .env\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Bash\",\"cwd\":\"$PWD\",\"tool_input\":{\"command\":\"rm -rf app/migrations\"}}" | python3 $G; echo "exit=$?"
echo 'not json' | python3 $G; echo "exit=$?"      # fails closed

# Should ALLOW (exit=0)
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/.env.example\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/app/migrations_helper.py\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Bash\",\"cwd\":\"$PWD\",\"tool_input\":{\"command\":\"cat .env | grep DB\"}}" | python3 $G; echo "exit=$?"
echo "{\"tool_name\":\"Bash\",\"cwd\":\"$PWD\",\"tool_input\":{\"command\":\"python manage.py makemigrations\"}}" | python3 $G; echo "exit=$?"
```

```bash
R=.claude/hooks/ruff_after_edit.py

# Fixable only: unused import removed, x=1 reformatted, exit=0
printf 'import os\nx=1\n' > _hook_test.py
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/_hook_test.py\"}}" | python3 $R; echo "exit=$?"; cat _hook_test.py

# Not auto-fixable (undefined name): exit=2, F821 listed on stderr
printf 'print(undefined_name)\n' > _hook_test.py
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/_hook_test.py\"}}" | python3 $R; echo "exit=$?"

# Non-Python file: skipped, exit=0
echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$PWD/README.md\"}}" | python3 $R; echo "exit=$?"

rm -f _hook_test.py
```

I ran every guard case above, including the fail-closed case, and they returned the expected exit codes. I also ran the ruff hook's skip cases: non-Python file, deleted file, and ruff not installed. I didn't have ruff available, so the two cases that need ruff are untested. Run them once yourself.

## 6. Live check

- In Claude Code, run `/hooks`. Both entries should be listed under PreToolUse and PostToolUse.
- Ask Claude to "add FOO=1 to .env". It should be blocked and offer to update `.env.example` instead.
- Ask Claude to edit a `.py` file badly formatted. The file should come back formatted.
- If something doesn't fire, start Claude Code with `claude --debug` to see each hook run, its exit code and its output.

---

## Check before you use this

- **The Bash check is best-effort.** `python -c "open('.env','w')"`, `bash -c '...'`, `git checkout -- migrations/` or `rm -rf app` (the parent folder) all get past it. The Edit/Write guard and the `permissions.deny` rules are the real protection.
- **It blocks some harmless commands.** `cp .env .env.bak` and `mv` out of `migrations/` are blocked, because the hook can't tell a source path from a destination.
- **The deny rules are narrower than the hook.** They cover `.env` and `migrations/**`. `.env.local`, `.env.production` and the like are covered by the hook only. Add more `Edit(**/.env.local)` lines if you want two layers for those too.
- **The file changes after Claude writes it.** Ruff rewrites the file after each edit, so it no longer matches what Claude wrote. Claude re-reads the file before its next edit, so this is normally fine.
- **The `uvx` fallback can be slow once.** If ruff isn't in `.venv` or on PATH, the first run downloads it and can take a while. The hook gives up after 25 s per step without blocking anything.
- **Paths assume macOS/Linux.** On Windows, change `.venv/bin/ruff` to `.venv\Scripts\ruff.exe`.
- **One question for you:** should Claude also be prevented from *reading* `.env`, to keep secrets out of the chat? If yes, add `"Read(**/.env)"` to `permissions.deny`, plus a line for each real secrets file such as `"Read(**/.env.local)"`. Don't use `.env.*`, because that would also stop Claude reading `.env.example`.
