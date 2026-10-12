#!/usr/bin/env python3
"""Mix local chapter narration with the user's selected background music."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC_VERSION = "youtube-ADvyiXJOS-s-v2"
BGM = ROOT / ".audio-work/bgm/source.m4a"
SOURCE_URL = "https://www.youtube.com/watch?v=ADvyiXJOS-s"
MUSIC_TITLE = "深度睡眠，放松和治愈睡眠音乐（BGM）"


def mix(chapter):
    work = ROOT / ".audio-work" / f"{chapter:02d}"
    manifest = json.loads((work / "manifest.json").read_text())
    if manifest["status"] != "completed":
        raise ValueError("Complete chapter narration first")
    if not BGM.is_file():
        raise FileNotFoundError(
            "Download the user-selected BGM to .audio-work/bgm/source.m4a first"
        )
    duration = manifest["duration"]
    target = ROOT / "static/audio" / f"chapter-{chapter:02d}-mixed.mp3"
    temporary = target.with_suffix(".tmp.mp3")
    filters = (
        "[0:a]asplit=2[voice][control];"
        f"[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,loudnorm=I=-32:TP=-8:LRA=7,"
        f"volume=0.88,afade=t=in:d=3,afade=t=out:st={max(0, duration - 5)}:d=5[music];"
        "[music][control]sidechaincompress=threshold=0.025:ratio=4:attack=25:release=650[bed];"
        "[voice][bed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-18:TP=-2:LRA=9[out]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-i",
            str(ROOT / manifest["output"]),
            "-stream_loop",
            "-1",
            "-i",
            str(BGM),
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            "-metadata",
            f"title={manifest['source'].removesuffix('.md')} · 配乐版",
            "-metadata",
            "artist=guige",
            str(temporary),
        ],
        check=True,
        timeout=1200,
    )
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(temporary), "-f", "null", "-"],
        check=True,
        timeout=120,
    )
    temporary.replace(target)
    path = ROOT / "data/audio.json"
    catalog = json.loads(path.read_text())
    minutes, seconds = divmod(round(duration), 60)
    episode = dict(
        mixed=str(target.relative_to(ROOT / "static")),
        duration=f"{minutes}:{seconds:02d}",
        seconds=round(duration, 2),
        revision=hashlib.sha256(target.read_bytes()).hexdigest()[:16],
        music=MUSIC_TITLE,
        music_source=SOURCE_URL,
    )
    if manifest["output"].startswith("static/"):
        episode["voice"] = manifest["output"].removeprefix("static/")
    catalog[str(chapter)] = episode
    temporary_catalog = path.with_suffix(".tmp")
    temporary_catalog.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    )
    temporary_catalog.replace(path)
    (work / "mix.json").write_text(
        json.dumps(
            dict(
                episode=episode,
                music_version=MUSIC_VERSION,
                source_hash=manifest["source_hash"],
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(episode, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=int, nargs="?", default=1, choices=range(1, 30))
    mix(parser.parse_args().chapter)
