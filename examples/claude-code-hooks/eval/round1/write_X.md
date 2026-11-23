# Two Claude Code hooks for your Python repo

You need three files, all in the repo so they can be committed and shared:

```
.claude/settings.json
.claude/hooks/protect-files.sh
.claude/hooks/ruff-fix.sh
```

Requirements: `jq` on PATH (`brew install jq` / `apt install jq`), and `ruff` either in the project venv (`.venv/bin/ruff`) or on PATH.

---

## 1. `.claude/settings.json`

If you already have this file, merge the `"hooks"` key into it rather than replacing the file.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff-fix.sh", "timeout": 60 }
        ]
      }
    ]
  }
}
```

Notes:
- Matchers are case-sensitive regexes against tool names (`Edit`, not `edit`).
- `"$CLAUDE_PROJECT_DIR"` (quoted) makes the path work no matter what directory Claude has `cd`'d into, and survives spaces in the path.

---

## 2. `.claude/hooks/protect-files.sh` — block `.env*` and `migrations/`

```bash
#!/usr/bin/env bash
# PreToolUse: block edits to .env files and anything under migrations/
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$FILE" ] && exit 0
NAME=$(basename -- "$FILE")

reason=""
case "$NAME" in
  .env|.env.*|*.env) reason="$FILE is an env file (secrets)" ;;
esac
case "/$FILE/" in
  */migrations/*) reason="$FILE is under migrations/ (generate migrations with the framework, don't hand-edit)" ;;
esac

if [ -n "$reason" ]; then
  echo "Blocked by protect-files hook: $reason. Ask the user to make this change." >&2
  exit 2
fi
exit 0
```

How it works: on **exit code 2** Claude Code cancels the tool call and shows the stderr text to Claude, which then knows why and stops trying. (Exit 1 or any other code would only log a warning and the edit would go through.)

What it matches (tested):

| Path | Result |
|---|---|
| `.env`, `.env.local`, `.env.production`, `prod.env` | blocked |
| `app/migrations/0001_initial.py`, `migrations/env.py` (Alembic) | blocked |
| `app/models.py`, `environment.py`, `my_migrations/x.py` | allowed |

If you want Claude to be able to edit committed templates like `.env.example`, add this line as the first case inside the first `case`:

```bash
  .env.example|.env.sample|.env.template) ;;
```

---

## 3. `.claude/hooks/ruff-fix.sh` — auto-format and lint-fix edited Python files

```bash
#!/usr/bin/env bash
# PostToolUse: ruff check --fix + ruff format on any Python file Claude edited
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
case "$FILE" in
  *.py|*.pyi) ;;
  *) exit 0 ;;
esac
[ -f "$FILE" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0   # so ruff picks up pyproject.toml / ruff.toml

# Prefer the project's venv ruff, then whatever is on PATH
if   [ -x .venv/bin/ruff ];           then RUFF=.venv/bin/ruff
elif command -v ruff >/dev/null 2>&1; then RUFF=ruff
else echo "ruff-fix hook: ruff not found (.venv/bin/ruff or PATH); skipped $FILE" >&2; exit 0; fi

# Fix first, then format (fixes can leave code unformatted)
OUT=$("$RUFF" check --fix --quiet "$FILE" 2>&1); STATUS=$?
"$RUFF" format --quiet "$FILE" >/dev/null 2>&1

if [ $STATUS -ne 0 ]; then
  # Lint errors ruff could not auto-fix: exit 2 feeds them back to Claude to fix
  { echo "ruff check: unfixable issues remain in $FILE:"; printf '%s\n' "$OUT"; } >&2
  exit 2
fi
exit 0
```

Behaviour:
- Non-Python files are ignored instantly.
- Uses your project's ruff config (it runs from the project root).
- If ruff fixes everything, it stays silent. If lint errors remain that ruff can't auto-fix (for example `F821 undefined name`), the hook exits 2, and the edit has already happened, so this doesn't undo it. It just shows Claude the ruff output so it fixes them on its next step.
- Don't want Claude nagged about unfixable lint? Change the final `exit 2` to `exit 0`.
- Claude sees that the file changed on disk after formatting, so it re-reads it before its next edit. That's expected.

---

## 4. Make them executable and check them

```bash
chmod +x .claude/hooks/protect-files.sh .claude/hooks/ruff-fix.sh

# should print the "Blocked..." message and exit 2
echo '{"tool_name":"Edit","tool_input":{"file_path":"app/migrations/0002_x.py"}}' \
  | .claude/hooks/protect-files.sh; echo "exit=$?"

# should print nothing and exit 0
echo '{"tool_name":"Edit","tool_input":{"file_path":"app/models.py"}}' \
  | .claude/hooks/protect-files.sh; echo "exit=$?"
```

Then restart Claude Code (or open `/hooks` to confirm they're loaded) and ask it to edit `.env`. It should be refused.

The missing executable bit is the most common reason a hook "does nothing". Claude Code logs a permission error and carries on.

---

## Optional: belt and braces with permissions

Hooks only see the Edit/Write tools. Claude could still change `.env` through Bash (`echo X >> .env`, `sed -i`). To close that gap too, add deny rules in the same `settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Edit(./.env)", "Edit(./.env.*)", "Edit(**/migrations/**)",
      "Read(./.env)", "Read(./.env.*)"
    ]
  }
}
```

(Drop the `Read(...)` rules if you're fine with Claude *reading* env files.) Even with these, a determined shell command can get around them. Hooks and deny rules are guardrails, not a sandbox.
