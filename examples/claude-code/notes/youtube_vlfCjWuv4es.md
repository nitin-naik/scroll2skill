# Rethinking Claude Code Best Practices — Lydia Hallie (Anthropic)

## Source
- **Platform:** YouTube, channel AI Engineer (@aiDotEngineer, ~1.05M subscribers)
- **URL:** https://www.youtube.com/watch?v=vlfCjWuv4es
- **Format:** conference talk, re-recorded at home (16:9, about 17.5 min / 1051 s). Speaker in a webcam bubble over animated slides. No cuts.
- **Uploaded:** 2026-11-12
- **Engagement:** 927,570 views · 10,360 likes · 294 comments. Likes are 1.12 per 100 views and comments are 2.84 per 100 likes. That is solid reach for a conference upload, with normal engagement for a talk.
- **Caveat:** the transcript is a machine Ukrainian dub or translation track, not her English captions. I checked terms against slide OCR and the images. Exact English wording of commands said aloud (not on a slide) is therefore uncertain.

## Opening (0:00–0:30)
She explains she had technical problems at the live talk, so she is recording it at home. She introduces herself as working on the Claude Code team. Her claim is that the models (Opus 5.5 for daily work, Fable 5.2 just launched) are now strong at long tasks and at checking their own work. So "the way we work with them in Claude Code is changing". The title slide shows one line splitting into many parallel tracks with green checks. That is the promise: go from babysitting one session to running many unattended sessions.

## Structure (YouTube chapters)
- 0:00 Evolution of workflow. Early-2026 sessions on Opus 4.5 with manual approvals, steering and IMPORTANT! in CLAUDE.md, compared with today's dozens of parallel, hours-long sessions. Stat on screen: Anthropic monorepo merged changes went from 2,500/day (May 2026) to 30,000+/day (Sept 2026).
- 2:14 Rethinking best practices. Each "in the loop" job (steering, approving, saying no, checking, starting) moves to the model, the harness or the environment. Upgrade the model, switch to auto mode, trim CLAUDE.md.
- 4:11 Managing auto mode. What the classifier does, and configuring `autoMode` in settings.json in plain language.
- 5:30 Safety and environment. Deny rules, the "can I take it back?" test, sandbox.
- 8:16 Cloud-based environments. Cloud sessions, network secrets, the domain allowlist.
- 10:53 Verification strategies. Define "done", a test per task, hooks, exit code 2.
- 14:00 Scaling with CI and PRs. CI auto-fix, merge when ready, review scaled to risk.
- 15:10 Orchestration and conclusion. One orchestrator session (Fable) with Opus 5.5 workers, a recap table, and a "try this" checklist.

## Format
Clean animated slides (dark theme): timeline diagrams of tool calls, settings.json code blocks, and mock Claude Code UI showing the prompt box, model and permission-mode footer. There is no live terminal demo. Every config is shown as a slide snippet.

## Teaching
1. **Use current defaults first.** Use Opus 5.5 (or the newest model) and **auto** permission mode, not Manual. She says auto mode became the default in August 2026. The mock prompt footer changes from "Manual · Opus 4.5" to "Auto · Opus 5.5" (on screen).
2. **Strip CLAUDE.md down.** Remove "IMPORTANT", "always/never!", "Think hard and be thorough", "Keep going until it's done", the stack ("We're on Node 18") and "where to look". With current models these lead to more tool calls and worse results. Keep **only what Claude can't see in the code**. Her on-screen example of a line worth keeping: `src/legacy still serves our mobile apps`.
3. **Audit config per model.** She names a command that checks CLAUDE.md and skills for what the new model no longer needs. The translated transcript renders it as "doctor prompt audit". *Exact name UNVERIFIED (said only, and only through translation).* It is probably a `/doctor` subcommand or argument. The other video shows `/doctor` used for the same purpose.
4. **Know what auto mode does.** Reads and edits inside the project run with no check. Commands the classifier knows are safe (run tests, install deps) are allowed. Commands it is unsure about (e.g. `git reset --hard`, or pushing to a deploy repo outside the current repo) are blocked. By default it trusts only the current folder and repo.
5. **If auto mode still prompts often, tune it in plain language in `.claude/settings.json`** (on screen):
   ```json
   "autoMode": {
     "environment": ["$defaults",
       "Source control: github.com/acme and all repos under it",
       "Trusted cloud buckets: s3://acme-staging",
       "Trusted internal domains: *.internal.acme.com"],
     "allow": ["$defaults", "Deploying to staging is allowed"],
     "hard_deny": ["$defaults", "Never send code to third-party APIs"]
   }
   ```
   This text goes straight to the classifier.
