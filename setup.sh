#!/usr/bin/env bash
# scroll2skill setup: installs yt-dlp, ffmpeg, whisper.cpp and the speech model, then links the skill.
#   ./setup.sh            install what's missing (asks before installing)
#   ./setup.sh --check    report only, change nothing (exit 1 if something is missing)
#   ./setup.sh --yes      install without asking
# macOS (Homebrew) and Debian/Ubuntu (apt). Windows: use WSL.
set -euo pipefail
export PATH="$PATH:$HOME/.local/bin"   # where the Linux path installs yt-dlp and whisper-cli

MODEL_DIR="${SCROLL2SKILL_MODEL_DIR:-$HOME/.local/share/whisper}"
MODEL_NAME="${SCROLL2SKILL_MODEL_NAME:-ggml-large-v3-turbo-q5_0.bin}"   # the Linux E2E CI job uses ggml-tiny.bin (75 MB)
MODEL="$MODEL_DIR/$MODEL_NAME"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$MODEL_NAME"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$HERE/scroll2skill"
CHECK=0; YES=0
for a in "$@"; do case "$a" in --check) CHECK=1;; --yes|-y) YES=1;; esac; done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
miss() { printf '  \033[31m✗\033[0m %s\n' "$1"; MISSING=1; }
MISSING=0
OS="$(uname -s)"

echo "scroll2skill setup ($OS)"
command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
  && ok "python3 $(python3 -V | cut -d' ' -f2)" || miss "python3 >= 3.10"
for t in yt-dlp ffmpeg ffprobe; do command -v "$t" >/dev/null && ok "$t" || miss "$t"; done
command -v whisper-cli >/dev/null && ok "whisper-cli (whisper.cpp)" || miss "whisper-cli (whisper.cpp)"
[ -f "$MODEL" ] && ok "speech model $(du -h "$MODEL" | cut -f1)" || miss "speech model at $MODEL"
[ -f "$MODEL_DIR/ggml-silero-v5.1.2.bin" ] && ok "voice-activity model" || echo "  - voice-activity model missing (optional; setup downloads it)"
if [ "$OS" = Darwin ]; then
  command -v swiftc >/dev/null && ok "swiftc (on-screen text via Apple Vision)" \
    || echo "  - swiftc missing: on-screen text OCR off (xcode-select --install)"
else
  command -v tesseract >/dev/null && ok "tesseract (on-screen text)" \
    || echo "  - tesseract missing: on-screen text OCR off (optional)"
fi
for d in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  [ -e "$d/scroll2skill" ] && ok "skill linked in $d" || echo "  - not linked in $d"
done

if [ "$CHECK" = 1 ]; then exit "$MISSING"; fi
if [ "$MISSING" = 0 ]; then echo "All set."; else
  if [ "$YES" = 0 ]; then read -r -p "Install missing pieces? [y/N] " r; [[ "$r" =~ ^[Yy] ]] || exit 1; fi

  if [ "$OS" = Darwin ]; then
    command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
    pkgs=(); command -v yt-dlp >/dev/null || pkgs+=(yt-dlp)
    command -v ffmpeg >/dev/null || pkgs+=(ffmpeg)
    command -v whisper-cli >/dev/null || pkgs+=(whisper-cpp)
    [ ${#pkgs[@]} -eq 0 ] || brew install "${pkgs[@]}"
  elif command -v apt-get >/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq ffmpeg python3 python3-pip pipx git cmake build-essential curl tesseract-ocr
    command -v yt-dlp >/dev/null || { pipx install yt-dlp && pipx ensurepath; }
    if ! command -v whisper-cli >/dev/null; then
      src="$HOME/.local/src/whisper.cpp"
      [ -d "$src" ] || git clone --depth 1 https://github.com/ggml-org/whisper.cpp "$src"
      cmake -S "$src" -B "$src/build" -DCMAKE_BUILD_TYPE=Release >/dev/null
      cmake --build "$src/build" -j --config Release --target whisper-cli >/dev/null
      mkdir -p "$HOME/.local/bin" && ln -sf "$src/build/bin/whisper-cli" "$HOME/.local/bin/whisper-cli"
      echo "  whisper-cli built into ~/.local/bin (study.py finds it there automatically)"
    fi
  else
    echo "Unsupported system. Install yt-dlp, ffmpeg and whisper.cpp yourself, then rerun --check."; exit 1
  fi

  if [ ! -f "$MODEL" ]; then
    mkdir -p "$MODEL_DIR"
    echo "Downloading speech model $MODEL_NAME (large-v3-turbo is 547 MB)..."
    if ! curl -L --fail --progress-bar -o "$MODEL.part" "$MODEL_URL"; then
      rm -f "$MODEL.part"; echo "Model download failed: $MODEL_URL" >&2; exit 1
    fi
    mv "$MODEL.part" "$MODEL"
  fi
fi
# voice-activity model (864 KB): lets whisper skip silence and music instead of inventing words
VAD="$MODEL_DIR/ggml-silero-v5.1.2.bin"
if [ "$CHECK" = 0 ] && [ ! -f "$VAD" ]; then
  mkdir -p "$MODEL_DIR"
  curl -sL --fail -o "$VAD.part" "https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin" \
    && mv "$VAD.part" "$VAD" || { rm -f "$VAD.part"; echo "  - VAD model download failed (optional; whisper still works)"; }
fi

# link the skill for Claude Code, and for Codex if it is installed
link() { mkdir -p "$1"; [ -e "$1/scroll2skill" ] || { ln -s "$SKILL_SRC" "$1/scroll2skill"; echo "Linked skill into $1"; }; }
link "$HOME/.claude/skills"
command -v codex >/dev/null && link "$HOME/.agents/skills"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) [ "$OS" = Darwin ] || echo "Tip: add ~/.local/bin to PATH to run yt-dlp/whisper-cli yourself: echo 'export PATH=\$HOME/.local/bin:\$PATH' >> ~/.bashrc";; esac
echo "Done. In Claude Code: /scroll2skill <links or playlist> — or ask Codex to use the scroll2skill skill."
