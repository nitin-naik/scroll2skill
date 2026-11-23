Run it as one loop: **Explore → Plan → Build → Verify → Commit**. Below is a kickoff prompt to paste, the checks that define "done", a session checklist with commit points, and the risks.

## 1. Kickoff prompt (paste in plan mode)

Press **Shift+Tab** until "plan mode on" shows under the input. Claude can read the code but can't edit it yet. Then paste this, filling in the paths if you know them (Tab completes paths):

```
I need to add rate limiting for failed logins on our login endpoint. Figure out where in our Express + TypeScript API this should happen (route handler, middleware, or auth service), how to reuse our existing Redis client, whether we need any new dependencies (I'd prefer none if the Redis client is enough), and how to approach it.

Known context:
- Login route: <path, e.g. src/routes/auth.ts>   (find it if I left this blank)
- Redis client: <path, e.g. src/lib/redis.ts>
- Tests: Vitest. Follow the existing test setup and how other tests handle Redis (real or mocked).

Requirements:
- Limit is 5 FAILED login attempts per (email + IP) pair in a 15-minute window.
- Once the limit is hit, the next attempt gets a 429 with a `Retry-After` header (seconds until the window resets), and the password is not checked.
- Only failed attempts count. Normal successful logins must not change.
- Normalize the email (trim and lowercase) before building the key.
- Get the client IP correctly given our proxy setup. Check the `trust proxy` setting and tell me what you find.

In the plan, say what you decide on each of these:
- Does a successful login reset the counter for that email+IP?
- Fixed window (INCR + EXPIRE on the first failure) or a sliding window? Keep the increment and the expiry atomic either way.
- What happens if Redis is down: fail open or fail closed?

It's done when a 6th failed attempt within 15 minutes from the same email+IP gets a 429 with a correct Retry-After header, and existing login behavior and the existing test suite still pass. Split the work into tasks, each with its own test. End the plan with a Verification section of concrete checks. Show me the test output.
```

When the plan comes back, edit it directly instead of arguing with it. **Ctrl+G** opens the plan in your editor. Save it, then tell Claude you changed it. If the plan is self-contained, approve with **"Yes, clear context and auto-accept edits"** so the build starts with a clean context.

## 2. Verification list

1. Five failed logins for `a@x.com` from one IP each return the normal 401 (or whatever the endpoint returns today). The 6th returns **429** with a `Retry-After` header holding a positive integer of 900 or less.
2. While the user is locked out, a request with the **correct** password still gets 429, and the password isn't checked.
3. Isolation: same email from a different IP is not blocked, and a different email from the same IP is not blocked. `A@X.com ` and `a@x.com` share one counter.
4. Expiry: once the window passes (use Vitest fake timers or a short TTL set in config), the email+IP can log in again. The Redis key has a TTL and is never left without one.
5. A successful login before the limit doesn't count toward it (and resets it, if that's what the plan chose).
6. The whole test suite plus `tsc --noEmit` pass, and Claude shows the output.
7. Redis outage: the endpoint follows the fail-open or fail-closed rule the plan chose, and a test covers it.

## 3. Session checklist

- [ ] **Plan mode.** Paste the kickoff prompt, read the plan, fix it with Ctrl+G, and approve with "clear context and auto-accept edits".
- [ ] **Check the tests before trusting them.** Look at the first tests Claude writes and make sure they test the real requirement: the 6th attempt, Retry-After, the email+IP key. Weak tests give you false passes.
- [ ] **Build in small steps**, in roughly this order:
  - [ ] Limiter module (Redis increment, read the count and TTL) with unit tests. **COMMIT** ("Can you create a commit for this?" makes Claude match your `git log` style.)
  - [ ] Wire it into the login route: count failures and return 429 + Retry-After when blocked. Add integration tests with supertest or your existing HTTP test helper. **COMMIT**
  - [ ] Reset on success and the Redis-down behavior, with tests. **COMMIT**
- [ ] If Claude heads the wrong way, press **Esc** right away. Press **Esc Esc** to rewind code and/or conversation. If it really goes sideways, revert to the last good commit, `/clear`, and retry with sharper instructions.
- [ ] **Verify.** Have Claude run the full suite and the type check and show you the output, then go through the verification list above. This is an API change, so skip browser checks.
- [ ] **Fresh-context review.** Before the final commit, say: "Use a subagent to review the diff against the plan. Only flag issues that affect correctness, the stated requirements, or the done condition." Fix those issues. **FINAL COMMIT**
- [ ] If Claude hit the same problem twice (for example, how Redis is mocked in tests), have it add the fix to CLAUDE.md.
- [ ] **Context:** if you run low on room mid-feature, `/compact` right after a commit. When this feature is done, `/clear` before starting the next one.

## 4. Risks and how to gate them

- **Locking out real users or everyone at once.** If the IP is read wrong behind a proxy or load balancer (for example, every request shows the LB's IP), a whole office shares one counter, or the limit gets applied in the wrong place. Gate: have Claude confirm the `trust proxy` setting in the plan, and test with `X-Forwarded-For`.
- **Redis keys without a TTL** turn into permanent lockouts. Gate: the increment and expiry must be atomic (MULTI or a Lua script), and the tests should check the TTL.
- **Redis-down behavior is a security vs. availability choice.** Decide it yourself in the plan. Don't let Claude pick it silently.
- **Nothing irreversible here.** There are no migrations or deletes. Deploying is the irreversible step, so keep it out of this session: Claude commits locally, and you push or deploy after reviewing. Consider putting the limit (5, 15 minutes) in config so you can tune it without a redeploy.
