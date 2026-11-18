#!/usr/bin/env python3
"""Transcrit chaque groupe de souffle séparément (Whisper via sherpa-onnx)."""
import sys, json, wave, numpy as np, sherpa_onnx as so
model_dir, prefix, wav, out = sys.argv[1:5]
SEG = [(0.62, 5.54), (6.15, 9.39), (9.89, 15.35), (15.80, 18.68), (19.04, 21.93), (22.36, 27.22), (27.60, 35.59), (35.98, 36.68), (37.13, 42.96), (43.46, 47.24), (47.68, 50.20)]
rec = so.OfflineRecognizer.from_whisper(encoder=f"{model_dir}/{prefix}-encoder.int8.onnx", decoder=f"{model_dir}/{prefix}-decoder.int8.onnx",
    tokens=f"{model_dir}/{prefix}-tokens.txt", language="ar", task="transcribe", num_threads=4)
with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
res = []
for a, b in SEG:
    s = rec.create_stream(); s.accept_waveform(sr, x[int(max(0, a - .15) * sr):int((b + .15) * sr)]); rec.decode_stream(s)
    res.append({"start": a, "end": b, "text": s.result.text.strip()}); print(f"{a:6.2f}-{b:6.2f} {s.result.text.strip()}", flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
