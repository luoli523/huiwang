#!/usr/bin/env python3
"""Produce, inspect and resume the remaining episodes using local services only."""

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import narrate

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".audio-work/batch.json"


def save(state):
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(STATE_PATH)


def normalized(text):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", text).lower()


def inspect(chapter, manifest):
    source = (ROOT / "content/docs" / manifest["source"]).read_text()
    spoken = source.replace("T2次", "特快二次").replace("诺基亚6610", "诺基亚六六一零")
    title = f"第{chapter}章，" + Path(manifest["source"]).stem.split("-", 1)[1]
    expected = narrate.chunks(spoken, title)
    actual = [(s["text"], s["pause"]) for s in manifest["segments"]]
    if expected != actual:
        raise ValueError(
            f"Chapter {chapter}: spoken text does not cover current source"
        )
    work = ROOT / ".audio-work" / f"{chapter:02d}"
    candidates = [s for s in manifest["segments"][1:] if s["duration"] < 110]
    if not candidates:
        raise ValueError("No suitable excerpt for local transcription")
    reviews = []
    for name, segment in [("opening", candidates[0]), ("ending", candidates[-1])]:
        path = work / f"{name}-review.json"
        if path.exists():
            review = json.loads(path.read_text())
            if review.get("segment") == segment["file"]:
                reviews.append(review)
                continue
        boundary = uuid.uuid4().hex
        audio = (work / segment["file"]).read_bytes()
        body = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="excerpt.wav"\r\n'
                "Content-Type: audio/wav\r\n\r\n"
            ).encode()
            + audio
            + f"\r\n--{boundary}--\r\n".encode()
        )
        request = urllib.request.Request(
            narrate.BASE + "/v1/audio/transcriptions",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            transcription = json.loads(response.read())["text"]
        similarity = difflib.SequenceMatcher(
            None, normalized(segment["text"]), normalized(transcription), autojunk=False
        ).ratio()
        review = dict(
            segment=segment["file"],
            expected=segment["text"],
            transcription=transcription,
            similarity=round(similarity, 3),
        )
        path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
        reviews.append(review)
    # Transcription can confuse names/homophones; a low score requires inspection.
    if min(r["similarity"] for r in reviews) < 0.65:
        raise ValueError(
            f"Chapter {chapter}: inspect local transcript before publishing"
        )
    return dict(
        source_covered=True, excerpt_similarity=[r["similarity"] for r in reviews]
    )


def publish(chapters):
    subprocess.run(["hugo", "--minify"], cwd=ROOT, check=True)
    files = ["data/audio.json"] + [
        f"static/audio/chapter-{n:02d}-mixed.mp3" for n in chapters
    ]
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    if any(path not in files for path in staged):
        raise RuntimeError("Unrelated files are staged; inspect before publishing")
    subprocess.run(["git", "add", "--", *files], cwd=ROOT, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    title = f"feat: publish guige audio chapters {chapters[0]} through {chapters[-1]}"
    subprocess.run(["git", "commit", "-m", title], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    run = None
    for _ in range(12):
        data = subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                "gh-pages.yml",
                "--limit",
                "5",
                "--json",
                "databaseId,headSha",
            ],
            cwd=ROOT,
            text=True,
        )
        run = next((r for r in json.loads(data) if r["headSha"] == head), None)
        if run:
            break
        time.sleep(5)
    if run is None:
        raise RuntimeError("Pages deployment was not found")
    subprocess.run(
        [
            "gh",
            "run",
            "watch",
            str(run["databaseId"]),
            "--exit-status",
            "--interval",
            "10",
        ],
        cwd=ROOT,
        check=True,
        timeout=1200,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, default=2)
    parser.add_argument("--last", type=int, default=29)
    parser.add_argument(
        "--publish-every",
        type=int,
        default=0,
        help="Publish each N inspected chapters (0: local only)",
    )
    args = parser.parse_args()
    if not 2 <= args.first <= args.last <= 29:
        parser.error("Chapter range must be between 2 and 29")
    voice_version = json.loads((ROOT / ".audio-work/01/manifest.json").read_text())[
        "voice_version"
    ]
    state = (
        json.loads(STATE_PATH.read_text())
        if STATE_PATH.exists()
        else dict(voice_version=voice_version, chapters={})
    )
    if state["voice_version"] != voice_version:
        raise ValueError("Batch reference differs from the approved first episode")
    state.update(status="running", last_started=time.time())
    save(state)
    pending_publish = []
    for chapter in range(args.first, args.last + 1):
        source = next((ROOT / "content/docs").glob(f"{chapter}-*.md"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        episode = state["chapters"].get(str(chapter), {})
        output = ROOT / "static/audio" / f"chapter-{chapter:02d}-mixed.mp3"
        if (
            episode.get("status") == "completed"
            and episode.get("source_hash") == digest
            and output.exists()
        ):
            print(f"CHAPTER {chapter}: completed, reusing", flush=True)
            if args.publish_every and not episode.get("published"):
                pending_publish.append(chapter)
                if len(pending_publish) >= args.publish_every or chapter == args.last:
                    publish(pending_publish)
                    for n in pending_publish:
                        state["chapters"][str(n)]["published"] = time.time()
                    pending_publish.clear()
                    save(state)
            continue
        episode = dict(status="generating", source_hash=digest, started=time.time())
        state["chapters"][str(chapter)] = episode
        state["current"] = chapter
        save(state)
        print(f"CHAPTER {chapter}: generating {source.stem}", flush=True)
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/narrate.py"),
                    str(chapter),
                    "--archive-voice",
                    "--voice-version",
                    voice_version,
                ],
                check=True,
            )
            episode["status"] = "mixing"
            save(state)
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/mix-chapter.py"), str(chapter)],
                check=True,
            )
            episode["status"] = "inspecting"
            save(state)
            manifest = json.loads(
                (ROOT / ".audio-work" / f"{chapter:02d}" / "manifest.json").read_text()
            )
            review = inspect(chapter, manifest)
            episode.update(
                status="completed",
                duration=manifest["duration"],
                review=review,
                completed=time.time(),
            )
            save(state)
            print(
                f"CHAPTER {chapter}: ready ({manifest['duration']:.1f}s), review={review}",
                flush=True,
            )
            pending_publish.append(chapter)
            if args.publish_every and (
                len(pending_publish) >= args.publish_every or chapter == args.last
            ):
                state["status"] = "publishing"
                save(state)
                publish(pending_publish)
                for n in pending_publish:
                    state["chapters"][str(n)]["published"] = time.time()
                pending_publish.clear()
                state["status"] = "running"
                save(state)
        except Exception as exc:
            episode.update(status="failed", error=str(exc))
            state["status"] = "failed"
            save(state)
            raise
    state["status"] = "completed"
    state["completed"] = time.time()
    save(state)
    print("BATCH COMPLETE", flush=True)


if __name__ == "__main__":
    main()
