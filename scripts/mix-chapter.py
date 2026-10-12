#!/usr/bin/env python3
"""Mix local chapter narration with original instrumental themes and scene fades."""

import argparse
import array
import hashlib
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATE = 24000
MUSIC_VERSION = "v2"
THEMES = {
    "night": (
        "夜行与微光",
        6,
        "keys",
        [(52, 59, 64, 67), (48, 55, 60, 64), (55, 62, 67, 71), (50, 57, 62, 66)],
    ),
    "warm": (
        "屋里的灯",
        6,
        "keys",
        [(48, 55, 60, 64), (53, 60, 65, 69), (55, 62, 67, 71), (48, 55, 60, 67)],
    ),
    "playful": (
        "小屋里的笑声",
        4.5,
        "pluck",
        [(48, 55, 64, 67), (57, 64, 69, 72), (53, 60, 65, 69), (55, 62, 67, 71)],
    ),
    "memory": (
        "旧日的银杏",
        7.5,
        "keys",
        [(57, 64, 69, 72), (53, 60, 65, 69), (48, 55, 60, 64), (52, 59, 64, 67)],
    ),
    "dawn": (
        "书页上的晨光",
        5,
        "pluck",
        [(55, 62, 67, 71), (52, 59, 64, 67), (48, 55, 60, 64), (50, 57, 62, 69)],
    ),
    "guitar": (
        "两根弦的对话",
        6,
        "guitar",
        [(52, 59, 64, 67), (48, 55, 60, 64), (55, 62, 67, 71), (50, 57, 62, 66)],
    ),
    "erhu": (
        "风与远方",
        7,
        "bow",
        [(57, 64, 69, 72), (55, 62, 67, 71), (53, 60, 65, 69), (52, 59, 64, 67)],
    ),
    "winter": (
        "冬夜的小灯",
        6,
        "bell",
        [(48, 55, 60, 64), (53, 60, 65, 69), (57, 64, 69, 72), (55, 62, 67, 71)],
    ),
    "resolve": (
        "并肩向前",
        5,
        "keys",
        [(52, 59, 64, 67), (48, 55, 60, 64), (55, 62, 67, 71), (50, 57, 62, 69)],
    ),
}
# Locate turns in spoken text; fractions serve only as explicit fallbacks.
PROFILES = {
    1: ("night", []),
    2: ("memory", [("这一次的备考", "warm", 0.58)]),
    3: ("playful", []),
    4: ("warm", []),
    5: ("playful", [("经过一整天的奔波", "warm", 0.86)]),
    6: ("dawn", []),
    7: ("playful", [("不过这事之后", "warm", 0.74)]),
    8: ("playful", [("这段插曲过后", "warm", 0.9)]),
    9: ("playful", [("从车棚往呱呱餐厅走", "memory", 0.35)]),
    10: ("warm", []),
    11: ("playful", [("短信内容只有一句", "warm", 0.63)]),
    12: ("playful", []),
    13: (
        "warm",
        [("桌角放着一个玻璃相框", "memory", 0.22), ("空气静了一秒", "warm", 0.32)],
    ),
    14: ("warm", [("这时史云涛又补了一句", "erhu", 0.65)]),
    15: ("dawn", [("两人坐在篮球场边的石阶上", "memory", 0.36)]),
    16: ("guitar", []),
    17: ("playful", [("偶尔，考研团也会破例", "guitar", 0.66)]),
    18: ("memory", [("我帮你找到专业课真题了", "warm", 0.98)]),
    19: ("warm", []),
    20: ("playful", [("青藏线？你别糊弄我们啊", "erhu", 0.51)]),
    21: ("warm", [("李礼靠在沙发上", "memory", 0.67), ("邓娜伸了个懒腰", "warm", 0.9)]),
    22: (
        "memory",
        [("我找到更合适的工作了", "warm", 0.53), ("后来呢", "playful", 0.7)],
    ),
    23: ("guitar", []),
    24: ("playful", []),
    25: ("playful", [("从那以后", "warm", 0.71)]),
    26: ("winter", [("快乐的时光总是过的特别快", "warm", 0.92)]),
    27: ("resolve", []),
    28: ("resolve", [("最后一门考试结束的铃声", "warm", 0.77)]),
    29: (
        "memory",
        [("这次考完是1月15日", "playful", 0.13), ("几天后，大家基本上", "warm", 0.86)],
    ),
}


