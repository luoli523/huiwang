#!/usr/bin/env python3
"""Generate resumable chapter narration using the existing loopback TTS service."""

import argparse
import hashlib
import json
import re
import subprocess
import time
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8091"


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=1800) as response:
        return response.read()


def chunks(source, title):
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", source, count=1, flags=re.S)
    body = re.sub(r"^#+.*$", "", body, flags=re.M).strip()
    if "本章节内容待更新" in body or "暂时到此为止" in body:
        raise ValueError("This chapter has no narrative body")
    # Preserve scene boundaries, while short paragraphs share a synthesis request.
    result = [(title + "。", 1.0)]
    for scene in re.split(r"\n\s*---\s*\n", body):
        current = ""
        for paragraph in re.split(r"\n\s*\n", scene.strip()):
            paragraph = re.sub(r"[*`#>]", "", paragraph).strip()
            if not paragraph:
                continue
            if current and len(current) + len(paragraph) > 450:
                result.append((current, 0.35))
                current = ""
            current += ("\n" if current else "") + paragraph
        if current:
            result.append((current, 0.9))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=int)
    parser.add_argument(
        "--archive-voice",
        action="store_true",
        help="Keep pure speech locally; publish only the mixed episode",
    )
    parser.add_argument(
        "--voice-version", help="Pin the same reference version across a batch"
    )
    args = parser.parse_args()
    source_path = next((ROOT / "content/docs").glob(f"{args.chapter}-*.md"))
    source = source_path.read_text()
    # Spoken forms disambiguate the train code and digit-by-digit model name.
    spoken = source.replace("T2次", "特快二次").replace("诺基亚6610", "诺基亚六六一零")
    title = f"第{args.chapter}章，" + source_path.stem.split("-", 1)[1]
    voice = next(
        v
        for v in json.loads(request("/v1/audio/voices"))["voices"]
        if v["id"] == "guige"
    )
    voice_version = args.voice_version or voice["version"]
    payload_base = dict(
        model="qwen3-tts",
        voice="guige",
        voice_version=voice_version,
        response_format="wav",
        lang_code="chinese",
        speed=1.0,
    )
    plan = chunks(spoken, title)
    work = ROOT / ".audio-work" / f"{args.chapter:02d}"
    work.mkdir(parents=True, exist_ok=True)
    manifest = dict(
        chapter=args.chapter,
        source=source_path.name,
        source_hash=hashlib.sha256(source.encode()).hexdigest(),
        voice="guige",
        voice_version=voice_version,
        normalization={"T2": "特快二", "诺基亚6610": "诺基亚六六一零"},
        segments=[],
        status="running",
    )
    started = time.monotonic()
    paths = []
    for index, (text, pause) in enumerate(plan):
        payload = dict(payload_base, input=text)
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        path = work / f"{index:03d}-{digest}.wav"
        print(
            f"[{index + 1}/{len(plan)}] {len(text)} characters {'cached' if path.exists() else 'generating'}",
            flush=True,
        )
        if not path.exists():
            data = request("/v1/audio/speech", payload)
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(data)
            with wave.open(str(temporary)) as audio:
                if not audio.getnframes():
                    raise ValueError("Empty audio returned by TTS")
            temporary.replace(path)
        paths.append((path, pause))
        with wave.open(str(path)) as audio:
            seconds = audio.getnframes() / audio.getframerate()
        manifest["segments"].append(
            dict(file=path.name, text=text, pause=pause, duration=round(seconds, 3))
        )
        (work / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )
    master = work / "narration.wav"
    with wave.open(str(master), "wb") as output:
        audio_params = None
        for path, pause in paths:
            with wave.open(str(path)) as audio:
                params = (
                    audio.getnchannels(),
                    audio.getsampwidth(),
                    audio.getframerate(),
                )
                if audio_params is None:
                    audio_params = params
                    output.setnchannels(params[0])
                    output.setsampwidth(params[1])
                    output.setframerate(params[2])
                if params != audio_params:
                    raise ValueError("TTS segments have inconsistent audio formats")
                output.writeframes(audio.readframes(audio.getnframes()))
                output.writeframes(
                    b"\x00" * int(params[2] * pause) * params[0] * params[1]
                )
    target = (
        work / "voice.mp3"
        if args.archive_voice
        else ROOT / "static/audio" / f"chapter-{args.chapter:02d}-voice.mp3"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-i",
            str(master),
            "-af",
            "loudnorm=I=-18:TP=-2:LRA=9",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            "-metadata",
            f"title={title}",
            "-metadata",
            "artist=guige",
            str(target),
        ],
        check=True,
    )
    with wave.open(str(master)) as audio:
        manifest["duration"] = audio.getnframes() / audio.getframerate()
    manifest.update(
        status="completed",
        elapsed=round(time.monotonic() - started, 2),
        output=str(target.relative_to(ROOT)),
    )
    (work / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )
    print(
        json.dumps(
            {k: manifest[k] for k in ("status", "duration", "elapsed", "output")},
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
