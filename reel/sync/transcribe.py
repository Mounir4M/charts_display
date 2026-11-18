#!/usr/bin/env python3
"""Transcrit la voix off avec Whisper (sherpa-onnx) et exporte les horodatages par token.
Usage: transcribe.py MODEL_DIR PREFIX WAV16K OUT.json [lang]"""
import sys, json, wave, numpy as np, sherpa_onnx as so
model_dir, prefix, wav_path, out = sys.argv[1:5]
lang = sys.argv[5] if len(sys.argv) > 5 else "ar"
rec = so.OfflineRecognizer.from_whisper(
    encoder=f"{model_dir}/{prefix}-encoder.int8.onnx", decoder=f"{model_dir}/{prefix}-decoder.int8.onnx",
    tokens=f"{model_dir}/{prefix}-tokens.txt", language=lang, task="transcribe", num_threads=4,
    enable_token_timestamps=True, enable_segment_timestamps=True)
with wave.open(wav_path) as w:
    sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
# découpe aux silences (<30 s par fenêtre Whisper)
cuts = [0.0, 22.15, 47.45, len(x) / sr]
res = []
for a, b in zip(cuts, cuts[1:]):
    seg = x[int(a * sr):int(b * sr)]
    s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s); r = s.result
    toks = [{"t": tk, "start": round(a + ts, 3)} for tk, ts in zip(r.tokens, r.timestamps)]
    res.append({"chunk": [a, b], "text": r.text, "tokens": toks, "seg_ts": list(getattr(r, "segment_timestamps", []) or [])})
    print(f"[{a:.1f}-{b:.1f}] {r.text}", flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
