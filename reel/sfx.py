#!/usr/bin/env python3
"""Sound design du Reel 01 : woosh + tonalités courtes synthétisés (aucun fichier externe, donc aucun droit),
puis mixage final (voix + jingle + nappe + sfx avec ducking) et accélération 1,1× qui préserve la hauteur.
Usage: python3 sfx.py            → out/reel_01_v7.mp4
Les événements sont calés sur les mêmes ancres (T/E) que les visuels : la synchro est conservée."""
import os, sys, json, subprocess, numpy as np
from scipy.signal import lfilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B

R = B.R; SR = 44100; DUR = B.DUR; SPEED = 1.1
T, E = B.T, B.E
rng = np.random.default_rng(7)

def env_raised(n, a=.35):
    na = max(1, int(n * a)); e = np.ones(n)
    e[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na)); e[na:] = np.cos(np.linspace(0, np.pi / 2, n - na)) ** 2
    return e

def bandpass_coefs(fc, q):
    w0 = 2 * np.pi * fc / SR; al = np.sin(w0) / (2 * q)
    b = np.array([al, 0, -al]); a = np.array([1 + al, -2 * np.cos(w0), 1 - al])
    return b / a[0], a / a[0]

def woosh(dur=.5, direction="up", f0=500, f1=3800, level=.30):
    n = int(dur * SR); noise = rng.normal(0, 1, n); out = np.zeros(n); zi = np.zeros(2)
    blk = 256
    for s in range(0, n, blk):
        p = s / n; p = p if direction == "up" else 1 - p
        fc = f0 * (f1 / f0) ** p
        b, a = bandpass_coefs(fc, 1.4)
        seg, zi = lfilter(b, a, noise[s:s + blk], zi=zi); out[s:s + blk] = seg
    out *= env_raised(n, .45); out /= (np.abs(out).max() + 1e-9)
    return out * level

def tone(freq, dur=.16, level=.22, partials=((1, 1.0), (2, .25), (3, .08)), decay=7.0):
    t = np.arange(int(dur * SR)) / SR
    y = sum(a * np.sin(2 * np.pi * freq * k * t) for k, a in partials) * np.exp(-decay * t)
    y *= np.minimum(1, t / .004)  # attaque douce (pas de clic)
    return y / (np.abs(y).max() + 1e-9) * level

def pop(freq, level=.20):  # petite « bulle » : légère glissande montante
    dur = .14; t = np.arange(int(dur * SR)) / SR
    f = freq * (1 + .35 * (1 - np.exp(-t * 40)))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * np.minimum(1, t / .003)
    return y / (np.abs(y).max() + 1e-9) * level

def chime(freq=1318.5, dur=1.1, level=.20):  # scintillement pour le logo
    t = np.arange(int(dur * SR)) / SR; y = np.zeros_like(t)
    for k, (m, a, dly) in enumerate([(1, 1, 0), (1.5, .6, .09), (2, .45, .18), (3, .2, .27)]):
        tt = np.clip(t - dly, 0, None); y += a * np.sin(2 * np.pi * freq * m * tt) * np.exp(-4.5 * tt) * (t >= dly)
    y *= np.minimum(1, t / .005)
    return y / (np.abs(y).max() + 1e-9) * level

def check(level=.16): return tone(1568, .12, level, ((1, 1), (2, .2)), 14)

