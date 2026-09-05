"""Build the pixel-free bed: drop only tasks whose answer exists ONLY as pixels."""
import json
from pathlib import Path

SRC = Path(r"D:\PycharmProj\HarnessX\recipe\gaia_evolver\data\webthinker_gaia_dev.json")
DST = SRC.with_name("webthinker_gaia_dev_nopixel.json")
MANIFEST = SRC.with_name("webthinker_gaia_dev_nopixel.README.md")

# The criterion is narrow on purpose: the answer is carried by image or video
# pixels and by nothing else on the open web. A question that merely mentions a
# picture, or asks *about* a media object whose answer is written in text
# somewhere (caption, transcript, revision history, fan wiki), stays in.
DROP = {
    "7a4a336d-dcfa-45a0-b014-824c7619e8de":
        "the racetrack shown at the two-minute mark of a Let's Play video — the answer is a "
        "video frame; no transcript, description or wiki states which track is on screen then",
    "624cbf11-6a41-4692-af9c-36b3e5ca3130":
        "the rhyme on a headstone visible in the BACKGROUND of a photo — the answer is a "
        "region of one image, never transcribed anywhere",
    "0e9e85b8-52b9-4de4-b402-5f635ab9631f":
        "'the latest year date WRITTEN IN THE IMAGE on the webpage' — the question names the "
        "image as the medium of the answer",
}

# Deliberately kept, with the reason, so the line is auditable rather than a matter of taste:
KEPT_BORDERLINE = {
    "5f982798-16b9-4051-ab57-cfc7ebdb2a91":
        "asks for a time span shown in an arXiv figure, but arXiv papers state their measured "
        "spans in the caption and body text — a reading task, not a perception task",
    "d5141ca5-e7a0-469f-bf3e-e773507c86e2":
        "asks WHEN a picture was added to a Wikipedia page — answered by revision history, "
        "which is text and has an API",
    "0bdb7c40-671d-4ad1-9ce3-986b159c0ddc":
        "NASA Astronomy Picture of the Day — the explanation text under every APOD names what "
        "is in the frame; passes 9/12 today",
}

tasks = json.loads(SRC.read_text(encoding="utf-8"))
kept = [t for t in tasks if t["task_id"] not in DROP]
dropped = [t for t in tasks if t["task_id"] in DROP]
assert len(dropped) == len(DROP), f"expected {len(DROP)} drops, matched {len(dropped)}"
DST.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding="utf-8")

lines = [
    "# Pixel-free GAIA bed (100 tasks)",
    "",
    f"`{DST.name}` = `{SRC.name}` minus {len(DROP)} tasks whose answer exists only as pixels.",
    "",
    "## Why this exists",
    "",
    "Across M25's twelve batches, 14 of the 103 tasks never passed once. Classifying them by",
    "what actually blocks them: 3 need perception of an image or video frame, ~3 sit behind an",
    "access wall with a usable API, and 7 are fully reachable and fail on method. Only the first",
    "group is unreachable in principle for a text-only agent, and those three cost $60 over",
    "twelve rounds (11% of batch spend) at 18-19 steps each, buying nothing.",
    "",
    "Removing them is NOT a score edit dressed up as hygiene: 68.0% on 103 becomes ~70.7% on 100,",
    "a move smaller than this bed's own +/-5-task noise envelope. What it buys is that the",
    "evolution loop stops being told to solve them. The loop proposed an OCR tool twice (R5, R6)",
    "and a transcript tool once (R11), aiming its scarcest resource at the one direction with the",
    "smallest ceiling on the board.",
    "",
    "## Dropped",
    "",
]
for tid, why in DROP.items():
    q = next(t["Question"] for t in dropped if t["task_id"] == tid)
    lines += [f"- `{tid}` (L{next(t['Level'] for t in dropped if t['task_id']==tid)}) — {why}", f"  > {q[:200]}", ""]
lines += ["## Deliberately kept (borderline, stated so the line is auditable)", ""]
for tid, why in KEPT_BORDERLINE.items():
    lines.append(f"- `{tid}` — {why}")
lines += [
    "",
    "## Comparability",
    "",
    "Scores on this bed are NOT comparable to M22/M24/M25 or to the paper's 103-task numbers.",
    "Any cross-campaign claim must either restate the old runs on the same 100 tasks (their",
    "per-task ledgers make that a recount, not a re-run) or say plainly which bed it used.",
]
MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {DST.name}: {len(kept)} tasks (dropped {len(dropped)})")
print(f"wrote {MANIFEST.name}")
lv = {}
for t in kept:
    lv[t["Level"]] = lv.get(t["Level"], 0) + 1
print("levels:", dict(sorted(lv.items())))
