#!/usr/bin/env python3
"""Study videos from any yt-dlp-supported site (YouTube, Shorts, TikTok,
Instagram, X, LinkedIn, Facebook, Vimeo, Reddit, ~1800 more) or local files.

For each video, writes OUT/<platform>_<id>/:
  meta.json       platform, url, creator, caption, hashtags/tags, engagement,
                  duration, chapters, scene cuts, transcript source/language
  transcript.txt  timestamped; native captions when available, else local
                  whisper.cpp (free)
  frames/*.jpg    every 0.5s for 0-3s (the hook), one per chapter start, then
                  evenly spaced; count scales with duration. Name = timestamp.
Media is deleted afterwards unless --keep-media.

Playlist / channel / profile / Watch Later URLs are expanded into their
videos (capped by --max-items).

Usage:
  study.py OUT SOURCE [SOURCE ...]
  study.py OUT --links links.txt
"""
import argparse
import atexit
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

MODEL = Path(os.environ.get("SCROLL2SKILL_MODEL_DIR", Path.home() / ".local/share/whisper")) / \
    os.environ.get("SCROLL2SKILL_MODEL_NAME", "ggml-large-v3-turbo-q5_0.bin")  # same env vars as setup.sh
# setup.sh installs yt-dlp (pipx) and whisper-cli (source build) into ~/.local/bin on Linux;
# find them even when that directory is not on the caller's PATH yet.
_LOCAL_BIN = str(Path.home() / ".local" / "bin")
if _LOCAL_BIN not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + _LOCAL_BIN
VIDEO_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4a", ".mp3", ".opus", ".ogg", ".wav")


def run(cmd, **kw):
    # tools can emit invalid UTF-8 (whisper splits multi-byte characters across tokens): replace, never crash
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def safe(s: str, n: int = 60) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(s))[:n].strip("_") or "x"


TRACKING_PARAMS = re.compile(r"^(utm_\w+|si|igsh|igshid|mdxt|fbclid|gclid|feature|ref|ref_src|share_id|t|s)$", re.I)


def source_key(source: str) -> str:
    """Stable identity for a video across URL variants (tracking params, short links, /reel vs /p, host case)."""
    if is_local(source):
        return "local:" + str(Path(source).expanduser().resolve())
    pats = [
        (r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})", "youtube"),
        (r"instagram\.com/(?:[^/?#]+/)?(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", "instagram"),
        (r"tiktok\.com/.*/video/(\d+)", "tiktok"),
        (r"(?:twitter|x)\.com/[^/]+/status/(\d+)", "x"),
        (r"vimeo\.com/(?:video/)?(\d+)", "vimeo"),
    ]
    for pat, plat in pats:
        m = re.search(pat, source, re.I)  # host is case-insensitive; the captured ID keeps its case
        if m:
            return f"{plat}:{m.group(1)}"
    # Unknown site: lowercase scheme and host only, keep path case, drop only tracking parameters.
    # Erring towards distinct keys is safer: a duplicate study costs tokens, a wrong skip loses a video.
    u = urllib.parse.urlsplit(source.strip())
    query = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True) if not TRACKING_PARAMS.match(k)]
    return urllib.parse.urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path.rstrip("/"),
                                    urllib.parse.urlencode(query), ""))


def load_known(path: str | None) -> set[str]:
    """Keys of videos already studied (a skill's sources.json, or a previous index.json)."""
    if not path or not Path(path).expanduser().exists():
        return set()
    data = json.loads(Path(path).expanduser().read_text())
    items = data.get("videos", data) if isinstance(data, dict) else data
    keys = set()
    for it in items:
        if isinstance(it, str):
            keys.add(source_key(it))
        elif isinstance(it, dict):
            if it.get("key"):
                keys.add(it["key"])
            for k in ("url", "source"):
                if it.get(k):
                    keys.add(source_key(it[k]))
    return keys


def is_local(source: str) -> bool:
    return Path(source).expanduser().exists()


COOKIE_FILE = None


# yt-dlp hardening: ignore user/system config and plugins so a stray config can't change behaviour
# (idea from brenoepics/video-to-skill, MIT).
YTDLP = ["yt-dlp", "--ignore-config", "--no-plugin-dirs"]
_SNAPSHOTS: dict[tuple, str] = {}
COOKIE_DIR = Path.home() / ".cache" / "scroll2skill" / "cookies"


