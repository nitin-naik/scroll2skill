# Token costs, as measured

Every number below is the `subagent_tokens` total that Claude Code reported when that subagent finished (Claude Opus, 2026-11-20). The fixed startup cost depends on the setup: this machine had many MCP servers and skills installed, so a leaner setup costs less.

## Fixed cost of a subagent

| Run | Tokens |
|---|---|
| Empty subagent ("reply ok", no tools) | 39,654 |

## Reading frames: one by one vs contact sheets + OCR (same 89 s reel, same brief)

| Method | Tokens | Tool calls | Time | Work after subtracting fixed cost |
|---|---|---|---|---|
| 23 frames read one at a time | 72,787 | 27 | 85 s | ~33k |
| 4 contact sheets + OCR text | 63,794 | 7 | 60 s | ~24k |

## Study step of the demo (8 YouTube videos, 80 min)

| Batch | Videos | Tokens |
|---|---|---|
| 1 | 2 long talks (17 + 20 min) | 110,956 |
| 2 | 2 practitioner videos (13 + 10 min) | 92,963 |
| 3 | 4 shorter videos (9 + 3 + 3 + 3.5 min) | 100,583 |
| **Total** | **8** | **304,502** (≈ 38k per video) |

## Testing the three skills

| Run | Tokens |
|---|---|
| Round 1 cold tests with friction logs (audit / loop / delegation) | 56,377 / 52,222 / 54,373 |
| Plain-Claude baseline (all three tasks, one agent) | 56,919 |
| Round 1 blind judge | 72,119 |
| Round 2 cold tests (audit / loop / delegation) | 62,728 / 53,794 / 57,273 |
| Round 2 blind judge | 78,882 |
| **Total** | **≈ 545k** |
