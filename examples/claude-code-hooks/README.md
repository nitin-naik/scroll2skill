# Example 3: 3 videos on Claude Code hooks → refused by the gate

A fresh agent ran the full scroll2skill workflow, unattended, on 3 YouTube videos about Claude Code hooks ([links.txt](links.txt)). The job: "writing Claude Code hooks".

| Video | Creator | Length | Verdict |
|---|---|---|---|
| [Hooks in Claude Code](https://www.youtube.com/watch?v=IkaPHiMDazM) | Claude (official Anthropic channel) | 3:21 | USEFUL. Most precise source, but its force-push regex is buggy |
| [How Claude Code Hooks Save Me HOURS Daily](https://www.youtube.com/watch?v=Q4gsvJvRjCU) | Better Stack | 2:43 | USEFUL. Live proof that exit 2 + stderr makes Claude self-correct; its event list is outdated |
| [Skills vs Subagents vs MCP vs Hooks vs Plugins](https://www.youtube.com/watch?v=qljN6aKRez8) | Skills For AI | 6:14 | SKIP. Accurate but shallow |

It wrote two skills, [`writing-claude-code-hooks`](skills/writing-claude-code-hooks/SKILL.md) and [`auditing-claude-code-hooks`](skills/auditing-claude-code-hooks/SKILL.md), cold-tested them, fixed the friction, and compared each blind against plain Claude (same model, same tools, no skill). The judge ran both answers' code.

## Result: both tied, neither installed

Scores are correctness / coverage / actionability / focus, each out of 10.

| Task | Round | Plain Claude | With skill | Margin |
|---|---|---|---|---|
| Write hooks | 1 (first draft) | 7/7/9/9 = 32 | 8/9/9/7 = 33 | +1 |
| Write hooks | 2 (after fixes) | 9/8/9/9 = 35 | 9/10/9/6 = 34 | −1 |
| Audit hooks | 1 (first draft) | 9/8/9/8 = 34 | 9/9/9/8 = 35 | +1 |
| Audit hooks | 2 (after fixes) | 9/8/9/8 = 34 | 9/10/9/7 = 35 | +1 |

A skill must win by at least 2 points out of 40 to be installed. Every margin here was 1 point from a single judge, which is noise, so both skills count as ties.

## Why

- **The videos taught what the model already knew.** Exit code 2 blocks, the JSON `permissionDecision` deny, `$CLAUDE_PROJECT_DIR`, matcher syntax: plain Claude got all of it right (9/10 correctness in every round).
- **The skills' extra coverage was real but cost focus.** The write skill added a guard for Bash writes to protected files (`echo >> .env`, `sed -i migrations/`), which plain Claude missed and even wrongly claimed its Edit deny rules covered. After the fix round, though, its answers were about 2.5x longer, and focus fell from 9 to 6.
- **The audit skill found more** (NotebookEdit, `git push -uf` and `+main` force pushes, fail-closed when jq is missing, a retry cap), but its quote-stripping guard flags `git commit -m "rm -rf / fix"` as dangerous.

The most useful finding wasn't a skill: the force-push check in the official video misses cases. That's in [its notes](notes/youtube_IkaPHiMDazM.md).

## What changed in scroll2skill because of this run

The agent logged 26 problems with the workflow. The ones that changed the rules:

- Margins under 2/40 are ties (before, any win counted).
- The blind comparison uses a held-back task written *before* the skill is drafted, so fixes can't be fit to the test (round 2 here reused the round-1 task).
- A fixed judge prompt, so rounds are comparable.
- Fixes that bloat the answer are called out, not only fixes that narrow it.
- The audit fixture is built by a separate agent, so the skill isn't graded on its own answer key.

## Files

- `notes/`: what the study agent took from each video
- `skills/`: the fixed drafts (not installed)
- `eval/round1/`: first drafts (`skills_v1/`), blind answers (`*_X.md`, `*_Y.md`), `judgement.md`, `key.txt`, friction logs
- `eval/round2/`: answers from the fixed drafts, `judgement.md`, `key.txt`
- `eval/audit-fixture/`: the hooks setup with planted flaws; `audit-fixture-key.txt` lists them (the judge never read it)