# -------------------------------------------------------------- événements (temps de la timeline d'origine, en secondes)
def events():
    ev = []
    def add(t, y, name): ev.append((float(t), y, name))
    # 1) cartes photo de l'accroche : petites bulles ascendantes (pentatonique) très discrètes
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 987.77, 1174.66, 1318.5, 1479.98]
    k = 0
    for c in range(3):
        for i in range(3):
            add(.1 + c * .22 + i * .12 + .18, pop(scale[k], .14), f"carte accroche {k+1}"); k += 1
    # 2) transitions : woosh directionnel au début de chaque transition (le jingle couvre l'entrée de la signature)
    add(B.T_DRESS + .05, woosh(.75, "up", 400, 3200), "iris → dressing")
    add(B.T_SIG + .30, tone(1046.5, .35, .10, ((1, 1), (2, .3)), 6), "signature (douce)")
    add(B.T_WARD, woosh(.6, "down", 3600, 500), "push → armoire")
    add(B.T_ASK, woosh(.75, "up", 350, 2600), "fondu-zoom → mannequin")
    add(B.T_EX1, woosh(.6, "up", 500, 3600), "wipe → exemple 1")
    add(B.T_EX2, woosh(.6, "up", 450, 3400), "push → exemple 2")
    add(B.T_LIST, woosh(.75, "up", 400, 3000), "iris → liste")
    add(B.T_THREE, woosh(.6, "down", 3600, 500), "push → 3 pièces")
    add(B.T_END, woosh(.65, "up", 450, 3600), "wipe → fin")
    # 3) apparitions d'images / cartes
    add(T("ناقص") - .05, tone(698.46, .35, .16, ((1, 1), (2, .3)), 5), "point d'interrogation")
    add(T("مثلاً") + .12, pop(784, .20), "mannequin (carte)")
    shoes = [T("صباط"), T("مريح"), T("كيناسبهم")]
    for i, ts in enumerate(shoes): add(ts + .04, pop([880, 988, 1109][i], .18), f"carte chaussures {i+1}")
    shoe_t = E("كيناسبهم") - .45
    add(shoe_t - .3, tone(1318.5, .30, .16, ((1, 1), (2, .25)), 6), "sélection mocassins")
    add(shoe_t, woosh(.5, "up", 500, 2800, .22), "mocassins → mannequin")
    add(T("عندك", 27) + .05, pop(784, .20), "carte robe")
    add(T("جاكيطة", 27), woosh(.5, "down", 3000, 600, .24), "veste qui arrive")
    add(T("جاكيطة", 27) + .2, pop(988, .18), "carte veste")
    add(T("تنسّقيها"), woosh(.8, "up", 400, 2800, .24), "veste → mannequin")
    add(T("تنسّقيها") + .55, chime(1174.7, .9, .12), "tenue complète")
    qs = [T("شنو", 35), T("لفين"), T("ومع")]
    for i, tt in enumerate(qs): add(tt + .9, check(), f"case cochée {i+1}")
    add(T("الحوايج") + .05, pop(880, .20), "note exemple")
    for i, tt in enumerate([T("بثلاث") + .1, T("حاجات") + .1, T("ليهم") - .1]): add(tt + .06, pop([784, 988, 1175][i], .20), f"carte pièce {i+1}")
    add(T("تابعيني") - .1 + .1, chime(1318.5, 1.1, .16), "logo")
    return sorted(ev, key=lambda e: e[0])

def build_track(ev):
    n = int(DUR * SR) + SR
    mix = np.zeros(n)
    for t, y, _ in ev:
        s = int(t * SR); mix[s:s + len(y)] += y[:max(0, n - s)] if s + len(y) <= n else y[:n - s]
    mix = mix[:int((DUR + .5) * SR)]
    peak = np.abs(mix).max()
    if peak > .9: mix *= .9 / peak
    return mix

def write_wav(path, y):
    import wave
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def main():
    ev = events(); track = build_track(ev)
    os.makedirs(os.path.join(R, "jingle"), exist_ok=True)
    wav = os.path.join(R, "jingle", "sfx_track.wav"); write_wav(wav, track)
    json.dump([(round(t, 3), n) for t, _, n in ev], open(os.path.join(R, "jingle", "sfx_events.json"), "w"), ensure_ascii=False, indent=1)
    print(len(ev), "événements sonores ; piste:", wav)
    out = os.path.join(R, "out", "reel_01_v7.mp4")
    fc = ("[1:a]volume=1.0,asplit=2[v][vsc];[2:a]adelay=5450|5450,volume=.9[j];"
          "[3:a]volume=.02,lowpass=f=420,tremolo=f=.22:d=.7[m];"
          "[4:a]aresample=48000,volume=.55,highpass=f=250[s0];"
          "[s0][vsc]sidechaincompress=threshold=0.015:ratio=12:attack=5:release=220:makeup=1[sd];"
          "[v][j][m][sd]amix=inputs=4:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5,"
          f"atempo={SPEED}[a]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", os.path.join(R, "out", "frames", "f%05d.jpg"),
           "-i", os.path.join(R, "voiceover.m4a"), "-i", os.path.join(R, "jingle", "signature_jingle.wav"),
           "-f", "lavfi", "-t", str(DUR), "-i", "sine=f=196:sample_rate=44100", "-i", wav,
           "-filter_complex", fc, "-filter:v", f"setpts=PTS/{SPEED},fps=30",
           "-map", "0:v", "-map", "[a]", "-t", f"{DUR / SPEED:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
           "-preset", "medium", "-c:a", "aac", "-b:a", "192k", out]
    subprocess.run(cmd, check=True); print("→", out)

if __name__ == "__main__":
    main()
