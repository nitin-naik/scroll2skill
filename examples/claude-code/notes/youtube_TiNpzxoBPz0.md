# Claude Code - 47 PRO TIPS in 9 minutes

**Source:** YouTube, Greg Baugues (@gregcode, 11.6K subscribers). https://www.youtube.com/watch?v=TiNpzxoBPz0. Horizontal talking head plus screen recordings, 9:18 (558s), uploaded 2025-05-22. 210,994 views, 5,240 likes, 163 comments. Likes per 100 views: 2.48. Comments per 100 likes: 3.11. Views are 18x the subscriber count, so it broke out well beyond his audience. It is about 18 months old as of Nov 2026 (the Claude Code banner on screen still says "research preview").

**Opening (0-30s):** A face-cam intro: "Claude Code has become my default way of writing code", then pro tips "primarily based on this post by Boris Cherny, creator of Claude Code". A terminal-style "CLAUDE CODE Pro Tips" card sits in the corner. The promise is borrowed authority (the creator of the tool) plus speed ("pretty quickly"). The first tip starts at 0:23 with no further setup.

**Structure (creator chapters):**
- 0:00 Intro
- 0:24 CLI basics and command-line arguments
- 1:02 Images and screenshots
- 1:54 Automation with Puppeteer
- 2:09 MCP
- 2:55 Fetching URLs and documentation
- 3:23 CLAUDE.md
- 4:56 Slash commands
- 5:42 UI tips
- 6:21 Version control
- 7:31 Managing context
- 8:27 Managing cost

**Format:** Mostly face-cam. A numbered lower-third caption shows each tip ("1. Use CC as a bash CLI" ... "47. Upgrade to Claude Max"), but the numbers jump (1, 6, 8, 10, 12, 13, 16, 18...), so all 47 tips are never shown on screen. Short terminal clips from his Bluey Uno project and a Rails project, a CLAUDE.md in an editor, the Anthropic Console prompt improver, the GitHub MCP repo page, and a Datadog blog post.

**Teaching:**
1. Treat Claude Code as an ordinary bash CLI:
   - pass arguments at launch
   - run `claude -p "..."` for headless mode
   - pipe data in and chain it with other tools
   - run several instances in parallel. Subagents (the "Task" tool) are Claude Code launching Claude Code.
2. Images:
   - Drag an image file into the terminal.
   - Or take a screenshot to the clipboard with Cmd+Shift+Ctrl+4 (the key glyphs ⌘⇧^4 are shown on screen only) and paste it with **Ctrl+V**, not Cmd+V.
   - Use images in two ways: (a) paste a mockup and ask Claude to build it; (b) close the loop by screenshotting what it built and feeding that back for iteration.
3. Automate that loop by having an MCP browser server take screenshots of the running app and save them locally. On screen: `claude mcp list` and `claude mcp remove browserbase`. **Outdated:** the reference Puppeteer MCP server has since been archived. Today use Playwright MCP or the Claude in Chrome extension.
4. MCP:
   - Claude Code can act as an MCP client and also as an MCP server (`claude mcp serve`; the command is not shown in the video).
   - Examples: Postgres MCP to reach your database directly; API-wrapper servers (on screen, `/mcp` shows postgres, puppeteer and stripe, and the prompt "what's my current balance on stripe?" calls `stripe:retrieve_balance`); vendor doc servers such as Cloudflare.
5. Paste a URL and Claude fetches it. Use this for library docs (on screen: PydanticAI docs fetched into a todo plan) and for domain knowledge you would otherwise describe yourself. His example prompt, shown on screen: `write pseudo code to describe the rules of uno based on here: https://www.unorules.com/`. Claude wrote it to `uno_rules.txt` and then built the game from that file.
6. CLAUDE.md is loaded with every request. Put in it:
   - common bash commands
   - style and lint rules
   - how to run tests
   - repository etiquette

   The example shown on screen only:
   - `npm run test:wild-draw-four`
   - `npx eslint src/ --fix`
   - "Use Puppeteer MCP tools for browser testing and screenshots"
   - "DO NOT commit to main branch", "ALWAYS test before committing", feature branches named `feature/description`, "Run linter before commits", "All changes require PR review"
