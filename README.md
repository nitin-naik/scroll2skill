# scroll2skill

**Turn the videos you saved "for later" into agent skills, and find out whether they actually help.**

Point it at reels, Shorts, YouTube videos, a playlist or a folder, and name the job you want to get better at. It watches them (frames, on-screen text, transcript), merges what the creators teach (agreement = confidence, disagreement = cited variants), and writes 1–4 [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) for that job. Then it tests each skill cold and, optionally, blind against plain Claude.

That last step is the point. A skill only helps when the videos contain something your model doesn't already know: a new tool, a recent change, a niche method, your field's current practice. In our two demos, skills built from recent Claude Code talks **beat plain Claude 3/3**; skills built from general short-form-video tips **won 0/2**, because the model already knew it. The blind test tells you which case you're in before you install anything.

- **Any platform.** YouTube (videos, Shorts, playlists, channels, Watch Later), Instagram, TikTok, X, LinkedIn, Facebook, Vimeo, Reddit, about 1,800 sites via yt-dlp, plus local files.
- **Free and local.** Transcription runs on your machine with whisper.cpp; on-screen text uses Apple Vision on macOS or tesseract on Linux. No API keys.
- **Evidence you can check.** Every technique cites the creator and the exact moment (`&t=` link). (The Claude Code example predates this rule and cites videos, not moments.) Text in a video's caption, title, tags, chapters, speech or on-screen text that addresses an AI ("ignore previous instructions"…) is flagged, and common credential formats (API keys, tokens, private keys) are redacted before an agent reads them. This is a warning layer for English patterns, not a guarantee.
- **Tested, not just written.** Each skill is run cold by a fresh agent that reports where it had to guess and what it was never told. Optionally, it's compared blind against plain Claude on a held-back task, and a skill that doesn't win by at least 2 points out of 40 isn't installed.
- **Safe by default.** It never touches your browser cookies unless you say yes, and it explains why that matters.

## Two worked examples

| Example | Videos | Result vs plain Claude (blind) | Takeaway |
|---|---|---|---|
| [`examples/claude-code/`](examples/claude-code/) | 8 YouTube talks and tutorials on Claude Code, incl. Anthropic's own | **won 3/3** after one fix round | Recent, specialist facts the model didn't reliably know |
| [`examples/short-form-creators/`](examples/short-form-creators/) | 8 Shorts/reels on hooks, captions, editing | **lost 2/2**, two rounds | Mostly common knowledge; skills added length, not substance. Don't install |

### Example 1: 8 videos → 3 Claude Code skills

[`examples/claude-code/`](examples/claude-code/) is a complete run on 8 YouTube videos about using Claude Code: Anthropic's own talks plus well-known practitioners, about 80 minutes in total.

| Skill it wrote | What it does |
|---|---|
| [`claude-code-setup-audit`](examples/claude-code/skills/claude-code-setup-audit/SKILL.md) | Audits CLAUDE.md, permissions, hooks, agents and context cost; outputs findings plus ready-to-apply diffs; covers unattended runs |
| [`claude-code-task-loop`](examples/claude-code/skills/claude-code-task-loop/SKILL.md) | Turns a feature request into paste-ready prompts for each phase: plan, tests first, build, fresh-context review |
| [`claude-code-delegation`](examples/claude-code/skills/claude-code-delegation/SKILL.md) | Decides between main session, subagent, fork and worktrees, then writes briefs that carry the rules a subagent can't see |

### Did the skills actually help? (a small blind pilot)

Each skill was given one realistic task. Plain Claude (same model, Opus, no skill) got the same task. A separate Claude judge scored both answers without knowing which was which: 1–10 on correctness, coverage, actionability and focus, summed below out of 40. The judge prompts, randomized keys and full judgments are in the eval folder.

| | Audit | Task loop | Delegation |
|---|---|---|---|
| **Round 1** (first drafts, `eval/round1/skills_v1`) vs plain Claude | lost | lost | tie |
| **Round 2** (skills in `eval/round2`) vs plain Claude | **won** 33–31 (8+9+9+7 vs 8+7+8+8) | **won** 32–30 (9+9+8+6 vs 7+7+8+8) | **won** 33–31 (9+9+9+6 vs 7+8+8+8) |

