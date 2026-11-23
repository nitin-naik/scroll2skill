#!/usr/bin/env bash
# End-to-end Linux check, fails on any broken step.
#   docker run --rm -v "$PWD":/repo:ro ubuntu:24.04 bash /repo/tests/linux-e2e.sh
# Required part is hermetic: it builds its own test video (spoken words + on-screen text),
# so it doesn't depend on YouTube. Set E2E_NETWORK=1 to also try a real YouTube download
# (reported, never required: cloud IPs are often bot-blocked).
set -euo pipefail

echo "== system packages"
apt-get update -qq >/dev/null
apt-get install -y -qq sudo curl git espeak-ng python3-pytest >/dev/null
id tester >/dev/null 2>&1 || useradd -m tester
echo "tester ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/tester
rm -rf /home/tester/scroll2skill && cp -r /repo /home/tester/scroll2skill && chown -R tester /home/tester/scroll2skill

cat > /home/tester/run.sh <<'INNER'
set -euo pipefail
cd ~/scroll2skill
export SCROLL2SKILL_MODEL_NAME="${SCROLL2SKILL_MODEL_NAME:-ggml-tiny.bin}"

echo "== setup.sh --yes (fresh machine)"
./setup.sh --yes
echo "== setup.sh --check"
./setup.sh --check

echo "== unit tests"
python3 -m pytest -q tests

echo "== build a test video: speech + on-screen text"
mkdir -p /tmp/e2e/in && cd /tmp/e2e
espeak-ng -w speech.wav "The quick brown fox jumps over the lazy dog. Hello from scroll2skill."
ffmpeg -loglevel error -y -f lavfi -i "color=c=white:s=720x1280:d=6" -i speech.wav \
  -vf "drawtext=text='SCROLL2SKILL TEST':fontsize=72:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2" \
  -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac in/clip.mp4

echo "== study.py on the local video"
python3 ~/scroll2skill/scroll2skill/scripts/study.py out in --transcript whisper > result.json
python3 - <<'PY'
import json, pathlib, sys
r = json.load(open("result.json"))
assert len(r) == 1 and r[0]["ok"], f"study failed: {r}"
d = pathlib.Path(r[0]["dir"])
meta = json.loads((d / "meta.json").read_text())
transcript = (d / "transcript.txt").read_text().lower()
onscreen = (d / "onscreen_text.txt").read_text().lower() if (d / "onscreen_text.txt").exists() else ""
checks = {
    "frames extracted": len(meta["frames"]) >= 5,
    "contact sheets built": len(meta["sheets"]) >= 1 and all((d / s["sheet"]).exists() for s in meta["sheets"]),
    "whisper transcript has the spoken words": "fox" in transcript and "dog" in transcript,
    "OCR read the on-screen text": "scroll2skill" in onscreen,
}
# informational only: dedupe is unit-tested directly; here it depends on codec noise
print(f"INFO dedupe kept {len(meta['frames_kept'])} of {len(meta['frames'])} frames")
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
if not all(checks.values()):
    print("transcript:", transcript[:200]); print("onscreen:", onscreen[:200]); sys.exit(1)
PY

if [ "${E2E_NETWORK:-0}" = 1 ]; then
  echo "== optional: real YouTube download"
  if python3 ~/scroll2skill/scroll2skill/scripts/study.py net "https://www.youtube.com/watch?v=jNQXAC9IVRw" \
       | python3 -c 'import json,sys; r=json.load(sys.stdin); sys.exit(0 if r[0]["ok"] else 1)'; then
    echo "PASS network download"
  else
    echo "SKIP network download failed (often bot-blocking on cloud IPs); not counted"
  fi
fi
echo "== ALL REQUIRED CHECKS PASSED"
INNER
chown tester /home/tester/run.sh
su - tester -c "E2E_NETWORK=${E2E_NETWORK:-0} SCROLL2SKILL_MODEL_NAME=${SCROLL2SKILL_MODEL_NAME:-ggml-tiny.bin} bash /home/tester/run.sh"