def _cookie_dir() -> Path:
    """Private 0700 folder for cookie copies. Copies older than a day (left by a killed run) are removed."""
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(COOKIE_DIR, 0o700)
    for old in COOKIE_DIR.glob("*.txt"):
        if time.time() - old.stat().st_mtime > 86400:
            old.unlink(missing_ok=True)
    return COOKIE_DIR


def _private_cookie_copy(src: str | None, browser: str, url: str) -> str:
    """Write cookies to a private temp file (0600, deleted when the run ends) and return its path.

    From a user cookies.txt: copy it, so yt-dlp never rewrites the user's file. From the browser
    store: export once, so there is a single Keychain prompt and every later call uses the copy
    (idea from Lum1104/video-to-skill). Raises with a clear message if nothing usable comes out."""
    if src and (not Path(src).is_file() or Path(src).stat().st_size == 0):
        raise RuntimeError(f"cookie file {src} is missing or empty")
    fd, path = tempfile.mkstemp(prefix="cookies-", suffix=".txt", dir=_cookie_dir())
    os.close(fd)
    os.chmod(path, 0o600)
    atexit.register(lambda: Path(path).unlink(missing_ok=True))
    if src:
        shutil.copyfile(src, path)
        return path
    r = run([*YTDLP, "--cookies-from-browser", browser, "--cookies", path,
             "--skip-download", "--flat-playlist", "--playlist-end", "1", url])
    if Path(path).stat().st_size == 0:
        Path(path).unlink(missing_ok=True)
        last = ((r.stderr or "").strip().splitlines() or ["no output"])[-1]
        raise RuntimeError(f"could not export cookies from {browser}: {last}")
    return path


def cookie_attempts(mode: str, browser: str, url: str = ""):
    """Yield yt-dlp cookie arguments lazily: the browser store is only touched if an anonymous try failed."""
    if COOKIE_FILE:
        key = ("file", COOKIE_FILE)
        _SNAPSHOTS[key] = _SNAPSHOTS.get(key) or _private_cookie_copy(COOKIE_FILE, browser, url)
        yield ["--cookies", _SNAPSHOTS[key]]
        return
    if mode in ("never", "auto"):
        yield []
    if mode in ("auto", "always"):
        key = ("browser", browser)
        _SNAPSHOTS[key] = _SNAPSHOTS.get(key) or _private_cookie_copy(None, browser, url)
        yield ["--cookies", _SNAPSHOTS[key]]


# ---------------------------------------------------------------- expansion
def expand(source: str, a) -> list[str]:
    """Return video URLs. Playlists/channels/profiles become their entries."""
    if is_local(source):
        p = Path(source).expanduser()
        if p.is_dir():
            found = sorted(str(f) for f in p.iterdir() if f.suffix.lower() in VIDEO_EXT)
            if not found:
                print(f"warning: no video/audio files in folder {p}", file=sys.stderr)
            return found or [f"EMPTY_FOLDER:{p}"]
        return [str(p)]
    for extra in cookie_attempts(a.cookies, a.browser, source):
        r = run([*YTDLP, *extra, "--flat-playlist", "-J",
                 "--playlist-end", str(a.max_items), source])
        if r.returncode == 0 and r.stdout.strip():
            info = json.loads(r.stdout)
            if info.get("_type") not in ("playlist", "multi_video"):
                return [source]
            urls = []
            for e in info.get("entries") or []:
                u = e.get("url") or e.get("webpage_url")
                if u and not u.startswith("http") and e.get("ie_key") == "Youtube":
                    u = f"https://www.youtube.com/watch?v={u}"
                if u:
                    urls.append(u)
            return urls[: a.max_items]
    return [source]  # let download() report the real error


