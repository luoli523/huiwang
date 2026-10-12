#!/usr/bin/env python3
"""Mix chapter 1 with an original, deterministic sparse keyboard score."""
import array
import hashlib
import json
import math
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.audio-work/01'
RATE = 24000


def make_score():
    # Original 96-second phrase: no sampled recordings or existing melodies.
    # Minor opening with a warmer G-major ending; restrained, unhurried notes.
    score = array.array('f', [0.0]) * (RATE * 96)
    chords = [(52, 59, 64, 67), (48, 55, 60, 64), (55, 62, 67, 71), (50, 57, 62, 66)]
    melody = [None, 71, 67, None, 69, 64, None, 67, None, 71, 74, None, 69, 67, None, 66]

    def note(midi, start, length, volume):
        frequency = 440 * 2 ** ((midi - 69) / 12)
        offset = round(start * RATE)
        for i in range(min(round(length * RATE), len(score) - offset)):
            t = i / RATE
            attack = min(1, t / .06)
            release = min(1, max(0, (length - t) / 1.2))
            envelope = attack * release * math.exp(-t / 2.2)
            sound = sum(weight * math.sin(2 * math.pi * frequency * harmonic * t)
                        for harmonic, weight in [(1, 1), (2, .22), (3, .07)])
            score[offset + i] += volume * envelope * sound

    for bar in range(16):
        chord = chords[bar % 4]
        start = bar * 6
        note(chord[0], start, 5.8, .12)
        for beat, midi in enumerate(chord[1:]):
            note(midi, start + .8 + beat * 1.3, 4.5, .08)
        if melody[bar] is not None:
            note(melody[bar], start + 2.4, 3.5, .06)
    pcm = array.array('h')
    for i, value in enumerate(score):
        fade = min(1, i / (RATE * 3), (len(score) - i) / (RATE * 5))
        pcm.append(round(max(-1, min(1, value * fade)) * 32767))
    if __import__('sys').byteorder != 'little':
        pcm.byteswap()
    path = WORK / 'original-night-train.wav'
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    return path


def main():
    manifest = json.loads((WORK / 'manifest.json').read_text())
    if manifest['status'] != 'completed':
        raise ValueError('Complete chapter narration first')
    music = make_score()
    duration = manifest['duration']
    target = ROOT / 'static/audio/chapter-01-mixed.mp3'
    # Normalize music separately, then duck it under speech. Sparse phrase loops
    # with its own fades; score enters/leaves gently over the chapter timeline.
    filters = (
        '[0:a]asplit=2[voice][control];'
        f'[1:a]loudnorm=I=-29:TP=-6:LRA=7,volume=0.45,atrim=duration={duration},'
        f'afade=t=in:d=4,afade=t=out:st={max(0, duration - 6)}:d=6[music];'
        '[music][control]sidechaincompress=threshold=0.025:ratio=4:attack=25:release=650[bed];'
        '[voice][bed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-18:TP=-2:LRA=9[out]'
    )
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i',
                    str(ROOT / manifest['output']), '-stream_loop', '-1', '-i', str(music),
                    '-filter_complex', filters, '-map', '[out]', '-c:a', 'libmp3lame', '-b:a', '128k',
                    '-metadata', 'title=第一章 重返北京 · 轻配乐版',
                    '-metadata', 'artist=guige', str(target)], check=True)
    catalog_path = ROOT / 'data/audio.json'
    catalog = json.loads(catalog_path.read_text())
    minutes, seconds = divmod(round(duration), 60)
    catalog['1'] = dict(voice=manifest['output'], mixed=str(target.relative_to(ROOT)),
                        duration=f'{minutes}:{seconds:02d}', seconds=round(duration, 2),
                        revision=hashlib.sha256(target.read_bytes()).hexdigest()[:16],
                        music='原创器乐：夜行与微光')
    # Hugo paths are relative to static/ (or can be replaced with hosted URLs).
    for key in ('voice', 'mixed'):
        catalog['1'][key] = catalog['1'][key].removeprefix('static/')
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(catalog['1'], ensure_ascii=False))


if __name__ == '__main__':
    main()