def make_score(theme):
    folder = ROOT / ".audio-work/music"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{theme}-{MUSIC_VERSION}.wav"
    if path.exists():
        return path
    _, bar_length, timbre, chords = THEMES[theme]
    length = 16 * bar_length
    score = array.array("f", [0.0]) * round(RATE * length)

    def note(midi, start, seconds, volume):
        frequency = 440 * 2 ** ((midi - 69) / 12)
        offset = round(start * RATE)
        decay = 1.3 if timbre in ("pluck", "guitar") else 2.2
        harmonics = [(1, 1), (2, 0.22), (3, 0.07)]
        if timbre == "guitar":
            harmonics = [(1, 1), (2, 0.32), (3, 0.16), (4, 0.06)]
        if timbre == "bell":
            harmonics = [(1, 1), (2.01, 0.16), (3.99, 0.06)]
        if timbre == "bow":
            harmonics = [(1, 1), (2, 0.12), (3, 0.15)]
        for i in range(min(round(seconds * RATE), len(score) - offset)):
            t = i / RATE
            attack = min(1, t / (0.6 if timbre == "bow" else 0.04))
            release = min(1, max(0, (seconds - t) / 1.2))
            envelope = (
                attack * release * math.exp(-t / (5 if timbre == "bow" else decay))
            )
            phase = 2 * math.pi * frequency * t
            if timbre == "bow":
                phase += 0.08 * math.sin(2 * math.pi * 4.3 * t)
            sound = sum(
                weight * math.sin(phase * harmonic) for harmonic, weight in harmonics
            )
            score[offset + i] += volume * envelope * sound

    for bar in range(16):
        chord = chords[bar % 4]
        start = bar * bar_length
        note(chord[0], start, bar_length - 0.2, 0.1)
        for beat, midi in enumerate(chord[1:]):
            note(midi, start + 0.7 + beat * bar_length / 5, bar_length * 0.7, 0.065)
        if bar % 3 != 0:
            note(
                chord[3] + (2 if bar % 4 == 2 else 0),
                start + bar_length * 0.48,
                bar_length * 0.5,
                0.05,
            )
            if timbre == "guitar":
                note(chord[2], start + bar_length * 0.7, bar_length * 0.3, 0.05)
    pcm = array.array("h")
    for i, value in enumerate(score):
        fade = min(1, i / (RATE * 3), (len(score) - i) / (RATE * 5))
        pcm.append(round(max(-1, min(1, value * fade)) * 32767))
    if sys.byteorder != "little":
        pcm.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    return path


def scene_plan(chapter, manifest):
    duration = manifest["duration"]
    opening, turns = PROFILES[chapter]
    scenes = [dict(at=0, theme=opening, anchor=None)]
    for anchor, theme, fallback in turns:
        clock, located = 0, None
        for segment in manifest["segments"]:
            with wave.open(
                str(ROOT / ".audio-work" / f"{chapter:02d}" / segment["file"])
            ) as audio:
                seconds = audio.getnframes() / audio.getframerate()
            offset = segment["text"].find(anchor)
            if offset >= 0:
                located = clock + seconds * offset / max(1, len(segment["text"]))
                break
            clock += seconds + segment["pause"]
        at = located if located is not None else duration * fallback
        scenes.append(
            dict(
                at=round(at, 3), theme=theme, anchor=anchor, matched=located is not None
            )
        )
    scenes.sort(key=lambda s: s["at"])
    for i, scene in enumerate(scenes):
        scene["duration"] = (
            scenes[i + 1]["at"] if i + 1 < len(scenes) else duration
        ) - scene["at"]
    return scenes


def mix(chapter):
    work = ROOT / ".audio-work" / f"{chapter:02d}"
    manifest = json.loads((work / "manifest.json").read_text())
    if manifest["status"] != "completed":
        raise ValueError("Complete chapter narration first")
    scenes = scene_plan(chapter, manifest)
    target = ROOT / "static/audio" / f"chapter-{chapter:02d}-mixed.mp3"
    temporary = target.with_suffix(".tmp.mp3")
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-y",
        "-i",
        str(ROOT / manifest["output"]),
    ]
    filters, labels = ["[0:a]asplit=2[voice][control]"], []
    for i, scene in enumerate(scenes, 1):
        cmd += ["-stream_loop", "-1", "-i", str(make_score(scene["theme"]))]
        seconds = scene["duration"]
        fade = min(3, seconds / 3)
        label = f"p{i}"
        filters.append(
            f"[{i}:a]atrim=duration={seconds},asetpts=PTS-STARTPTS,loudnorm=I=-29:TP=-6:LRA=7,"
            f"volume=0.45,afade=t=in:d={fade},afade=t=out:st={seconds - fade}:d={fade}[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append("".join(labels) + f"concat=n={len(scenes)}:v=0:a=1[music]")
    filters.append(
        "[music][control]sidechaincompress=threshold=0.025:ratio=4:attack=25:release=650[bed]"
    )
    filters.append(
        "[voice][bed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-18:TP=-2:LRA=9[out]"
    )
    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[out]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-metadata",
        f"title={manifest['source'].removesuffix('.md')} · 轻配乐版",
        "-metadata",
        "artist=guige",
        str(temporary),
    ]
    subprocess.run(cmd, check=True, timeout=1200)
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(temporary), "-f", "null", "-"],
        check=True,
        timeout=120,
    )
    temporary.replace(target)
    path = ROOT / "data/audio.json"
    catalog = json.loads(path.read_text())
    minutes, seconds = divmod(round(manifest["duration"]), 60)
    episode = dict(
        mixed=str(target.relative_to(ROOT / "static")),
        duration=f"{minutes}:{seconds:02d}",
        seconds=round(manifest["duration"], 2),
        revision=hashlib.sha256(target.read_bytes()).hexdigest()[:16],
        music="原创器乐："
        + "、".join(dict.fromkeys(THEMES[s["theme"]][0] for s in scenes)),
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
                scenes=scenes,
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