# ---------------------------------------------------------------- download
def download(url: str, d: Path, a) -> tuple[Path, dict, Path | None]:
    base = ["--no-playlist", "--no-progress", "--write-info-json",
            "-S", f"res:{a.max_res},ext:mp4:m4a", "--merge-output-format", "mp4",
            "--write-subs", "--write-auto-subs", "--sub-format", "vtt",
            "--sub-langs", a.sub_langs, "--ignore-errors",
            # mark (not cut) sponsor/intro/outro segments so timestamps stay on the original timeline
            "--sponsorblock-mark", "sponsor,intro,outro,selfpromo",
            "-o", str(d / "video.%(ext)s"), url]
    err = "unknown error"
    for extra in cookie_attempts(a.cookies, a.browser, url):
        for _ in range(2):  # one retry, only for YouTube's transient 403s
            for leftover in d.glob("video*"):  # never accept a file from a failed earlier attempt
                leftover.unlink(missing_ok=True)
            r = run([*YTDLP, *extra, *base])
            vids = [p for p in d.glob("video.*") if p.suffix.lower() in VIDEO_EXT]
            if vids:
                info = {}
                ip = d / "video.info.json"
                if ip.exists():
                    info = json.loads(ip.read_text())
                    ip.unlink()
                return vids[0], info, pick_sub(list(d.glob("video*.vtt")), info.get("language"))
            lines = [l for l in (r.stderr or r.stdout).splitlines() if "ERROR" in l]
            err = (lines or (r.stderr or r.stdout).strip().splitlines() or [err])[-1]
            if "403" not in err:
                break
    hint = ""
    if re.search(r"log(ged)?[- ]in|cookies|private|sign in|not a bot|rate.?limit|login", err, re.I):
        hint = " [NEEDS LOGIN: ask the user before retrying with --cookie-file or --cookies]"
    raise RuntimeError(f"download failed: {err}{hint}")


def pick_sub(subs: list[Path], video_lang: str | None) -> Path | None:
    """Original-language captions first; never a machine translation if avoidable."""
    def lang_of(p: Path) -> str:
        m = re.search(r"video\.(.+)\.vtt$", p.name)
        return m.group(1) if m else ""
    vl = (video_lang or "").split("-")[0].lower()
    def rank(p: Path) -> int:
        l = lang_of(p).lower()
        base, orig = l.split("-")[0], l.endswith("-orig")
        if "live_chat" in l:
            return 99
        # YouTube's AI dubbing adds an "-orig" auto-caption track for every dubbed language,
        # so "-orig" alone does not mean "the language actually spoken": match the video's language.
        if vl and base == vl:
            return 0 if orig else 1
        if not vl and orig:
            return 2 if base == "en" else 3
        if not vl and base == "en":
            return 4
        return 50  # likely a translation or a dub
    subs = sorted(subs, key=rank)
    return subs[0] if subs and rank(subs[0]) < 50 else None


def vtt_to_lines(vtt: Path) -> str:
    """Collapse VTT (including YouTube's rolling auto-captions) to [MM:SS] lines."""
    out, last = [], ""
    ts = None
    for raw in vtt.read_text(errors="ignore").splitlines():
        m = re.match(r"(\d+):(\d\d):(\d\d)\.\d+ -->", raw) or re.match(r"(\d\d):(\d\d)\.\d+ -->", raw)
        if m:
            g = [int(x) for x in m.groups()]
            secs = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 3 else g[0] * 60 + g[1]
            ts = f"{secs // 60:02d}:{secs % 60:02d}"
            continue
        line = re.sub(r"<[^>]+>", "", raw).strip()
        if not line or ts is None or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if line == last or (out and out[-1].endswith(line)):
            continue
        out.append(f"[{ts}] {line}")
        last = line
    return "\n".join(out)


# ---------------------------------------------------------------- analysis
def probe(video: Path) -> tuple[float, bool]:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", str(video)])
    try:
        j = json.loads(r.stdout)
    except json.JSONDecodeError:
        return 0.0, False
    has_video = any(s.get("codec_type") == "video" for s in j.get("streams", []))
    return float(j.get("format", {}).get("duration") or 0), has_video


def scene_cuts(video: Path, threshold: float = 0.3) -> list[float]:
    # downscale first so this stays fast on long videos
    r = run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf",
             f"scale=160:-2,select='gt(scene,{threshold})',showinfo",
             "-an", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def default_rest(dur: float) -> int:
    if dur <= 90:
        return 16
    if dur <= 600:
        return 24
    if dur <= 1800:
        return 28
    return 32


