# Friction log: claude-code-task-loop skill

1. "Hooks that block finishing until checks pass (see the `claude-code-setup-audit` skill; failing hooks must exit 2)." I was told to read only this skill, and that skill isn't available, so I couldn't give hook config. Guess: I left hooks out of the checklist instead of giving a half-specified hook.

2. "Use the strongest level available" followed by a numbered list 1-4. It doesn't say whether the list is ordered weakest-first or strongest-first, or whether "use the strongest" means use only that one. Guess: the list goes from weakest to strongest, levels add up, and I used 1+2 (browser isn't relevant; hooks can't be specified).

3. Step 3 says "Ask Claude to commit after each working step", but step 5 is titled "Review in fresh context, then commit" and says "Before the final commit, spawn a reviewer". It's unclear whether the review covers the whole multi-commit diff or only the last step. Guess: one review of the full feature diff before a final fix-up commit.

4. Output item 1, "Kickoff prompt ... 'done when…' with evidence", and step 2, "The plan must end with a Verification section". It's unclear whether the kickoff prompt itself should contain the verification list (output item 2) or just ask Claude to produce one. Guess: the prompt asks Claude to end its plan with a Verification section, and the verification list is kept separate for the user to check against.

5. "Name exact files and constraints when you know them". I don't know the user's file paths. The skill doesn't say whether to use placeholders or let Claude find them. Guess: placeholders with example paths plus "(find it if I left this blank)".

6. The skill says nothing about surfacing gaps in the user's own requirements (reset on success? fixed vs. sliding window? fail-open vs. fail-closed when Redis is down? proxy IP?). Guess: I added a "decide these in the plan" list to the kickoff prompt. That's arguably beyond the skill's output spec.

7. Output item 4, "Risks: anything irreversible the task touches (migrations, deletes, deploys)". This task touches nothing irreversible. The skill doesn't say whether to write "none" or list non-irreversible but high-impact risks. Guess: I listed the high-impact risks (lockouts, missing TTL) and said that nothing is irreversible apart from deploys.

8. "with the commit points marked". No format is given. Guess: bold **COMMIT** on checklist items.

9. "Approve with 'Yes, clear context and auto-accept edits'". This quotes exact UI wording I can't check. Guess: repeated it as written.

10. "Ask a subagent or a side question". There's no command for "side question", so it's unclear what to tell the user to type. I didn't use it in the output.

11. The loop is "Explore → Plan → Build → Verify → Commit" in the body but the cited source title says "Explore → Plan → Code → Commit". It's a small inconsistency with no effect on the output.

12. There's no guidance on answer length or framing (any preamble, how much explanation). Guess: one-line intro, then the four output sections.
