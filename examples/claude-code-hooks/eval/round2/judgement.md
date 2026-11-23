# Blind judgement (scores: correctness / coverage / actionability / focus)

## Task "write"
| | Corr | Cov | Act | Focus | Total |
|---|---|---|---|---|---|
| X | 9 | 8 | 9 | 9 | 35 |
| Y | 9 | 10 | 9 | 6 | 34 |
Winner: X (narrow).
- I ran both. Both guards block .env/.env.*/migrations/ with exit 2 and allow models.py and my_migrations/. Both ruff hooks fix, then format, and exit 2 on unfixable lint (F821). I checked this with real ruff.
- X is tight and correct. It blocks .env.example by default but says how to allow it, and it points out the Bash gap and adds deny rules.
- Y adds a Bash write guard (it catches `echo >> .env`, `sed -i`, `rm -rf app/migrations`), fail-closed parsing, a uvx fallback and --force-exclude. That is real coverage beyond what was asked, but it is about 2.5x longer, with a lot of caveats and test text. Y also lets `prod.env` through (a design choice). No factual errors in either.

## Task "audit"
| | Corr | Cov | Act | Focus | Total |
|---|---|---|---|---|---|
| X | 9 | 8 | 9 | 8 | 34 |
| Y | 9 | 10 | 9 | 7 | 35 |
Winner: Y (narrow).
- Both find the core bugs: `bash` vs `Bash`, rm exit 1 to stdout, relative path, missing stop_hook_active, protect-env.sh at mode 644, JSON+exit 2 ignored, jq reading stdin twice, `*.env*` over-match, PostToolUse `*` running npm test. They also give correct fixes (JSON deny on exit 0, stderr on exit 2).
- Y also covers NotebookEdit, fails closed when jq is missing, fails open in the Stop hook when npm/package.json/the test script is missing, and caps retries at 3. In my tests: retries go 2,2,2,0; `-uf` and `+main` force pushes are blocked; `rm -rf /tmp/foo` and node_modules are allowed.
- Y has one flaw: it strips quotes, so `echo "rm -rf /"` and `git commit -m "rm -rf / fix"` get blocked (false positives). Its guard is also long, about 75 lines.
- X's guard blocks every rm -rf, node_modules included (it says so). It misses `git push -uf` and `+refspec`. Its Stop fix allows only one retry, which is correct but blunt.