def frame_times(dur: float, rest: int, chapters: list[float]) -> list[float]:
    times = {t / 2 for t in range(0, 7) if t / 2 < dur}  # hook: 0..3s
    ch = [c for c in chapters if 3 < c + 1 < dur]
    if len(ch) > 12:  # cap chapter frames, keep them spread out
        ch = [ch[round(i * (len(ch) - 1) / 11)] for i in range(12)]
    times |= {round(c + 1, 2) for c in ch}  # 1s into each chapter
    if dur > 3.5 and rest > 0:
        step = (dur - 3.0) / (rest + 1)
        times |= {round(3.0 + step * (i + 1), 2) for i in range(rest)}
    return sorted(times)


def extract_frames(video: Path, times: list[float], fdir: Path, width: int) -> list[str]:
    fdir.mkdir(exist_ok=True)
    out = []
    for t in times:
        p = fdir / f"t{int(t // 60):03d}m{t % 60:05.2f}s.jpg"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t),
             "-i", str(video), "-frames:v", "1", "-vf", f"scale={width}:-2",
             "-q:v", "4", str(p)])
        if p.exists():
            out.append(p.name)
    return out


VAD_MODEL = MODEL.parent / "ggml-silero-v5.1.2.bin"


def whisper(video: Path, d: Path, prompt: str = "") -> tuple[str, str]:
    if not shutil.which("whisper-cli") or not MODEL.exists():
        return "", f"unavailable (brew install whisper-cpp; model at {MODEL})"
    wav = d / "audio.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    if not wav.exists():
        return "", "no audio track"
    # Hallucination guards (values from brenoepics/video-to-skill, MIT): a stricter entropy
    # threshold catches repetition loops, a short context stops one bad window poisoning the
    # next, and non-speech tokens are suppressed. The title primes names and jargon.
    cmd = ["whisper-cli", "-m", str(MODEL), "-l", "auto", "-f", str(wav),
           "-et", "2.8", "-mc", "64", "-sns", "-oj", "-of", str(d / "whisper"), "-np"]
    if prompt:
        cmd += ["--prompt", prompt[:160]]
    if VAD_MODEL.exists():
        cmd += ["--vad", "-vm", str(VAD_MODEL)]
    r = run(cmd)
    wav.unlink(missing_ok=True)
    jp = d / "whisper.json"
    if not jp.exists():
        return "", "whisper failed: " + ((r.stderr or "?").strip().splitlines() or ["?"])[-1]
    data = json.loads(jp.read_text(encoding="utf-8", errors="replace"))
    jp.unlink()
    segs = []
    for seg in data.get("transcription", []):
        t = seg["timestamps"]["from"]  # HH:MM:SS,mmm
        h, m, s = int(t[0:2]), int(t[3:5]), int(t[6:8])
        text = seg["text"].strip()
        if text:
            segs.append((f"[{h * 60 + m:02d}:{s:02d}]", text))
    return "\n".join(f"{ts} {tx}" for ts, tx in dedupe_segments(segs)), data.get("result", {}).get("language", "?")


