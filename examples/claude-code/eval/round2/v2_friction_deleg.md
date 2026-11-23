# Friction in claude-code-delegation SKILL.md

1. "the inventory session writes `docs/migration/inventory.md` and commits it" — doesn't say which branch to commit to, or what happens when CLAUDE.md forbids committing to main. Guessed: create an integration branch (`feat/date-fns`) in the main session first and commit everything there.

2. "Parallel worktree sessions: `claude --worktree <name>` ... or `git worktree add ../<name> -b <branch>`" — doesn't give the base branch. Worktrees have to branch from the foundation commit, not main, or they won't have the helper. Guessed: `git worktree add ../x -b branch feat/date-fns`, plus a note to check what `claude --worktree` branches from.

3. "Order: put shared foundations ... first in the main session, then fan out." — doesn't say whether the inventory comes before or after the foundation. Guessed: inventory first, because the helper API depends on which moment APIs are used.

4. The mode table says Main session is for work that "Needs the conversation so far", but the Order line puts foundations in the main session even though they don't need the conversation. Guessed: the Order line wins for foundations.

5. "Keep behaviour-changing fixes on a separate branch from pure refactors" — doesn't say what a refactor worker should do when it finds a bug. Guessed: preserve the current behaviour and log the bug to a findings file that the fix session reads.

6. "Merge plan: order to integrate results" — doesn't say which branch to merge into (main vs an integration branch). Guessed: an integration branch with one final PR to main.

7. "Give a subagent an edit task only when it's small and its paths don't overlap anything else running" — doesn't say whether a subagent should commit. Guessed: yes, on the current branch, because the "hand results through committed files" rule requires it.

8. "'a few turns' means roughly under 10 files or one clear change" — mixes turns and file counts, and gives no upper guidance on how many files per parallel worker. Guessed: about 13 files per worker across 3 worktrees, within the "2-4 pieces" range.

9. The docs-update piece has no clear row in the mode table (it's an edit, small, with no overlap if it runs last). Guessed: a subagent, run after everything else merges.
