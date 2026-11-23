# Running "rate-limit the login endpoint" in Claude Code

**Short answer:** do it as four prompts in one session. Plan first in plan mode, then have Claude write failing tests, then build until they pass, then get a review in a fresh context. Commit after each step. Everything to paste is below, in order.

Before you start, have the answers to the four **open decisions** ready, or let the plan propose them and approve them yourself. They change the code, so settle them in the plan, not halfway through the build:
1. **Window type:** fixed window (counter with a 15-min TTL set on the first failure) or sliding window. Fixed is simpler and matches "5 per 15 minutes". Sliding is stricter at the window edges.
2. **Reset on success:** does a correct login before the limit clear the counter? This is usually yes.
3. **Redis down:** fail open (allow the login, log an error) or fail closed (return 503)? Most teams fail open on login so an outage doesn't lock everyone out.
4. **Client IP behind a proxy:** what is `app.set('trust proxy', ...)` set to? If it's wrong, `req.ip` is either the load balancer for everyone (one shared bucket) or spoofable through `X-Forwarded-For`.

---

## 1. Paste-ready prompts

### (a) Kickoff: plan mode, no edits
Press **Shift+Tab** until "plan mode on" shows, then paste:

```
I need to add brute-force protection to our login endpoint. Figure out where in this Express + TypeScript API it should happen, whether we need new dependencies (I'd rather use the existing Redis client than add a rate-limit library unless there's a strong reason), and how to approach it.

Context:
- Login route: <path to login route/controller>. Find it if I left this blank.
- Redis client is already set up: <path to redis client>. Find it if blank.
- Tests are Vitest. Look at how existing tests hit routes (supertest?) and how they get Redis (real instance, testcontainers, mock?), and follow that.

Requirement:
- Count FAILED login attempts per (normalized email + client IP). Lowercase and trim the email.
- Max 5 failures per 15 minutes. While locked, the endpoint returns 429 with a Retry-After header (integer seconds left in the window) BEFORE checking the password. A correct password while locked still gets 429.
- The window starts at the first failure (TTL set only then, never extended by later failures). Increment and TTL must be atomic (MULTI or a Lua script, or SET NX EX then INCR). No race where a key ends up with no TTL.
- Malformed requests (missing or invalid email/password, validation 400s) don't count as failures.
- The 429 body and the failure responses must not reveal whether the account exists. Unknown-email failures count the same as wrong-password failures.

Decisions the plan must settle (propose an answer for each, with a one-line reason):
1. Fixed vs sliding window
2. Does a successful login reset the counter?
3. Redis unavailable: fail open or closed, and how it's logged
4. How client IP is derived: current `trust proxy` setting, and whether X-Forwarded-For can be spoofed in our deployment
5. Redis key format (consider hashing the email so raw emails aren't stored in Redis)

It's done when: the 6th failed attempt for the same email+IP within 15 minutes returns 429 with a correct Retry-After, the same email from a different IP is unaffected, and all existing auth tests still pass. Split it into tasks, each with its own test. Show me the test output.

End the plan with a Verification section listing the concrete checks (request → expected status/header/Redis state).
```

Read the plan. If something is wrong, press **Ctrl+G** to edit the plan file directly, save, and tell Claude "I edited the plan, re-read it." Don't argue with it in chat. When the plan is right, approve it with **"Yes, clear context and auto-accept edits"**.

### (b) Tests first
```
Before writing any implementation, write failing Vitest tests for the cases in the plan's Verification section plus the cases below. Run them and show me they fail for the right reason (missing behaviour, not import or setup errors). Do not change these tests later to make the code pass. If a test seems wrong, stop and tell me.

Cases: <paste the Test spec list from section 2 below>
```
Check the tests yourself before moving on. Make sure they actually assert the 429, the Retry-After value, and the Redis TTL, rather than only "status is not 200". Then: **"Commit these tests."**