The first drafts lost. They encoded the videos well, but they forced answers into a fixed template and pushed aside what the model already knew. For example, the audit skill produced a tidy findings table but never answered "how do I run this overnight safely?". One recommended hook could also loop forever. Those findings went back into the skills *and* into scroll2skill's own instructions ("add to the model's knowledge, don't replace it"), and the second round won all three.

Treat this as a pilot, not proof:
- The margins are small (about 2 of 40 points).
- There are three tasks, one sample each, one LLM judge (also Claude), and no variance estimate. A different judge or rerun could flip a result.
- The skill answers still score lower on focus because they run longer.
- The skills in `examples/claude-code/skills/` are the round-2 versions plus one more round of friction-log fixes (section order, hook timing, branch plan), which has not been judged. The judged round-2 answers are in `eval/round2/`.

All raw outputs, friction logs, blind keys and judgments are in [`examples/claude-code/eval/`](examples/claude-code/eval/), so you can check them yourself.

### Example 2: 8 Shorts/reels → 2 creator skills (not worth installing)

[`examples/short-form-creators/`](examples/short-form-creators/) ran the current rules on 8 public videos about hooks, script structure, captions and editing for retention. The pipeline caught a factually impossible example in one source, skipped two low-specificity videos (one a 170k-view list of hook names with no examples), and cited every technique with a timestamp. The two skills it wrote still lost to plain Claude in both rounds (29–34 and 32–33 on the final round): the videos taught what the model already knew, so the skills only added length. Its [README](examples/short-form-creators/README.md) has the details.

## Install

```bash
git clone https://github.com/nitin-naik/scroll2skill && cd scroll2skill
./setup.sh          # checks, asks, then installs yt-dlp, ffmpeg, whisper.cpp + a 547 MB speech model; links the skill
./setup.sh --check  # report only
```

- **macOS:** uses Homebrew.
- **Ubuntu/Debian:** needs `sudo` (apt packages), installs yt-dlp with pipx and builds whisper.cpp from source (a few minutes). Both land in `~/.local/bin`; the script finds them there even if that isn't on your PATH. A CI job runs this whole path in a fresh Ubuntu container on every push (`tests/linux-e2e.sh`, using the tiny speech model): setup, unit tests, then a full study on a generated video with known speech and on-screen text.
- **Windows:** use WSL.

It links the skill into `~/.claude/skills/`, and into `~/.agents/skills/` if Codex is installed.

## Use

In Claude Code:

```
/scroll2skill https://www.youtube.com/playlist?list=... — I want skills for writing better PR descriptions
/scroll2skill my Instagram "editing tips" saved collection → skills for editing my reels
/scroll2skill ~/Movies/talks/ — turn these conference talks into a skill for designing APIs
```

Other agents (Codex, etc.): ask them to use the scroll2skill skill. Steps that need subagents or a browser have fallbacks; see *Agent compatibility* in [SKILL.md](scroll2skill/SKILL.md).

The study script also works standalone:

```bash
python3 scroll2skill/scripts/study.py out/ "https://youtu.be/..." ~/clip.mp4 --links more.txt
```

## What it costs

Measured on the example run (Claude Code, Opus). Numbers are the per-subagent token totals Claude Code reports when each subagent finishes; every run is listed in [`examples/claude-code/eval/costs.md`](examples/claude-code/eval/costs.md):

| | Tokens |
|---|---|
| Fixed cost per subagent before any work (measured with an empty task; depends on how many tools and skills you have installed) | 39.7k on the author's setup |
| Work per short video, excluding that fixed cost (same reel, frames one by one vs contact sheets + OCR) | 33k → 24k |
| 8 videos, 80 min total, 3 parallel subagents (93k + 101k + 111k) | 305k (≈ 38k per video) |
| Testing 3 skills: cold runs with friction logs, plus 2 rounds of blind comparison (optional) | ≈ 545k |

Batching several videos into one subagent is the biggest saving, because it spreads the fixed cost. A lean setup has a much smaller fixed cost. Start with 5–10 videos on one topic.

