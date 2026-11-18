#!/usr/bin/env python3
"""Détection de la parole (enveloppe RMS) → intervalles voisés et pauses."""
import sys, json, wave, numpy as np
def load(p):
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x, sr
def envelope(x, sr, hop=0.01, win=0.025):
    h, n = int(hop * sr), int(win * sr)
    e = np.array([np.sqrt(np.mean(x[i:i + n] ** 2) + 1e-12) for i in range(0, len(x) - n, h)])
    return 20 * np.log10(e + 1e-9), hop
def intervals(db, hop, thr_db, min_gap, min_len=0.08):
    act = db > thr_db; segs = []; s = None
    for i, a in enumerate(act):
        if a and s is None: s = i
        if not a and s is not None: segs.append([s * hop, i * hop]); s = None
    if s is not None: segs.append([s * hop, len(act) * hop])
    m = []
    for a, b in segs:
        if m and a - m[-1][1] < min_gap: m[-1][1] = b
        else: m.append([a, b])
    return [(round(a, 3), round(b, 3)) for a, b in m if b - a >= min_len]
if __name__ == "__main__":
    x, sr = load(sys.argv[1]); db, hop = envelope(x, sr)
    peak = np.percentile(db, 95); print("p95 dB", round(peak, 1), "floor", round(np.percentile(db, 5), 1))
    ph = intervals(db, hop, peak - 28, 0.30)
    print(len(ph), "phrases:"); [print(f"  {a:6.2f} – {b:6.2f}  ({b-a:.2f}s)") for a, b in ph]
    json.dump(ph, open(sys.argv[2], "w"))