7. Run `/init` to generate CLAUDE.md from a scan of the repo.
8. Start a message with `#` to append a rule to CLAUDE.md (on screen: "# always use single responsibility principle when creating new methods" leads to "Saving project memory"). **Possibly outdated:** newer versions have dropped the `#` shortcut. Use `/memory` or ask Claude to "add this to CLAUDE.md". Check this on your version.
9. Where CLAUDE.md files live:
   - global `~/.claude/CLAUDE.md`, applied to every project
   - project root
   - subdirectories
10. Refactor CLAUDE.md often. It is a prompt sent on every turn, so cut duplicated and extra text and keep it specific. Optionally run it through Anthropic's prompt improver in the Console (shown on screen).
11. Custom slash commands are prompt files in `.claude/commands/`. Arguments are interpolated into them (the `$ARGUMENTS` placeholder is not named in the video). Example on screen: `/issue 39`, Boris's "fix GitHub issue" command. Other ideas: refactor, lint, review PR. **Note:** commands have since been folded into skills (`.claude/skills/`), though `.claude/commands/` still works.
12. Use Tab to autocomplete file and directory paths in prompts (on screen: `refactor src/game.js`). Naming exact files gives better results.
13. Press **Esc early and often** when Claude heads the wrong way, then ask it to undo its last turn. **Newer equivalent:** Esc Esc / `/rewind` restores checkpoints.
14. Version control is the main safety net against "it was working, then it got too ambitious":
   - ask Claude to commit after every major change
   - let it write commit messages
   - revert more often than you normally would: clear the conversation, `git` revert to the last good point, and retry with more specific instructions
15. Install the GitHub CLI (`gh`) and Claude will use it for PRs and code review. The GitHub MCP server is an alternative. **Outdated:** the frame shows a deprecation notice on the reference GitHub server; the official one is now github/github-mcp-server.
16. Context:
   - Watch the "Context left until auto-compact: 16%" indicator (shown on screen).
   - Compact early at natural breakpoints, for example right after a commit even at 35%.
   - Prefer `/clear` over compacting, and work so that a fresh session can pick up the task. Do this by having Claude plan in scratchpad files or GitHub issues (external memory).
17. Cost:
   - Smaller context means lower cost.
   - For team tracking, use Claude Code's OpenTelemetry support, for example sent to Datadog (Martin Amps' post).
   - His real advice is a Claude Max plan ($100 or $200). He spent about $150 of API-equivalent tokens in 3 days on the $100 plan. That is personal, and the prices are from May 2025.

**Demonstrated vs. said:**
- On screen, Claude keeps a todo list for multi-step tasks ("Update Todos", plus a tip banner: "Ask Claude to create a todo list when working on complex tasks"). He never says this.
- "auto-accept edits on (shift+tab to toggle)" is visible but never explained.
- He uses `uno_rules.txt` as an intermediate artifact: Claude fetches the URL, writes pseudo-code to a file, then codes against that file. This is a "distill to a file first" technique he doesn't name.
- His CLAUDE.md includes a tool-routing rule ("Use Puppeteer MCP tools for browser testing").

**Packaging:**
- The title "47 PRO TIPS in 9 minutes" promises density, and the number plus time box works.
- It under-delivers literally, because the on-screen numbering skips and only about 30 tips are actually covered.
- The caption has creator-made chapters and the source link, which is good for trust.
- No tags.
- Hard to fault, given the 18x view-to-subscriber ratio.

**Verdict:** USEFUL. It covers the most ground of the four (images, URL fetch, slash commands, git discipline, Esc/revert), but several specifics are outdated (`#` memory, Puppeteer MCP, research-preview UI), so check them against current docs.