## How it works

1. **Collect.** Links, playlist/channel URLs (expanded), a saved collection (via a browser tool), or files.
2. **Study script** (`study.py`, per video):
   - download at ≤720p
   - use the platform's captions first, else whisper.cpp with hallucination guards and voice-activity detection
   - frames every 0.5s for the first 3s (the hook), one per chapter, then evenly spaced
   - drop near-duplicate frames (difference hash + pixel change + on-screen text in any script; a frame is kept whenever OCR reads different numbers on it)
   - OCR the on-screen text
   - tile frames into contact sheets
   - record scene cuts, engagement metadata and chapters
   - flag text addressed to an AI and redact credentials
   - with `--skip-known`, skip videos already studied, so reruns only process new saves

   Downloaded media is deleted afterwards (`--keep-media` keeps it). Your own local files are never modified or deleted.
3. **Study** (subagents, batched): notes per video covering the opening, structure, format, what it teaches, what it shows but never says, packaging and a verdict.
4. **Distill**: 1–4 skills grouped by job, specific (commands, numbers, exact wording), every technique credited to its source.
5. **Test**: a cold run plus a friction log per skill; optionally a blind comparison against plain Claude.
6. **Gate and deliver**: a skill that doesn't beat plain Claude by at least 2 points isn't installed; for the rest, you approve before anything is installed.

## Tested, and not yet tested

Tested before release (Nov 2026):
- 52 unit tests; a full Linux run in a fresh Ubuntu container (setup, tests, a study on a generated video with known speech and on-screen text).
- ~25 real videos: YouTube (Shorts, long talks with chapters, Hindi, AI-dubbed), Instagram reels, local folders; a `--cookie-file` download.
- Three full runs by fresh agents given only this skill: a new-skill run with the blind gate (it correctly refused to install a skill that tied), an update of an existing skill (the already-studied video was skipped), and a Codex run without subagents using the fallbacks.

Not yet tested: reading cookies straight from a browser (the Keychain path), private playlists such as Watch Later, and pulling links from Instagram/TikTok/X saved collections with a browser tool. These need a logged-in account; reports welcome.

## Privacy and platform terms

- **Cookies are off by default.** For login-only videos it asks first and recommends a per-site cookies.txt export. Reading Chrome's cookie store directly needs the "Chrome Safe Storage" Keychain key, which unlocks *every* site's session; scroll2skill tells you that before you choose it.
- **What goes over the network:** downloads from the video sites you point it at, a SponsorBlock lookup for YouTube videos (to mark sponsor segments), the one-time tool and model installs, and your agent's normal model calls. Frames, transcripts and notes are sent to your model provider as part of those calls, like any file the agent reads. Transcription and OCR run locally; no extra service sees your data.
- **Use it for personal study** of videos you can already watch. Downloading may break a platform's terms of service even when the content is public; respect creators, and don't republish their videos, frames or transcripts. The example folder ships notes and skills only.
- **Some platforms are blocked in some countries** (TikTok in India, for example). The script reports that instead of retrying.

## Development

```bash
pytest -q tests                                                          # unit tests
docker run --rm -v "$PWD":/repo:ro ubuntu:24.04 bash /repo/tests/linux-e2e.sh   # full Linux run
```

## Credits

Inspired by and adapted from [doomer-agent](https://github.com/jnh12/doomer-agent) by Stiles Dichter (MIT); see [NOTICE](NOTICE). scroll2skill adds the local study pipeline, multi-platform support, cost controls and the test-before-delivery loop.

Related research: Microsoft Research's [RESOURCE2SKILL](https://www.microsoft.com/en-us/research/publication/resource2skill-distilling-executable-agent-skills-from-human-created-multimodal-resources/) distills tutorial videos and other resources into executable agent skills and reports an average +11.9 points over agents without skills. scroll2skill is a small, local take on the same idea, with a per-skill blind check so you also learn when a skill *doesn't* help.

For step-by-step software tutorials where every command should be run and verified, [brenoepics/video-to-skill](https://github.com/brenoepics/video-to-skill) adds sandboxed execution.

MIT licensed.
