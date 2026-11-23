# Example: short-form creator tips (a skill that did NOT beat plain Claude)

8 public videos on making Reels/Shorts (hooks, script structure, captions, editing for retention), studied with the current scroll2skill rules. 6 were used, 2 skipped (a list of hook names with no examples; generic tips).

The pipeline worked as designed: timestamped citations, creator agreement counts, a factual error caught in a source ("1893 Richard Feynman"; he was born in 1918), screen-over-speech corrections, and AI-dub caption tracks detected and ignored.

**But the skills lost the blind comparison to plain Claude, twice:**

| | Script task | Edit-plan task |
|---|---|---|
| Round 1 (first drafts, `eval/round1/skills_v1`) | lost 31–32 | lost 31–33 |
| Round 2 (after fixing friction + coverage gaps, `skills/`) | lost 29–34 | lost 32–33 |

Scores are four 1–10 dimensions summed (correctness, usefulness, actionability, focus); the judge, keys and raw answers are in `eval/`.

**Why:** these videos mostly teach things the model already knows (payoff-first hooks, word-by-word captions, open loops). The skills added caveats and structure but no new substance, and the extra length cost "focus". Compare `../claude-code/`, where the videos carried recent specialist facts and the skills won 3/3.

This is the case scroll2skill's blind test exists for: **don't install a skill that doesn't beat the base model.** The skills are kept here as a worked example, not as recommended installs.

Token cost: study 205k (2 subagents × 4 videos), tests and judging 424k.
