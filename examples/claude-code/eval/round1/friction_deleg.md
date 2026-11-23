# Friction log: claude-code-delegation skill

1. **The modes overlap: worktree sessions vs orchestrator + workers.** The table offers both "Independent features or fixes touching different files → Parallel sessions, one git worktree each" and "One big job splittable into tested tasks → Orchestrator + workers". A 40-file migration fits both rows. Nothing says how to choose between them.
   *Guess:* I used manual worktree sessions. The skill says orchestration is "some features in beta, verify availability", and this job is medium-sized.

2. **No threshold for "a few turns".** The skill says "Don't parallelize what one session can do in a few turns", but gives no rule of thumb in files or turns.
   *Guess:* 40 files is more than a few turns, but not by enough to justify more than 3 worktrees.

3. **No guidance on order or dependencies between pieces.** The Merge plan covers integration order. But the "Split" step doesn't say how to handle a piece that must finish before others can start (here, the shared helper module, and timezone fixes after the migration). It also doesn't say whether behaviour-changing fixes should be kept apart from refactors.
   *Guess:* helper first in the main session, then migration, then timezone fixes on their own branch, then docs.

4. **The "Subagent" vs "Worktree" choice is unclear for work that edits files.** The subagent row describes read-only "answer without the journey" work. The docs piece is a small edit, and the skill doesn't say whether a subagent may edit files or commit on a branch.
   *Guess:* I made docs a subagent with edit scope limited to docs/, on its own branch.

5. **"Built-in Explore and Plan agents skip CLAUDE.md and git status."** The skill doesn't say which agent type to recommend instead for a read-only search.
   *Guess:* I recommended a general-purpose subagent, with the rules restated anyway.

6. **"Main" appears in the Output format but gets no prompt.** "a complete delegation prompt for each non-main piece". It's unclear whether main-session pieces should get any guidance (what to decide, which commands to run).
   *Guess:* I described the main piece briefly in the merge plan, with no prompt.

7. **Prompts for pasted sessions vs subagents.** Section 2 describes what a *subagent* receives. Parallel worktree sessions are full sessions: they load CLAUDE.md but have none of this conversation. The skill doesn't say whether the 5-part brief applies the same way, or whether restating CLAUDE.md rules is still needed there.
   *Guess:* I used the same 5-part brief and restated the rules anyway (it costs little and protects against missing context).

8. **"Agent files: any `.claude/agents/*.md` worth creating"** has no criterion for "worth creating".
   *Guess:* I created only a reviewer, since it gets reused on every PR. The one-off inventory stays a plain prompt.

9. **No step for handing results between pieces.** The skill doesn't say how one piece's output (the inventory tables) should reach later prompts.
   *Guess:* placeholders in the prompts ("paste Table A rows here").

10. **Domain/tooling facts outside the skill.** The skill can't help with date-fns timezone packages (`@date-fns/tz` vs `date-fns-tz`) or TZ-based test runs. I added these from general knowledge and noted that the version should be checked.
