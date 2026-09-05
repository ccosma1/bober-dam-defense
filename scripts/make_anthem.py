#!/usr/bin/env python3
"""Original Bober anthem: AIN'T NO LEAK. New melody in D major. Not Cash."""
from __future__ import annotations

import os
import struct
import subprocess
import sys
import wave

import numpy as np

SR = 44100
BPM = 96.0
BEAT = 60.0 / BPM
BAR = 4.0 * BEAT
RNG = np.random.default_rng(19)

# D major folk stomper — rising major pentatonic, not minor-gospel.
# I–IV–I–V verses; IV–I–V–I chorus. New hook, new contour.
CH = {
    "D": [146.83, 220.00, 293.66, 369.99],
    "G": [98.00, 146.83, 196.00, 246.94],
    "A": [110.00, 164.81, 220.00, 277.18],
    "Bm": [123.47, 185.00, 246.94, 293.66],
    "Em": [164.81, 246.94, 329.63, 392.00],
}


def midi_hz(m):
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))


def env_adsr(n, a=0.02, d=0.08, s=0.7, r=0.12):
    e = np.ones(n, dtype=np.float64)
    na, nd, nr = int(a * n), int(d * n), int(r * n)
    na, nd, nr = max(1, na), max(1, nd), max(1, nr)
    if na + nd + nr >= n:
        na = max(1, n // 8)
        nd = max(1, n // 8)
        nr = max(1, n // 6)
    e[:na] = np.linspace(0, 1, na)
    e[na : na + nd] = np.linspace(1, s, nd)
    e[na + nd : n - nr] = s
    e[n - nr :] = np.linspace(s, 0, nr)
    return e


def lowpass(x, cutoff, sr=SR):
    x = np.asarray(x, dtype=np.float64)
    ny = sr * 0.5
    c = min(0.99, max(1e-4, cutoff / ny))
    try:
        from scipy.signal import butter, lfilter
        b, a = butter(1, c, btype="low")
        return lfilter(b, a, x)
    except Exception:
        a = 1.0 - np.exp(-2.0 * np.pi * cutoff / sr)
        y = np.empty_like(x)
        acc = 0.0
        for i, v in enumerate(x):
            acc += a * (v - acc)
            y[i] = acc
        return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def clip_soft(x, amt=1.4):
    return np.tanh(x * amt)


def mix_at(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    n = min(len(sig), len(buf) - i0)
    if n <= 0 or i0 < 0:
        return
    buf[i0 : i0 + n] += sig[:n] * gain


def ks_pluck(freq, dur, decay=0.988, brightness=0.45):
    n = max(2, int(SR / max(40.0, freq)))
    buf = RNG.uniform(-1, 1, n)
    buf = brightness * buf + (1 - brightness) * np.roll(buf, 1)
    out_len = int(dur * SR)
    reps = int(np.ceil(out_len / n)) + 1
    out = np.tile(buf, reps)[:out_len]
    t = np.arange(out_len) / SR
    damp = 3.2 + (1.0 - decay) * 80.0
    out *= np.exp(-t * damp * (freq / 220.0) ** 0.3)
    out *= env_adsr(out_len, 0.004, 0.04, 0.55, 0.22)
    return out


def guitar_strum(chord, dur, up=False):
    layers = []
    for i, f in enumerate(chord):
        delay = (0.012 * (len(chord) - 1 - i) if up else 0.011 * i)
        p = ks_pluck(f, dur + 0.05, decay=0.991 if i < 2 else 0.985)
        pad = np.zeros(int(delay * SR) + len(p))
        pad[-len(p) :] = p
        layers.append(pad)
    m = max(len(s) for s in layers)
    acc = np.zeros(m)
    for s in layers:
        acc[: len(s)] += s
    acc /= max(1, len(chord) * 0.55)
    return acc[: int(dur * SR)]


def bass_note(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    sig = 0.72 * np.sin(2 * np.pi * freq * t)
    sig += 0.18 * np.sin(2 * np.pi * freq * 2 * t)
    sig += 0.08 * np.sign(np.sin(2 * np.pi * freq * t)) * np.exp(-t * 6)
    sig *= env_adsr(len(sig), 0.01, 0.08, 0.7, 0.18)
    return clip_soft(sig, 1.1)


def stomp(dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * 62 * t) * np.exp(-t * 18)
    thump += 0.4 * np.sin(2 * np.pi * 90 * t) * np.exp(-t * 22)
    noise = RNG.normal(0, 1, n) * np.exp(-t * 28)
    noise = lowpass(noise, 420)
    return clip_soft(0.9 * thump + 0.35 * noise, 1.6)


def clap(dur=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    acc = np.zeros(n)
    for k, off in enumerate((0.0, 0.012, 0.023)):
        i = int(off * SR)
        burst = RNG.normal(0, 1, n - i)
        burst *= np.exp(-np.arange(len(burst)) / SR * (38 + k * 8))
        acc[i:] += burst * (1.0 - 0.2 * k)
    acc = highpass(acc, 900)
    acc = lowpass(acc, 4200)
    return clip_soft(acc * 1.8, 1.3)


def choir_pad(freqs, dur, gain=0.12):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for f in freqs:
        for det in (-0.6, 0.0, 0.7):
            ff = f * (2 ** (det / 1200.0))
            sig += np.sin(2 * np.pi * ff * t)
            sig += 0.15 * np.sin(2 * np.pi * ff * 2 * t)
    sig /= max(1, len(freqs) * 3)
    sig *= env_adsr(len(sig), 0.25, 0.2, 0.85, 0.35)
    return sig * gain


FORMANTS = {
    "a": (730, 1090, 2440),
    "ah": (730, 1090, 2440),
    "e": (530, 1840, 2480),
    "eh": (530, 1840, 2480),
    "i": (270, 2290, 3010),
    "ee": (270, 2290, 3010),
    "o": (570, 840, 2410),
    "oh": (570, 840, 2410),
    "u": (300, 870, 2240),
    "oo": (300, 870, 2240),
    "uh": (640, 1200, 2400),
    "ay": (660, 1720, 2410),
    "n": (400, 1500, 2500),
    "m": (250, 1200, 2200),
    "l": (450, 1100, 2600),
    "r": (490, 1350, 1700),
}


def resonate(t, f0, f1, f2, f3, buzz):
    s = buzz * 0.55
    for f, g, qdecay in ((f1, 0.55, 7.0), (f2, 0.32, 9.0), (f3, 0.12, 11.0)):
        s = s + g * np.sin(2 * np.pi * f * t) * np.exp(-((t * qdecay) % 0.08) * 0)
        s = s + 0.08 * np.sin(2 * np.pi * f * t + 0.3)
    return s


def vowel(f0, dur, key="ah", grit=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # slight vibrato, original — slow folk, not opera
    vib = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.1 * t))
    phase = np.cumsum(2 * np.pi * vib / SR)
    saw = 2.0 * (phase / (2 * np.pi) % 1.0) - 1.0
    buzz = 0.72 * saw + 0.28 * np.sin(phase)
    f1, f2, f3 = FORMANTS.get(key, FORMANTS["ah"])
    # cheap formant: mix band-limited harmonics weighted toward formants
    sig = np.zeros(n)
    for h in range(1, 12):
        fh = f0 * h
        w1 = np.exp(-((fh - f1) / 180.0) ** 2)
        w2 = np.exp(-((fh - f2) / 280.0) ** 2)
        w3 = np.exp(-((fh - f3) / 400.0) ** 2)
        amp = 0.55 * w1 + 0.35 * w2 + 0.12 * w3
        amp *= 1.0 / h ** 0.7
        sig += amp * np.sin(h * phase)
    noise = RNG.normal(0, 1, n) * grit * np.exp(-t * 3)
    sig = sig + 0.08 * noise
    sig *= env_adsr(n, 0.03, 0.08, 0.8, 0.12)
    # gravel: mix a sub-octave
    sig += 0.12 * np.sin(phase * 0.5)
    return clip_soft(sig * 0.55, 1.15)


def consonant(kind, dur=0.05):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = RNG.normal(0, 1, n)
    if kind in ("s", "t", "k", "ch"):
        x = highpass(noise, 2500) * np.exp(-t * 40)
    elif kind in ("h",):
        x = lowpass(highpass(noise, 800), 3500) * np.exp(-t * 18)
    elif kind in ("b", "d", "g", "p"):
        x = lowpass(noise, 600) * np.exp(-t * 50)
        x += 0.5 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 40)
    elif kind in ("w", "y"):
        x = lowpass(noise, 900) * np.exp(-t * 20) * 0.3
    else:
        x = lowpass(noise, 1800) * np.exp(-t * 30) * 0.4
    return x * 0.5


# Syllables: (lyric, vowel, midi, beats, cons)
# Melody is original D-major stomp. Rising fourths / pentatonic, not Cash.
# D4=62 E4=64 F#4=66 G4=67 A4=69 B4=71 C#5=73 D5=74

def line(sylls):
    return sylls


V1 = [
    line([("There", "eh", 66, 1.0, "t"), ("ain't", "ay", 67, 1.0, ""), ("no", "oh", 69, 1.0, "n"),
          ("leak", "ee", 74, 1.0, "l"), ("gon", "uh", 69, 0.5, "g"), ("na", "ah", 67, 0.5, "n"),
          ("hold", "oh", 66, 1.0, "h"), ("this", "i", 64, 0.5, "t"), ("dam", "ah", 62, 1.5, "d")]),
    line([("Bo", "oh", 62, 0.5, "b"), ("ber", "er", 64, 0.5, "b"), ("built", "i", 66, 1.0, "b"),
          ("it", "i", 67, 0.5, ""), ("with", "i", 69, 0.5, "w"), ("his", "i", 67, 0.5, "h"),
          ("own", "oh", 66, 1.0, ""), ("two", "oo", 64, 1.0, "t"), ("hands", "ah", 62, 2.5, "h")]),
    line([("Riv", "i", 69, 0.5, "r"), ("er", "er", 69, 0.5, ""), ("can", "ah", 67, 1.0, "k"),
          ("yell", "eh", 66, 1.0, "y"), ("and", "ah", 64, 0.5, ""), ("the", "uh", 62, 0.5, "t"),
          ("crabs", "ah", 64, 1.5, "k"), ("can", "ah", 66, 0.5, "k"), ("crawl", "ah", 69, 2.0, "k")]),
    line([("We", "ee", 62, 0.5, "w"), ("plant", "ah", 66, 1.0, "p"), ("the", "uh", 69, 0.5, "t"),
          ("sticks", "i", 71, 1.0, "s"), ("and", "ah", 69, 0.5, ""), ("we", "ee", 66, 0.5, "w"),
          ("hold", "oh", 67, 1.5, "h"), ("the", "uh", 64, 0.5, "t"), ("wall", "ah", 62, 2.0, "w")]),
]

CH_L = [
    line([("Ain't", "ay", 66, 1.0, ""), ("no", "oh", 69, 1.0, "n"), ("leak", "ee", 74, 1.5, "l"),
          ("ain't", "ay", 66, 1.0, ""), ("no", "oh", 69, 1.0, "n"), ("wash", "ah", 71, 1.0, "w"),
          ("a", "uh", 69, 0.5, ""), ("way", "ay", 67, 1.0, "w")]),
    line([("Bea", "ee", 67, 0.5, "b"), ("vers", "er", 69, 0.5, "v"), ("dig", "i", 71, 1.0, "d"),
          ("in", "i", 74, 1.0, ""), ("till", "i", 71, 1.0, "t"), ("the", "uh", 69, 0.5, "t"),
          ("break", "ay", 67, 1.5, "b"), ("of", "uh", 66, 0.5, ""), ("day", "ay", 62, 1.5, "d")]),
    line([("Yeet", "ee", 74, 1.0, "y"), ("the", "uh", 71, 0.5, "t"), ("wood", "oo", 69, 1.0, "w"),
          ("and", "ah", 67, 0.5, ""), ("hear", "ee", 66, 1.0, "h"), ("the", "uh", 64, 0.5, "t"),
          ("riv", "i", 66, 0.5, "r"), ("er", "er", 67, 0.5, ""), ("moan", "oh", 69, 2.5, "m")]),
    line([("This", "i", 62, 0.5, "t"), ("dam's", "ah", 66, 1.0, "d"), ("our", "ow", 69, 1.0, ""),
          ("home", "oh", 74, 1.5, "h"), ("we", "ee", 71, 0.5, "w"), ("ain't", "ay", 69, 1.0, ""),
          ("a", "uh", 66, 0.5, ""), ("lone", "oh", 62, 2.0, "l")]),
]

V2 = [
    line([("Mars", "ah", 66, 1.0, "m"), ("sent", "eh", 67, 1.0, "s"), ("a", "uh", 69, 0.5, ""),
          ("truck", "uh", 74, 1.5, "t"), ("that", "ah", 69, 0.5, "t"), ("no", "oh", 67, 0.5, "n"),
          ("bod", "ah", 66, 1.0, "b"), ("y", "ee", 64, 0.5, ""), ("asked", "ah", 62, 1.5, "")]),
    line([("Ot", "ah", 62, 0.5, ""), ("ters", "er", 64, 0.5, "t"), ("got", "ah", 66, 1.0, "g"),
          ("maps", "ah", 67, 1.0, "m"), ("and", "ah", 69, 0.5, ""), ("a", "uh", 67, 0.5, ""),
          ("pi", "i", 66, 0.5, "p"), ("rate", "ay", 64, 1.0, "r"), ("mast", "ah", 62, 2.5, "m")]),
    line([("Still", "i", 69, 1.0, "s"), ("we", "ee", 69, 0.5, "w"), ("stand", "ah", 67, 1.5, "s"),
          ("where", "eh", 66, 1.0, "w"), ("the", "uh", 64, 0.5, "t"), ("tim", "i", 66, 1.0, "t"),
          ("ber", "er", 69, 0.5, "b"), ("stacks", "ah", 74, 2.0, "s")]),
    line([("Hard", "ah", 62, 1.0, "h"), ("hat", "ah", 66, 1.0, "h"), ("on", "ah", 69, 1.0, ""),
          ("and", "ah", 71, 0.5, ""), ("we", "ee", 69, 0.5, "w"), ("got", "ah", 66, 1.0, "g"),
          ("their", "eh", 67, 1.0, "t"), ("backs", "ah", 62, 2.0, "b")]),
]

BR = [
    line([("When", "eh", 71, 0.5, "w"), ("the", "uh", 69, 0.5, "t"), ("wa", "ah", 67, 0.5, "w"),
          ("ter", "er", 66, 0.5, "t"), ("ris", "i", 64, 1.0, "r"), ("es", "eh", 62, 1.0, ""),
          ("when", "eh", 64, 0.5, "w"), ("the", "uh", 66, 0.5, "t"), ("night", "i", 67, 1.0, "n"),
          ("gets", "eh", 69, 0.5, "g"), ("mean", "ee", 71, 1.5, "m")]),
    line([("Fix", "i", 62, 1.0, "f"), ("the", "uh", 64, 0.5, "t"), ("cracks", "ah", 66, 1.5, "k"),
          ("and", "ah", 67, 0.5, ""), ("keep", "ee", 69, 1.0, "k"), ("the", "uh", 71, 0.5, "t"),
          ("wood", "oo", 69, 1.0, "w"), ("work", "er", 66, 0.5, "w"), ("clean", "ee", 62, 1.5, "k")]),
    line([("One", "uh", 66, 1.0, "w"), ("more", "oh", 69, 1.0, "m"), ("board", "oh", 74, 1.5, "b"),
          ("and", "ah", 71, 0.5, ""), ("one", "uh", 69, 1.0, "w"), ("more", "oh", 67, 1.0, "m"),
          ("prayer", "eh", 66, 2.0, "p")]),
    line([("Bo", "oh", 62, 0.5, "b"), ("ber's", "er", 66, 1.0, "b"), ("still", "i", 69, 1.0, "s"),
          ("here", "ee", 74, 1.5, "h"), ("the", "uh", 71, 0.5, "t"), ("dam's", "ah", 69, 1.0, "d"),
          ("still", "i", 66, 1.0, "s"), ("there", "eh", 62, 1.5, "t")]),
]

TAG = [
    line([("De", "ee", 69, 0.5, "d"), ("fend", "eh", 74, 1.5, "f"), ("the", "uh", 71, 0.5, "t"),
          ("dam", "ah", 69, 1.5, "d")]),
    line([("De", "ee", 66, 0.5, "d"), ("fend", "eh", 69, 1.5, "f"), ("the", "uh", 67, 0.5, "t"),
          ("dam", "ah", 62, 1.5, "d")]),
    line([("De", "ee", 62, 0.75, "d"), ("fend", "eh", 66, 1.25, "f"), ("the", "uh", 69, 0.75, "t"),
          ("dam", "ah", 74, 5.25, "d")]),  # hold
]


def render_line(sylls, choir=False):
    parts = []
    for lyric, vow, midi, beats, cons in sylls:
        dur = beats * BEAT
        if cons:
            parts.append(consonant(cons, min(0.06, dur * 0.18)))
        vkey = vow if vow in FORMANTS else ("er" if vow == "er" else "ah")
        if vkey == "er":
            vkey = "uh"
        if vow == "ow":
            vkey = "ah"
        lead = vowel(midi_hz(midi), dur, vkey, grit=0.22)
        if choir:
            c1 = vowel(midi_hz(midi + 4), dur * 0.98, vkey, grit=0.08) * 0.35
            c2 = vowel(midi_hz(midi - 5), dur * 0.98, "ah", grit=0.1) * 0.28
            n = min(len(lead), len(c1), len(c2))
            lead = lead[:n] + c1[:n] + c2[:n]
        parts.append(lead)
    if not parts:
        return np.zeros(1)
    return np.concatenate(parts)


def arrange():
    # 5-bar intro + 8+8+8+8+8 + 8 chorus + ~4 tag  ≈ 2:17
    intro_bars = 5
    verse_bars = 8
    chorus_bars = 8
    bridge_bars = 8
    tag_bars = 4
    total_bars = intro_bars + verse_bars + chorus_bars + verse_bars + chorus_bars + bridge_bars + chorus_bars + tag_bars
    dur = total_bars * BAR + 0.4
    left = np.zeros(int(dur * SR))
    right = np.zeros(int(dur * SR))

    verse_prog = ["D", "G", "D", "A", "D", "G", "A", "D"]
    chorus_prog = ["G", "D", "G", "A", "D", "G", "A", "D"]
    bridge_prog = ["Bm", "G", "D", "A", "Bm", "G", "A", "D"]

    def section_chords(start_bar, prog, stomps=True, claps=False, pad=False, extra_guitar=False):
        for i, name in enumerate(prog):
            t = (start_bar + i) * BAR
            ch = CH[name]
            # boom-chick: down 1, up 2, down 3, up 4
            mix_at(left, guitar_strum(ch, BEAT * 1.15, up=False), t, 0.55)
            mix_at(right, guitar_strum(ch, BEAT * 1.15, up=False), t + 0.004, 0.5)
            mix_at(left, guitar_strum(ch, BEAT * 0.7, up=True), t + BEAT, 0.32)
            mix_at(right, guitar_strum(ch, BEAT * 0.7, up=True), t + BEAT + 0.003, 0.38)
            mix_at(left, guitar_strum(ch, BEAT * 1.05, up=False), t + 2 * BEAT, 0.5)
            mix_at(right, guitar_strum(ch, BEAT * 1.05, up=False), t + 2 * BEAT + 0.004, 0.48)
            mix_at(left, guitar_strum(ch, BEAT * 0.65, up=True), t + 3 * BEAT, 0.3)
            mix_at(right, guitar_strum(ch, BEAT * 0.65, up=True), t + 3 * BEAT, 0.34)
            mix_at(left, bass_note(ch[0], BAR * 0.95), t, 0.7)
            mix_at(right, bass_note(ch[0], BAR * 0.95), t, 0.62)
            if extra_guitar:
                mix_at(left, ks_pluck(ch[-1] * 2, BEAT * 0.9, 0.976), t + 0.5 * BEAT, 0.18)
                mix_at(right, ks_pluck(ch[-1] * 2, BEAT * 0.9, 0.976), t + 1.5 * BEAT, 0.16)
            if stomps:
                mix_at(left, stomp(), t, 0.95)
                mix_at(right, stomp(), t, 0.85)
                mix_at(left, stomp(), t + 2 * BEAT, 0.9)
                mix_at(right, stomp(), t + 2 * BEAT, 0.95)
            if claps:
                mix_at(left, clap(), t + BEAT, 0.55)
                mix_at(right, clap(), t + BEAT, 0.7)
                mix_at(left, clap(), t + 3 * BEAT, 0.7)
                mix_at(right, clap(), t + 3 * BEAT, 0.55)
            if pad:
                mix_at(left, choir_pad(ch, BAR, 0.1), t, 1.0)
                mix_at(right, choir_pad([c * 1.003 for c in ch], BAR, 0.1), t, 1.0)

    # INTRO: stomps build + hum
    for i in range(intro_bars):
        t = i * BAR
        dens = 0.35 + 0.12 * i
        mix_at(left, stomp(), t, dens)
        mix_at(right, stomp(), t, dens * 0.9)
        mix_at(left, stomp(), t + 2 * BEAT, dens * 0.95)
        mix_at(right, stomp(), t + 2 * BEAT, dens)
        if i >= 2:
            mix_at(left, clap(), t + BEAT, 0.25 + 0.08 * i)
            mix_at(right, clap(), t + 3 * BEAT, 0.28 + 0.08 * i)
        ch = CH[["D", "D", "G", "A", "D"][i]]
        mix_at(left, guitar_strum(ch, BAR * 0.9, False), t, 0.28 + 0.05 * i)
        mix_at(right, guitar_strum(ch, BAR * 0.9, False), t + 0.01, 0.26 + 0.05 * i)
        mix_at(left, choir_pad(ch, BAR, 0.08 + 0.02 * i), t)
        mix_at(right, choir_pad([c * 1.004 for c in ch], BAR, 0.08 + 0.02 * i), t)
        mix_at(left, bass_note(ch[0], BAR * 0.9), t, 0.35 + 0.08 * i)
        mix_at(right, bass_note(ch[0], BAR * 0.9), t, 0.32 + 0.08 * i)

    b = intro_bars
    section_chords(b, verse_prog, stomps=True, claps=False, pad=True)
    b += 8
    section_chords(b, chorus_prog, stomps=True, claps=True, pad=True, extra_guitar=True)
    b += 8
    section_chords(b, verse_prog, stomps=True, claps=False, pad=True)
    b += 8
    section_chords(b, chorus_prog, stomps=True, claps=True, pad=True, extra_guitar=True)
    b += 8
    section_chords(b, bridge_prog, stomps=True, claps=False, pad=True)
    b += 8
    section_chords(b, chorus_prog, stomps=True, claps=True, pad=True, extra_guitar=True)
    b += 8
    # tag: D pedal, stomps, hold
    for i in range(tag_bars):
        t = b * BAR + i * BAR
        ch = CH["D"]
        mix_at(left, guitar_strum(ch, BAR, False), t, 0.5)
        mix_at(right, guitar_strum(ch, BAR, True), t, 0.48)
        mix_at(left, bass_note(ch[0], BAR), t, 0.75)
        mix_at(right, bass_note(ch[0], BAR), t, 0.7)
        mix_at(left, stomp(), t, 1.0)
        mix_at(right, stomp(), t + 2 * BEAT, 1.0)
        mix_at(left, clap(), t + BEAT, 0.65)
        mix_at(right, clap(), t + 3 * BEAT, 0.65)
        mix_at(left, choir_pad(ch, BAR, 0.16), t)
        mix_at(right, choir_pad(ch, BAR, 0.16), t)

    def place_lyrics(start_bar, lines, choir=False, gain=0.92):
        t = start_bar * BAR
        for sylls in lines:
            sig = render_line(sylls, choir=choir)
            # gravel baritone slightly left-of-center, choir wider
            mix_at(left, sig, t, gain)
            mix_at(right, sig, t, gain * 0.88)
            t += 2 * BAR  # each lyric line occupies 2 bars (8 beats)

    place_lyrics(intro_bars, V1, choir=False, gain=0.95)
    place_lyrics(intro_bars + 8, CH_L, choir=True, gain=1.05)
    place_lyrics(intro_bars + 16, V2, choir=False, gain=0.95)
    place_lyrics(intro_bars + 24, CH_L, choir=True, gain=1.08)
    place_lyrics(intro_bars + 32, BR, choir=False, gain=0.9)
    place_lyrics(intro_bars + 40, CH_L, choir=True, gain=1.1)
    # tag lines sit in last 4 bars: 3 calls + hold
    t = (intro_bars + 48) * BAR
    for i, sylls in enumerate(TAG):
        sig = render_line(sylls, choir=True)
        mix_at(left, sig, t, 1.15)
        mix_at(right, sig, t, 1.1)
        t += (1.0 if i < 2 else 2.0) * BAR

    # master
    stereo = np.stack([left, right], axis=1)
    peak = np.max(np.abs(stereo)) + 1e-9
    stereo = stereo / peak * 0.92
    # light glue
    stereo = np.tanh(stereo * 1.15) / np.tanh(1.15)
    return stereo, total_bars * BAR


def write_wav(path, stereo):
    pcm = np.clip(stereo, -1, 1)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def encode_mp3(wav_path, mp3_path):
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"
    cmd = [ff, "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "4", mp3_path]
    subprocess.check_call(cmd)


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "history")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    print("rendering AIN'T NO LEAK...", flush=True)
    stereo, dur = arrange()
    wav_path = os.path.join(out_dir, "anthem.wav")
    mp3_path = os.path.join(out_dir, "anthem.mp3")
    write_wav(wav_path, stereo)
    print("wav %.2fs -> %s" % (dur, wav_path), flush=True)
    encode_mp3(wav_path, mp3_path)
    print("mp3 -> %s" % mp3_path, flush=True)
    print("duration_s=%.3f" % dur)


if __name__ == "__main__":
    main()
