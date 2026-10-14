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
    cues = json.loads((ROOT / "data/audio-cues.json").read_text())
    cue = cues.get(str(chapter))
    extra_inputs = []
    music_filter = ""
    music_label = "music"
    if cue:
        if cue["source_hash"] != manifest["source_hash"]:
            raise ValueError("Chapter text changed; realign its music cue first")
        song = ROOT / cue["file"]
        if not song.is_file():
            raise FileNotFoundError(f"Download {cue['source']} to {song} first")
        fade = cue["fade_seconds"]
        start = cue["chapter_start"] - fade
        if not (0 <= start < duration - 5 and cue["source_start"] >= fade > 0):
            raise ValueError("Music cue is outside the narration timeline")
        extra_inputs = ["-ss", str(cue["source_start"] - fade), "-i", str(song)]
        # Start the fade two seconds before the lyric; singing at source 43s
        # then arrives exactly at the first spoken lyric. Keep it to the ending.
        music_filter = (
            f"[music]volume='if(lt(t,{start}),1,"
            f"max(0,1-(t-{start})/{fade}))':eval=frame[original];"
            f"[2:a]atrim=duration={duration - start},asetpts=PTS-STARTPTS,"
            "loudnorm=I=-29:TP=-8:LRA=7,"
            f"afade=t=in:d={fade},afade=t=out:st={duration - start - 5}:d=5,"
            f"adelay={round(start * 1000)}:all=1[song];"
            "[original][song]amix=inputs=2:duration=first:normalize=0[selected];"
        )
        music_label = "selected"
    target = ROOT / "static/audio" / f"chapter-{chapter:02d}-mixed.mp3"
    temporary = target.with_suffix(".tmp.mp3")
    filters = (
        "[0:a]asplit=2[voice][control];"
        f"[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,loudnorm=I=-32:TP=-8:LRA=7,"
        f"volume=0.88,afade=t=in:d=3,afade=t=out:st={max(0, duration - 5)}:d=5[music];"
        + music_filter
        + f"[{music_label}][control]sidechaincompress=threshold=0.025:ratio=4:attack=25:release=650[bed];"
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
            *extra_inputs,
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
    if cue:
        episode["music_cue"] = {key: cue[key] for key in (
            "title", "source", "source_start", "chapter_start", "fade_seconds"
        )}
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
