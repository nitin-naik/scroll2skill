# Friction: claude-code-task-loop skill

1. "A `Stop` hook that blocks finishing until tests pass." (step 4.3) together with Output (b) "write failing tests for these cases". These conflict: if the hook is installed before the tests-first phase, Claude can't end its turn after deliberately writing failing tests, and it loops or edits code/tests to get out. The skill doesn't say when to add the hook. I guessed: add it after the tests-first commit, and said so in the checklist.

2. "The kickoff prompt tells Claude to end its plan with a **Verification** section; you also keep your own list (output item 2) to check the plan against. The plan must end with a **Verification** section..." (step 2, first bullet). This states the same requirement twice in one bullet and reads like a merge leftover. It isn't contradictory, just redundant. No guess needed.

3. "Approve with 'Yes, clear context and auto-accept edits' when the plan is self-contained" versus Output 1 asking for separate prompts (b) tests-first, then (c) build. After approval Claude starts building right away, so the tests-first prompt has no natural slot unless the plan itself orders tests first. I guessed: keep (b) as the first prompt after approval and tell the user to check the tests before (c). An alternative would be to put "tests first" inside the plan; the skill doesn't say which.

4. "Session checklist (short)" combined with all the required content. "Short" is undefined. I guessed about 10 numbered steps.

5. Missing: guidance on testing time-based behaviour against real Redis (fake timers don't move Redis TTL). It isn't in the skill, so I added it from my own knowledge, as the skill permits.