def dedupe_segments(segs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop a segment that is a cut-off start of the next one (VAD window splits can emit
    "...expiry 2 \ufffd" and then the full sentence)."""
    out = []
    for i, (ts, tx) in enumerate(segs):
        stem = tx.rstrip("\ufffd ").strip()
        nxt = segs[i + 1][1] if i + 1 < len(segs) else ""
        if "\ufffd" in tx and len(stem) >= 8 and norm_text(nxt).startswith(norm_text(stem)[: max(8, len(norm_text(stem)) // 2)]):
            continue
        out.append((ts, tx.replace("\ufffd", "")))
    return out



# ---------------------------------------------------------------- cost reduction
CACHE = Path.home() / ".cache" / "scroll2skill"


def ocr_frames(paths: list[Path]) -> dict[str, str]:
    """On-screen text per frame. macOS: Apple Vision (compiled once). Else tesseract. Else empty."""
    if not paths:
        return {}
    if sys.platform == "darwin" and shutil.which("swiftc"):
        binp = CACHE / "ocr"
        src = Path(__file__).with_name("ocr.swift")
        if not binp.exists() or binp.stat().st_mtime < src.stat().st_mtime:
            CACHE.mkdir(parents=True, exist_ok=True)
            r = run(["swiftc", "-O", str(src), "-o", str(binp)])
            if r.returncode != 0:
                print("warning: OCR helper failed to compile: " + r.stderr[-300:], file=sys.stderr)
        if binp.exists():
            r = run([str(binp), *map(str, paths)])
            try:
                return {Path(k).name: v for k, v in json.loads(r.stdout or "{}").items()}
            except json.JSONDecodeError:
                pass
    if shutil.which("tesseract"):
        res = {}
        for p in paths:
            r = run(["tesseract", str(p), "-", "--psm", "11"])
            res[p.name] = " / ".join(l.strip() for l in r.stdout.splitlines() if len(l.strip()) > 1)
        return res
    return {}


def _gray(p: Path, w: int, h: int) -> bytes:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(p),
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    return r.stdout


def thumb(p: Path) -> bytes:
    return _gray(p, 24, 24)


def dhash(p: Path) -> int | None:
    """64-bit difference hash: is each pixel brighter than its right neighbour (9x8 gray)."""
    px = _gray(p, 9, 8)
    if len(px) != 72:
        return None
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (px[row * 9 + col] > px[row * 9 + col + 1])
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def norm_text(t: str) -> str:
    """Letters and digits in any script (Hindi, Arabic, CJK...), case-folded; punctuation and spaces dropped."""
    return re.sub(r"[\W_]+", "", t.casefold())


def text_similar(a: str, b: str, min_ratio: float = 0.9) -> bool:
    """Same on-screen text, tolerant of OCR noise, but strict about numbers.

    Character-level similarity absorbs OCR typos ("profitab1e"); standalone numbers must match
    exactly, because a changed step number, price or count is a real change."""
    na, nb = norm_text(a), norm_text(b)
    if not na and not nb:
        return True
    if re.findall(r"\b\d+(?:[.,]\d+)?\b", a) != re.findall(r"\b\d+(?:[.,]\d+)?\b", b):
        return False
    return difflib.SequenceMatcher(None, na, nb).ratio() >= min_ratio


def dedupe(frames: list[str], fdir: Path, ocr: dict[str, str], thr: float) -> tuple[list[str], dict]:
    """Drop a frame only when it matches a kept frame both visually and in on-screen text.

    Visual match = close difference hash AND small mean pixel change (the hash alone treats any two
    flat colours as equal). Two levels, after Lum1104/video-to-skill (MIT): strict against the
    previous kept frame, looser against the last 3 kept frames within 2 seconds."""
    kept, dropped, info = [], {}, []  # info: (name, time, dhash, thumb, text)
    for f in frames:
        p = fdir / f
        cur = (f, frame_time(f), dhash(p), thumb(p), ocr.get(f, ""))
        dup_of = None
        for i, prev in enumerate(reversed(info[-3:])):
            if cur[2] is None or prev[2] is None or not cur[3] or len(cur[3]) != len(prev[3]):
                continue
            pix = sum(abs(x - y) for x, y in zip(cur[3], prev[3])) / len(cur[3])
            ham = hamming(cur[2], prev[2])
            strict = i == 0 and ham <= 3 and pix < thr
            near = cur[1] - prev[1] <= 2.0 and ham <= 5 and pix < thr * 1.5
            if (strict or near) and text_similar(cur[4], prev[4]):
                dup_of = prev[0]
                break
        if dup_of:
            dropped[f] = dup_of
            continue
        kept.append(f)
        info.append(cur)
    return kept, dropped


def frame_time(name: str) -> float:
    m = re.match(r"t(\d+)m([\d.]+)s", name)
    return int(m.group(1)) * 60 + float(m.group(2)) if m else 0.0


def contact_sheets(frames: list[str], fdir: Path, d: Path, cols: int, rows: int,
                   cell_w: int, prefix: str) -> list[dict]:
    """Tile frames into grids (read left to right, top to bottom). One image read per sheet."""
    sheets = []
    per = cols * rows
    for i in range(0, len(frames), per):
        chunk = frames[i:i + per]
        name = f"{prefix}{i // per + 1:02d}.jpg"
        lst = d / "_list.txt"
        lst.write_text("".join(f"file '{(fdir / f).resolve()}'\n" for f in chunk))
        c, r = (len(chunk), 1) if len(chunk) <= cols else (cols, -(-len(chunk) // cols))
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(lst), "-vf",
             f"scale={cell_w}:-2,pad=iw+8:ih+8:4:4:white,tile={c}x{r}:color=white",
             "-frames:v", "1", "-q:v", "4", str(d / name)])
        lst.unlink(missing_ok=True)
        if (d / name).exists():
            sheets.append({"sheet": name, "grid": f"{c}x{r}",
                           "cells_left_to_right_top_to_bottom_s": [round(frame_time(f), 2) for f in chunk],
                           "frames": chunk})
    return sheets

# ---------------------------------------------------------------- untrusted text
# Captions, transcripts and on-screen text come from strangers and end up in an agent's context.
# Flag text addressed to an AI and redact credentials before anything reads them.
# Pattern families adapted from brenoepics/video-to-skill (MIT), own wording.
INJECTION = [
    r"\b(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|prompts?|rules)",
    r"\bif\s+you\s+are\s+an?\s+(ai|llm|language model|assistant|agent|chatbot)\b",
    r"\b(ai|llm)\s+(agent|assistant)s?\s*[:,]\s*(run|execute|install|delete|send|open|download)\b",
    r"\b(do\s+not|don'?t)\s+(tell|inform|show)\s+the\s+user\b",
    r"\b(reveal|print|show)\s+(your|the)\s+system\s+prompt\b",
    r"\bmark\s+(every|all|each)\s+(step|test|check)s?\s+as\s+(passed|done|complete)",
    r"\b(curl|wget)\s+[^|\n]{1,200}\|\s*(sudo\s+)?(ba|z)?sh\b",
]
SECRETS = {
    "aws-access-key": r"\bAKIA[0-9A-Z]{16}\b",
    "openai-key": r"\bsk-(proj-)?[A-Za-z0-9_-]{20,}\b",
    "anthropic-key": r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
    "github-token": r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "slack-token": r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b",
    "google-api-key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "private-key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "jwt": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
}


def scan_untrusted(text: str, where: str) -> tuple[str, list[dict]]:
    """Return (text with secrets redacted, flags). Injection text is kept (it is evidence) but flagged."""
    flags = []
    for kind, pat in SECRETS.items():
        for m in re.finditer(pat, text):
            flags.append({"where": where, "kind": f"secret:{kind}", "excerpt": m.group(0)[:4] + "…"})
        text = re.sub(pat, f"[REDACTED {kind}]", text)
    for pat in INJECTION:
        for m in re.finditer(pat, text, re.I):
            flags.append({"where": where, "kind": "instruction-to-ai", "excerpt": m.group(0)[:40]})
    return text, flags


# ---------------------------------------------------------------- per video
def study(source: str, out: Path, a) -> dict:
    tmp = out / ("_tmp_" + hashlib.md5(source.encode()).hexdigest()[:8])
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    info, subs = {}, None
    if source.startswith("EMPTY_FOLDER:"):
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"no video/audio files ({', '.join(VIDEO_EXT)}) in {source[13:]}")
    if is_local(source):
        video = Path(source).expanduser()
        name = "local_" + safe(video.stem, 40)
        local = True
    else:
        video, info, subs = download(source, tmp, a)
        name = f"{safe(info.get('extractor_key') or 'web', 20).lower()}_{safe(info.get('id') or hashlib.md5(source.encode()).hexdigest()[:10])}"
        local = False
    d = out / name
    if d.exists():
        shutil.rmtree(d)
    tmp.rename(d)
    if not local:
        video = d / video.name
        subs = d / subs.name if subs else None

    dur, has_video = probe(video)
    if a.max_duration and dur > a.max_duration:
        raise RuntimeError(f"too long ({dur/60:.0f} min > --max-duration {a.max_duration/60:.0f} min); "
                           "rerun with a higher --max-duration or trim with a local file")
    chapters = [round(c.get("start_time", 0), 2) for c in info.get("chapters") or []]
    frames, cuts, kept, dropped, sheets, ocr, flags_ocr = [], [], [], {}, [], {}, []
    if has_video:
        rest = a.rest_frames if a.rest_frames is not None else default_rest(dur)
        frames = extract_frames(video, frame_times(dur, rest, chapters), d / "frames", a.width)
        cuts = scene_cuts(video)
        fdir = d / "frames"
        ocr = {} if a.no_ocr else ocr_frames([fdir / f for f in frames])
        kept, dropped = (frames, {}) if a.no_dedupe else dedupe(frames, fdir, ocr, a.dedupe_threshold)
        if not a.no_sheets:
            hook = [f for f in kept if frame_time(f) <= 3.0]
            body = [f for f in kept if frame_time(f) > 3.0]
            sheets = contact_sheets(hook, fdir, d, 4, 2, a.hook_cell, "sheet_hook_")
            sheets += contact_sheets(body, fdir, d, 3, 2, a.body_cell, "sheet_body_")
        flags_ocr = []
        for f in list(ocr):
            ocr[f], fl = scan_untrusted(ocr[f], f"onscreen {f}")
            flags_ocr += fl
        if ocr:
            (d / "onscreen_text.txt").write_text("\n".join(
                f"[{int(frame_time(f) // 60):02d}:{frame_time(f) % 60:05.2f}] {ocr.get(f, '') or '(no text)'}"
                for f in kept) + "\n")

    transcript, lang, tsource = "", "?", "none"
    if subs and a.transcript != "whisper":
        transcript = vtt_to_lines(subs)
        m = re.search(r"\.([A-Za-z-]+)\.vtt$", subs.name)
        lang, tsource = (m.group(1) if m else "?"), "native captions"
    if not transcript and a.transcript != "captions":
        transcript, lang = whisper(video, d, info.get("title") or "")
        tsource = "whisper.cpp" if transcript else f"none ({lang})"
    for v in d.glob("video*.vtt"):
        v.unlink()
    transcript, flags_tr = scan_untrusted(transcript, "transcript")
    (d / "transcript.txt").write_text((transcript or "(no speech detected)") + "\n")

    desc, flags_cap = scan_untrusted(info.get("description") or "", "caption")
    title, fl = scan_untrusted(info.get("title") or "", "title"); flags_cap += fl
    tags = []
    for t in info.get("tags") or []:
        t2, fl = scan_untrusted(str(t), "tags"); tags.append(t2); flags_cap += fl
    chapters_meta = []
    for c in info.get("chapters") or []:
        ct, fl = scan_untrusted(str(c.get("title") or ""), "chapters"); flags_cap += fl
        chapters_meta.append({"start_s": round(c.get("start_time", 0), 1), "title": ct})
    meta = {
        "source": source,
        "platform": info.get("extractor_key") or ("local" if local else None),
        "url": info.get("webpage_url") or source,
        "creator": info.get("uploader") or info.get("channel") or info.get("creator") or info.get("uploader_id"),
        "creator_url": info.get("uploader_url") or info.get("channel_url"),
        "followers": info.get("channel_follower_count"),
        "title": title,
        "caption": desc,
        "hashtags": sorted(set(re.findall(r"#\w+", desc + " " + title))),
        "tags": tags,
        "categories": info.get("categories"),
        "upload_date": info.get("upload_date"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "comments": info.get("comment_count"),
        "reposts": info.get("repost_count"),
        "audio_track": " - ".join(x for x in (info.get("artist"), info.get("track")) if x) or None,
        "duration_s": round(dur, 2),
        "format": "short" if dur <= 90 else ("medium" if dur <= 1200 else "long"),
        "vertical": (info.get("height") or 0) > (info.get("width") or 0) if info.get("width") else None,
        "chapters": chapters_meta,
        "scene_cuts_s": cuts,
        "cuts_per_10s": round(len(cuts) / dur * 10, 2) if dur and has_video else None,
        "first_cut_s": cuts[0] if cuts else None,
        "transcript_source": tsource,
        "transcript_language": lang,
        "frames": frames,
        "frames_kept": kept,
        "duplicates_dropped": dropped,
        "sheets": sheets,
        "ocr": "apple-vision" if (ocr and sys.platform == "darwin") else ("tesseract" if ocr else "none"),
        "sponsor_segments": [{"start_s": round(c.get("start_time", 0), 1), "end_s": round(c.get("end_time", 0), 1),
                              "category": c.get("category")} for c in info.get("sponsorblock_chapters") or []],
        "untrusted_flags": flags_cap + flags_tr + flags_ocr,
        "key": source_key(info.get("webpage_url") or source),
    }
    if meta["likes"] and meta["comments"] is not None:
        meta["comments_per_100_likes"] = round(meta["comments"] / meta["likes"] * 100, 2)
    if meta["views"] and meta["likes"] is not None:
        meta["likes_per_100_views"] = round(meta["likes"] / meta["views"] * 100, 2)
    (d / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    if not local and not a.keep_media:
        video.unlink(missing_ok=True)
    return {"dir": str(d), "platform": meta["platform"], "duration_s": meta["duration_s"],
            "frames": len(frames), "kept": len(kept), "sheets": len(sheets), "cuts": len(cuts),
            "untrusted_flags": len(meta["untrusted_flags"]), "key": meta["key"], "transcript": tsource, "language": lang}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("sources", nargs="*", help="URLs, playlist/channel/profile URLs, files, or folders")
    ap.add_argument("--links", help="file with one source per line (# comments ok)")
    ap.add_argument("--cookies", choices=["auto", "always", "never"], default="never",
                    help="never (default). auto/always read the browser's cookie store, which on "
                         "macOS needs the 'Chrome Safe Storage' Keychain key and exposes every "
                         "site's session to yt-dlp. Only use after the user agrees. Safer: --cookie-file")
    ap.add_argument("--browser", default="chrome", help="chrome, safari, firefox, brave, edge, arc...")
    ap.add_argument("--max-items", type=int, default=15, help="cap per playlist/channel (default 15)")
    ap.add_argument("--max-duration", type=float, default=3600, help="skip videos longer than N seconds (0 = no cap)")
    ap.add_argument("--max-res", type=int, default=720)
    ap.add_argument("--rest-frames", type=int, default=None, help="frames after the hook (default scales with length)")
    ap.add_argument("--width", type=int, default=540)
    ap.add_argument("--transcript", choices=["auto", "captions", "whisper"], default="auto")
    ap.add_argument("--sub-langs", default=".*-orig,en,en-.*", help="yt-dlp caption languages to try")
    ap.add_argument("--cookie-file", help="Netscape cookies.txt for just the needed site(s); "
                    "preferred over --cookies (no Keychain access, scoped to that site)")
    ap.add_argument("--keep-media", action="store_true")
    ap.add_argument("--skip-known", help="JSON of videos already studied (a skill's sources.json or an "
                    "index.json); matching videos are skipped so a rerun only studies new saves")
    ap.add_argument("--no-sheets", action="store_true", help="skip contact sheets (read frames one by one)")
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--no-dedupe", action="store_true")
    ap.add_argument("--dedupe-threshold", type=float, default=6.0, help="mean pixel diff (0-255) on 24x24 gray")
    ap.add_argument("--hook-cell", type=int, default=360, help="cell width in the hook sheet")
    ap.add_argument("--body-cell", type=int, default=360, help="cell width in body sheets")
    a = ap.parse_args()
    global COOKIE_FILE
    COOKIE_FILE = str(Path(a.cookie_file).expanduser()) if a.cookie_file else None
    if COOKIE_FILE and (not Path(COOKIE_FILE).is_file() or Path(COOKIE_FILE).stat().st_size == 0):
        sys.exit(f"error: cookie file {a.cookie_file} is missing or empty. Export cookies.txt for the site again.")

    for tool in ("yt-dlp", "ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"missing {tool}: brew install {'yt-dlp' if tool == 'yt-dlp' else 'ffmpeg'}")
    raw = list(a.sources)
    if a.links:
        raw += [l.strip() for l in Path(a.links).expanduser().read_text().splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
    if not raw:
        ap.error("no sources")
    sources = []
    for s in raw:
        try:
            sources += expand(s, a)
        except RuntimeError as e:  # e.g. browser cookie export failed: say so plainly, no traceback
            sys.exit(f"error: {e}")
    sources = list(dict.fromkeys(sources))
    known = load_known(a.skip_known)
    skipped = [s for s in sources if source_key(s) in known]
    sources = [s for s in sources if source_key(s) not in known]
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    results = [{"source": s, "ok": True, "skipped": "already studied", "key": source_key(s)} for s in skipped]
    for i, s in enumerate(sources, 1):
        print(f"[{i}/{len(sources)}] {s}", file=sys.stderr, flush=True)
        try:
            results.append({"source": s, "ok": True, **study(s, out, a)})
        except Exception as e:  # keep going past one bad video
            results.append({"source": s, "ok": False, "error": str(e), "key": source_key(s)})
        for t in out.glob("_tmp_*"):
            shutil.rmtree(t, ignore_errors=True)
    idx = out / "index.json"
    prev = json.loads(idx.read_text()) if idx.exists() else []
    merged = {r["source"]: r for r in prev}
    merged.update({r["source"]: r for r in results})
    idx.write_text(json.dumps(list(merged.values()), indent=2, ensure_ascii=False))
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