### (c) Build
```
Now implement the plan to make those tests pass, one task at a time. After each task, run the full test suite (`<your test command, e.g. npx vitest run>`), show me the output, and commit with a message in this repo's style. Don't modify the tests from the previous step. Keep the change small: a limiter module + wiring in the login route + config for the limits. Don't refactor unrelated auth code.
```
If it heads somewhere wrong (new dependency you didn't approve, touching unrelated files), press **Esc** right away. If it has gone sideways, revert to the last good commit, `/clear`, and retry with a sharper instruction.

### (d) Fresh-context review
```
Use a subagent to review the whole feature diff (`git diff <base-branch>...HEAD`) against the plan. Tell it to report ONLY issues that affect correctness, the stated requirements, or the done condition. Specifically check:
- Is INCR + TTL atomic, and is the TTL set only on the first failure? Can a key ever persist with no TTL?
- Is the lock checked before the password is verified (no password oracle while locked, and no bcrypt work burned)?
- Is Retry-After an integer number of seconds derived from the real Redis TTL?
- Do unknown-email and wrong-password paths count and respond identically (no account enumeration, including timing differences)?
- How is client IP derived, and can X-Forwarded-For be spoofed to dodge the limit?
- What happens when Redis throws or times out? Does it match the decision in the plan?
- Do malformed requests and 5xx errors avoid incrementing the counter?
Everything else is optional; list it separately and don't fix it.
```
Fix what's real, rerun the tests, then make the final **COMMIT**.

---

## 2. Test spec (what the tests must cover)

**Core**
1. Failures 1–5 for the same email+IP return the normal 401. The 6th returns **429** with `Retry-After`.
2. `Retry-After` is an integer number of seconds, about 900 right after the 5th failure, and lower on a later request (it counts down). Assert this through Redis TTL or by manipulating the key's TTL. Vitest fake timers do **not** move real Redis time.
3. **TTL is set only on the first failure.** After failures 2–5, the key's TTL keeps counting down and is not reset to 900.
4. After the window expires (set a short TTL in the test, or delete the key), the user can log in again.
5. **Correct password while locked still gets 429**, and the password is not checked (spy on the hash compare).

**Scope of the key**
6. Same email from a different IP: not limited.
7. Different email from the same IP: not limited.
8. `User@Example.com ` and `user@example.com` share the same counter.

**What counts**
9. Malformed requests (missing email, missing password, invalid body → 400) don't increment the counter.
10. A successful login before the limit resets the counter (if you chose that in the plan).
11. A server error (e.g. DB throws) doesn't count as a failed attempt.

**Abuse and leakage**
12. Unknown email and wrong password both increment the counter and return identical status and body. The 429 body is identical whether or not the account exists.
13. Header spoofing: sending a different `X-Forwarded-For` on each request doesn't reset the limit under your production `trust proxy` setting.
14. Redis unavailable (mock the client to throw): behaviour matches the fail-open/closed decision and logs an error. The request doesn't hang.
15. Concurrency: fire about 10 parallel failed attempts. The counter ends at 10 with a TTL set, and at most 5 got through to password checking.

---

## 3. Session checklist

1. Shift+Tab into plan mode → paste prompt (a).
2. Read the plan. Check that all 5 decisions are answered and the Verification section matches the test spec. Ctrl+G to edit if needed.
3. Approve with "clear context and auto-accept edits".
4. Paste prompt (b). Check that the tests assert real behaviour → **COMMIT** (tests).
5. *(Optional, after step 4)* Add a Stop hook so Claude can't finish while tests fail. Put it in `.claude/settings.json`:
   `"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "npx vitest run >&2 || exit 2"}]}]}`
   Use your real test command. It must `exit 2` (exit 1 doesn't block). Add it **after** the tests-first step, because in step 4 the tests are supposed to fail. Remove it or keep it narrow if your suite is slow.
6. Paste prompt (c). Claude builds task by task → **COMMIT** after each passing task.
7. If context gets tight, run `/compact` right after a commit.
8. Paste prompt (d). Fix the real findings and rerun the tests → **COMMIT** (final).
9. If Claude hit the same snag twice (e.g. how test Redis is started), have it add the fix to CLAUDE.md.
10. `/clear` before the next feature.

No browser checks are needed. This is API-only.

---

## 4. Risks

**Nothing irreversible.** There are no migrations, deletes, or deploys in this task. Redis keys expire on their own, and the change reverts cleanly with git. The rollout still has three high-impact risks:

1. **Wrong client IP → mass lockout or no protection.** If `trust proxy` is off behind a load balancer, every user shares the LB's IP, so 5 failures from anyone lock out that email for everyone. If it's set to `true` with no proxy, attackers rotate `X-Forwarded-For`. Confirm the setting against your real deployment (number of proxy hops) before you ship.
2. **Redis failure mode.** A Redis blip either locks everyone out (fail closed) or silently removes protection (fail open). Choose deliberately, log and alert on it, and add a short Redis timeout so login doesn't hang.
3. **Lockout as a DoS and enumeration vector.** Because the key is email+IP, an attacker can't lock a victim out from their own IP. That's good, but it also means a botnet gets 5 tries per IP per email. Consider a separate, looser per-IP or per-account limit later. Keep the 429 and 401 responses free of account-existence hints.

Gate it by shipping behind a config flag or with the limit set in env vars, so you can loosen or disable it without a redeploy if real users start getting 429s.