6. **Use deny rules for guarantees.** Auto mode is not a guarantee. In Anthropic's August study, humans caught about 14% of clearly dangerous commands. Auto mode blocked 89%, so about 1 in 10 still got through. Deny rules are checked **before** the classifier, which never sees a denied call. On screen: `"permissions": { "deny": ["Bash(git reset --hard *)", "Read(./.env)"] }`.
7. **Decide rule vs. model with "Can I take it back?"** (on-screen table). If yes (edits to code, tests or docs, anything git can revert), leave it to the model. If no (deletes something for good, exposes a secret, sends something outside), make it a deny rule.
8. **Turn on the sandbox for side effects that permissions can't see.** `npm test` is allowed, but it runs code you didn't write (`node_modules/...`), which could read `.env` or `~/.ssh` and send them to an unknown host. Permissions only decide *whether* a call runs. The sandbox limits *what it can reach*: which files it reads, which folders it writes, which hosts it contacts. The OS enforces it, including on child processes. Turn it on with `/sandbox` or `"sandbox": { "enabled": true }` (on screen). With the sandbox on, deny rules pass down to the OS. Add `"Read(~/.ssh/**)"` yourself, because by default the sandbox can still read most of your disk. Limit: Claude's own file tools, MCP servers and hooks run **outside** the sandbox.
9. **Run long or unattended work in cloud sessions.** You get a fresh machine with a clean repo clone, it keeps running with the laptop closed, and there is no `.env`, SSH key or GitHub token on it. Add API keys as **network secrets**, so they are used without being shown to the model. The default network is limited to package registries and GitHub, so allowlist any other domains. The machine is temporary, but what leaves it (pushes, connector messages) is not. Keep auto mode and commit the deny rules to the repo (blocks force-push and committed secrets).
10. **Define "done" in the prompt** (on screen): "Move auth over to the new API. It's done when the auth tests pass and nobody gets logged out. Split it into tasks, each with its own test. Show me the test output." Without this, one request can produce many plausible but wrong outcomes (old API left in place, only new logins moved, everyone logged out).
11. **Enforce checkpoints with hooks** (on screen): every edit runs lint (`PostToolUse`), every task runs its tests (`TaskCompleted`, for example auth tests when auth was touched), and the end of the session runs all tests (`Stop`).
12. **Hook scripts must exit with code 2 to make Claude go back and fix the problem.** Exit 1 (the default for most test tools on failure) still lets the task be marked completed (on screen: "exit 2 → goes back to fix it; exit 1 → marked as completed"). This matches the documented hook behavior, where exit 2 blocks.
13. **Let CI be the shared check.** Every session ends in a PR, so CI runs the same checks no matter how the session went. Turn on **CI auto-fix** (Claude sees failing checks and fixes them) and GitHub **Merge when ready** for low-risk PRs.
14. **Scale review to risk.** At Anthropic, every PR is first reviewed by Claude in a separate session with fresh context, plus a separate group of agents that re-checks each bug found. Small changes (typos, lint fixes) need no human. Most changes get one reviewer. The riskiest get more than one.
15. **Orchestrate.** One main session splits the work, starts one worker session per task, follows their results and sends back anything incomplete. The orchestrator writes no code. Use a model that is good at deciding and judging (Fable) for the orchestrator, and Opus 5.5 for the workers. They are configured separately. In this setup context compaction and clearing are handled for you. She names the product as a beta (translation reads "Claude Code projects"). *Exact feature name UNVERIFIED.*
16. **Try it this way:** pick one task much bigger than you usually give Claude. Make sure CI catches what you care about. Set up the cloud environment (network access, secrets, setup script). Start in the cloud and watch where sessions get stuck or still need you, because that is the next thing to hand off.

**Flags:** Several features are recent or beta (TaskCompleted hook event, `autoMode` settings block, Fable orchestration, CI auto-fix). Check them against current docs before relying on them. The 2,500 → 30,000 stat and the 14%/89% study figures come from Anthropic's own posts and were not independently checked. "acme" names are example placeholders.

## Demonstrated vs. said
- The whole talk is built as "move each human-in-the-loop job to the model, the harness or the environment". The closing table maps steering to the model, approving to auto mode, saying no to deny rules and the environment, checking to tests, hooks and CI, and starting sessions to Claude. It is a usable audit checklist even though she never calls it one.
- Defense in depth is used without naming it: the classifier, then deny rules (before the classifier), then the OS sandbox, then the cloud VM, then CI and review.
- The "done" prompt is an example of acceptance criteria plus asking for evidence ("show me the test output") instead of trusting a claim of success.

## Packaging
- **Title:** "Rethinking Claude Code Best Practices — Lydia Hallie, Anthropic". It carries authority (an Anthropic staffer) and a "rethinking" angle that makes viewers worry their setup is out of date. It works.
- **Caption:** a clear promise ("most of what we've added... is now holding them back") plus a speaker bio. There are no tags specific to Claude Code (only generic AI Engineer channel tags).
- **What works:** tight 17 minutes, chapters, very clear diagrams, config snippets you can copy.
- **What doesn't:** no live demo. Some feature names are said aloud only (prompt audit, orchestrator product). It leans on new and beta features.

## Verdict
**USEFUL.** It is authoritative and current, with concrete settings for auto mode, deny rules, the sandbox, hooks (exit 2) and CI that change how you set up Claude Code.
