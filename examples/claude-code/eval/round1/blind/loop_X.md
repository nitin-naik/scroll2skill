# Running "login rate limiting" in Claude Code

Use one session in three short phases: **plan, then a failing test first, then implement until green.** The tests are the spec. That way Claude can check its own work and you only need to review one diff at the end.

## 0. Before you start (one minute)
```bash
git switch -c feat/login-rate-limit
claude
```
If your repo doesn't have a CLAUDE.md yet, run `/init` first so Claude knows your test and lint commands. Then press **Shift+Tab** until you're in **plan mode**, so Claude reads the code without editing anything.

## 1. Plan (paste this in plan mode)
```
Add rate limiting for failed logins on our login endpoint.

Requirements:
- Key: email + client IP. Normalize email (trim + lowercase). Use the IP that Express gives after our trust-proxy setup; check how app.set('trust proxy') is configured and tell me.
- Limit: max 5 FAILED attempts per key in a 15-minute window, stored in our existing Redis client (find it; don't add a new connection or a new Redis library).
- When a key is over the limit, reject BEFORE checking the password: HTTP 429, a `Retry-After` header in whole seconds (time until the window frees up, at least 1), and a JSON body in the same shape as our other error responses.
- Successful login clears the counter for that key.
- Only failed credential checks count. Validation errors (400) and server errors (5xx) don't count.
- Redis operations must be atomic: INCR + EXPIRE in a MULTI or a Lua script, setting the TTL only on the first increment, so the window doesn't slide forever and a crash can't leave a key with no TTL.
- If Redis is down: fail open (allow the login) and log a warning. Tell me if you think we should fail closed instead.
- The response must not reveal whether the email exists. Same 429 for unknown and known emails.

First, explore: find the login route/handler, the Redis client, the error-response helper, the existing Vitest setup, and how other tests handle Redis (real instance, ioredis-mock, or a hand-written fake). Then give me a short plan: which files you'll touch, the limiter's API, and the list of test cases. Don't write code yet.
```
Read the plan. Correct anything that's off (Redis mocking approach, fail-open vs fail-closed, where the middleware goes). Then press Shift+Tab to leave plan mode. "Accept edits" is fine here.

## 2. Tests first (paste)
```
Good. Now write ONLY the tests, no implementation yet. Use Vitest and follow our existing test conventions and Redis approach. Use fake timers (vi.useFakeTimers) or a controllable clock for the window. Don't sleep.

Cover:
1. 5 failed attempts → each returns 401. The 6th → 429 with Retry-After ≈ 900.
2. Once over the limit, even the CORRECT password gets 429 (the password isn't checked).
3. After 15 minutes the key is allowed again.
4. Retry-After decreases as time passes (e.g. after 10 min it's ≈ 300).
5. A successful login after 3 failures resets the count. 5 more failures are allowed after that.
6. Separation: same email + different IP, and same IP + different email, each have their own counter.
7. Email normalization: "User@X.com " and "user@x.com" share a counter.
8. A 400 validation error doesn't increment the counter.
9. Unknown email and known email get the same 429 response.
10. Redis error → login still works (fail open) and a warning is logged.
11. Unit test for the limiter: the TTL is set on the first increment only.

Run the new tests and show me they fail for the right reason (missing behavior, not import or setup errors). Commit them with "test: login rate limiting (failing)".
```

## 3. Implement (paste)
```
Now implement it so all the tests pass. Constraints:
- Put the limiter in its own module (e.g. src/services/loginRateLimiter.ts or wherever our services live) with a small API like check(key), recordFailure(key), reset(key). Wire it into the login route. Keep the route handler thin.
- Read limits from config/constants (MAX_ATTEMPTS = 5, WINDOW_SECONDS = 900), not magic numbers inside the logic.
- Don't add new dependencies unless you ask me first.
- Don't change the tests to make them pass. If a test looks wrong, stop and tell me why.

Loop: run the rate-limit tests, fix, repeat. When they pass, run the full test suite, typecheck and lint, and fix anything you broke. Finish with a summary: files changed, how Retry-After is computed, fail-open behavior, and anything you weren't sure about.
```

## 4. Review before you merge
In a fresh session (`/clear` or a new terminal), so the reviewer isn't biased by the reasoning that wrote the code:
```
Review `git diff main...HEAD` as a security reviewer. Check for: race conditions under concurrent requests (do two parallel failures both count?), IP spoofing via X-Forwarded-For, a key that never expires, user enumeration via timing or response differences, a Retry-After that's wrong or negative, and Redis key names that could collide with existing keys. List concrete issues with file:line. Don't edit anything.
```
If you have it, `/security-review` or `/code-review` works here too.

## Tips
- **Interrupt early.** If Claude heads somewhere you don't want, press **Esc**, correct it in one sentence, and carry on. Use Esc Esc to rewind to an earlier message.
- **Turn it off if it gets noisy:** if it starts editing unrelated files, tell it "Only touch the login route, the new limiter module and its tests."
- **Want it hands-off?** After step 1, steps 2–3 can run headless:
  `claude -p "<step 2 + 3 text>" --permission-mode acceptEdits --allowedTools "Bash(pnpm test*)" "Bash(npx vitest*)" "Bash(git add*)" "Bash(git commit*)"`. Change the commands to match your package manager.
- **Things to decide yourself, not Claude:** fail-open vs fail-closed, whether you also want a per-IP-only limit (to stop someone spraying many emails from one IP; this email+IP limit doesn't cover that), and whether 429s should be audit-logged.
