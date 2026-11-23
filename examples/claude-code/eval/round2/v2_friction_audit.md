# Friction log: claude-code-setup-audit SKILL.md

1. **Lines 92-93: a rule sits in the wrong section.**
   > "1. **Scorecard**: one line per section A-F … Protect code the repo says must not change … with a mechanical deny rule such as `"Edit(./src/legacy/**)"`"

   This is a permissions check, but it's placed inside the Output/Scorecard step. That makes it unclear whether it's a check, an output requirement, or a stray line.
   *Guess:* I treated it as a section B check and reported it as a High finding with a deny rule.

2. **Lines 78 and 86: sections are out of order.**
   Section F (checks 19-22) comes before section E (checks 17-18), but the scorecard asks for "one line per section A-F".
   *Guess:* I ordered the scorecard A, B, C, D, E, F.

3. **Line 25: the trigger for the verdict is too literal.**
   > "If the user's question is 'is this safe to run unattended?'"

   The user actually said "before I let Claude run on it unattended overnight". That isn't the quoted question.
   *Guess:* I treated it as the same intent and gave a verdict line plus a pre-flight list.

4. **Lines 61-71: the example hook contradicts the line after it.**
   The example uses `npx eslint`, but the next line says "Use the repo's real package manager".
   *Guess:* I used `pnpm exec eslint`.

   The example also depends on `jq`, which the skill never mentions.
   *Guess:* I added `which jq` to the verify list.

5. **Checks 12-13: no guidance for when the check commands can't pass yet.**
   Nothing covers a repo with no tsconfig, ESLint config or tests, where the recommended hooks would fail on every edit and every stop.
   *Guess:* I made it a High finding ("instructions that are wrong") and made fixing it a pre-flight prerequisite. I also added a caveat to the hook diff.

6. **Line 14: the trigger for missing `.mcp.json` doesn't fit this repo, and no severity is given.**
   > "no `.mcp.json` while servers are enabled"

   In this repo the servers are enabled through `enabledMcpjsonServers`, but no `.mcp.json` exists. That means they're either stale or defined elsewhere, and the skill doesn't say how severe either case is.
   *Guess:* I combined it with the write-capable MCP row in section B and rated it High for an unattended run.

7. **Line 46: the auto mode setting value is never given.**
   > "or auto mode where available (verify the setting value on your version)"

   *Guess:* I recommended `acceptEdits` in the diff and listed auto mode only in the verify list.

8. **Line 49: no advice on which settings file deny rules belong in.**
   The skill doesn't say whether they go in shared `settings.json` or `settings.local.json`. That matters for `git push*`, which you'd want blocked overnight but maybe not during the day.
   *Guess:* I put everything in `settings.json` and noted that the push rule can move to the local file.

9. **Lines 79-81: one consequence of headless `acceptEdits` is left out.**
   In `-p` mode with `acceptEdits`, any Bash command that isn't allowed is refused. That makes the allow list load-bearing, but the skill doesn't connect check 19 to check 8.
   *Guess:* I wrote explicit pnpm and git allow rules and explained the effect.

10. **Line 88: cleanupPeriodDays depends on information I didn't have.**
    > "Suggest `"cleanupPeriodDays": 365` if they use `/resume`"

    I couldn't tell from the repo whether the user uses `/resume`.
    *Guess:* I left it out, rather than padding the findings.

11. **Line 51 vs line 93: unclear whether a write deny needs both rules.**
    The skill doesn't say whether `Edit(...)` deny rules also cover the Write/MultiEdit tools, or whether a separate `Write(...)` rule is needed.
    *Guess:* I used `Edit(...)` only and put the deny syntax in the verify list.
