# Friction log: writing-claude-code-hooks (draft1) on "protect .env + migrations/, auto-ruff"

## Friction items (ambiguous / contradictory / missing / guessed)

1. "Require `jq` explicitly (...) or write the script in Python."
   The skill doesn't say when to pick each one. For a Python repo I guessed Python: python3 is guaranteed there and jq may not be. Suggest: "Python repo or no jq → Python; otherwise bash+jq".

2. "Matchers: ... `Edit|MultiEdit|Write`"
   It never mentions `NotebookEdit` (it uses `notebook_path`, not `file_path`). A file guard that leaves it out can be bypassed through .ipynb edits. Low impact here, but I guessed and added it.

3. "also block the file path with an Edit/Write matcher when protecting files"
   This line reads backwards for a file-protection request. The main mechanism is Edit/Write, and Bash is the addition. The skill doesn't say whether to add a Bash check at all, or how to separate reads from writes. I guessed: add Bash, block only write-ish commands that name the path, and allow `cat .env`.

4. "decide fail-open vs fail-closed explicitly and say which"
   It doesn't say which one is the default for a file guard. I guessed fail-closed for the guard, and fail-open (exit 1) for the formatter.

5. "PostToolUse formatters: ... never exit 2 on formatter failure unless you want Claude to fix it."
   It doesn't separate formatting from linting. `ruff check --fix` can leave violations that aren't failures but that Claude *should* fix. I guessed exit 2 for leftover lint violations and for format failure (usually a syntax error), and exit 1 when ruff itself is missing or broken. That's a real design decision the skill leaves open.

6. "exit 2 / `decision:"block"` feeds stderr/reason back to Claude" (PostToolUse row)
   It doesn't say whether to use exit 2+stderr or JSON `decision:block` for PostToolUse, or how they differ in what the user sees. I guessed exit 2 for consistency with the guard.

7. "Pick the scope" lists three files but gives no default rule.
   "Python repo" plus "for my repo" suggests project scope. I guessed `.claude/settings.json` (committed). The skill could say: "repo-specific policy → project settings.json".

8. "Write the settings entry with the command path quoted."
   For a Python script it doesn't say whether to call it as `python3 "<path>"` or rely on the shebang plus chmod. I guessed shebang+chmod, following the example. There's no Windows note.

9. "Merge into existing `hooks` keys"
   It gives no guidance on *how to tell the user* to merge when you can't see their file. I guessed one sentence of instruction plus the full standalone block.

10. "timeout is seconds (default 60)"
    No recommended value for formatters. Is `uvx` first-run download time a concern? I guessed 10s for the guard and 60s for ruff.

11. Output format step 5: "`echo '<sample JSON>' | path/to/script`"
    The sample JSON fields needed per tool aren't given (for example, whether `cwd` is needed and whether `file_path` is absolute). I guessed that `file_path` is absolute in practice and handled relative paths anyway.

12. "Settings edits made outside Claude Code may need review in `/hooks` or a restart ... *(current behaviour: snapshot at startup)*"
    Hedged twice and contradictory ("may need review" vs. "snapshot"). I guessed "restart, then confirm in /hooks".

13. "`MultiEdit` tool name" listed as date-sensitive
    It doesn't say whether to keep it in matchers. I guessed keep it (harmless) and noted that.

14. Output format item 7: "At most one short 'check before you use this' list"
    This conflicts with the need to explain design choices (the `.env.example` allowance, the exit-2-on-lint choice, ruff discovery). I put those explanations under each script, outside the list. Not clear that's allowed.

15. "Hooks cost zero context unless they print output that gets fed back."
    True, but there's no guidance on capping how much is fed back. ruff output on a big file could be long. I didn't cap it (a guess).

## Coverage gaps (what a complete answer needed that the skill never asked for)

1. **Path matching semantics**: absolute vs. relative `file_path`, normalizing `..`, matching a `migrations` *path component* rather than a substring (`migrations_helper.py`), and `.env` variants (`.env.local`) vs. templates (`.env.example`). This is the core correctness of any file guard, and the skill has none of it.
2. **Tool-specific path fields**: `file_path` vs. `notebook_path`. There's no table of the `tool_input` shape per tool.
3. **Locating the tool binary from a hook**: the hook PATH often lacks the venv. You need a project `.venv/bin` → PATH → `uvx` fallback. Not mentioned.
4. **Formatter honoring project config/excludes**: you need `ruff --force-exclude` (or the equivalent for other tools) when you pass an explicit path. Not mentioned.
5. **Formatter ordering** when more than one tool runs (ruff recommends `check --fix` before `format`). Not mentioned.
6. **File-changed-under-Claude effect**: a PostToolUse rewrite makes Claude's in-memory view stale. Not mentioned.
7. **Complementary `permissions.deny`** (for example `Read(./.env)`) as a second layer for secret files. The skill's "When a hook is the right tool" section skips permissions rules entirely, though they are the native way to deny Edit/Read on paths.
8. **Legitimate generators**: should `makemigrations` / `alembic revision` be allowed? Any "never touch X" guard should ask whether tool-generated writes count. The skill has no prompt for that.
9. **Python version floor** for Python hook scripts (type syntax `str | None` needs 3.10, or a `__future__` import).
10. **Multiple hooks in one answer**: the output format assumes one event and one script. There's no guidance for two events in one merged settings block, or whether to use one script or two (it says "one script per concern" but not how to lay out the answer).
11. **Steering message for file guards**: the examples are all command-based (bun, force-with-lease). There's no example of what to tell Claude to do instead when a *file* is protected (for example, "edit models and ask the user to generate the migration").
12. **Cleanup in test commands**: tests that create files (the formatter demo) need cleanup steps. Not asked for.

Totals: 15 friction items, 12 coverage gaps.
