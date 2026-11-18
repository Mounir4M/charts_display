#!/usr/bin/env python3
"""Alignement mot par mot de la voix off sur le script.
Principe : phrases (groupes de souffle) détectées sur l'enveloppe audio et confirmées par Whisper ;
dans chaque phrase, les pauses internes sont calées sur la ponctuation du script, puis les mots sont
répartis au prorata de leur longueur sur le temps voisé et recalés sur les creux d'énergie."""
import sys, re, json, numpy as np
from vad import load, envelope

SCRIPT = [  # (début, fin) phrase audio, texte du script
 (0.62, 5.54, "البرومو قربات… ولكن واش عارفة شنو خاصك، ولا غادي تعرفيه غير ملي تشوفي التخفيضات؟"),
 (6.15, 9.39, "White Friday sans regret… avec IN&OUT."),
 (9.89, 15.35, "فهاد السلسلة، غادي نوجدو اختياراتنا خطوة بخطوة. وأول خطوة… كتبدأ قدّام البلاكار ديالك."),
 (15.80, 18.68, "تفكري فآخر مرة بغيتي توجدي راسك وبقيتي حايرة:"),
 (19.04, 21.93, "فين كنتي غادية؟ وشنو كان ناقص باش تكملي اللبسة؟"),
 (22.36, 27.22, "مثلاً، عندك سراول للخدمة، ولكن كتقلّبي على صباط مريح كيناسبهم."),
 (27.60, 35.59, "ولا عندك روبات كيعجبوك، وباقي خاصك جاكيطة تنسّقيها معاهم. خدي تيليفونك ديالك دابا وكتبي:"),
 (35.98, 36.68, "شنو ناقصني؟"),
 (37.13, 42.96, "لفين غنلبسو؟ ومع شنو من الحوايج اللي عندي؟ بداي بثلاث حاجات عندك ليهم استعمال واضح."),
 (43.46, 47.24, "فالحلقة الجاية، غنشوفو كيفاش تقارني بين القطع وتختاري اللي يناسبك."),
 (47.68, 50.20, "تابعيني باش نكملو هاد الخطوات مع بعضياتنا."),
]
PUNCT = "،,.؟?:…!"
def tokens(text):
    out = []
    for w in text.split():
        p = w[-1] if w[-1] in PUNCT else ""
        core = re.sub(r"[،,.؟?:…!]", "", w)
        if core: out.append((core, p))
    return out
def weight(w):
    if re.match(r"[A-Za-z&]", w): return {"White": 1, "Friday": 2, "sans": 1, "regret": 2, "avec": 2, "IN&OUT": 3}.get(w, max(1.0, 0.4 * len(w))) * 4
    letters = re.sub(r"[ً-ّْ]", "", w)
    return max(1.5, len(letters) + 0.5)

def main(wav, out):
    x, sr = load(wav); db, hop = envelope(x, sr)
    # lissage léger pour la recherche de creux
    k = np.ones(5) / 5; dbs = np.convolve(db, k, mode="same")
    peak = np.percentile(db, 95); thr = peak - 30
    words = []; report = []
    for (a, b, text) in SCRIPT:
        toks = tokens(text); n = len(toks)
        ia, ib = int(a / hop), int(b / hop)
        voiced = dbs[ia:ib] > thr
        # pauses internes (seuil plus sensible), hors bords du groupe de souffle
        pthr = peak - 24; vp = dbs[ia:ib] > pthr; pauses = []; s_ = None
        for i, v in enumerate(vp):
            if not v and s_ is None: s_ = i
            if v and s_ is not None:
                if (i - s_) * hop >= 0.07 and s_ > 12 and (len(vp) - i) > 12: pauses.append((a + s_ * hop, a + i * hop))
                s_ = None
        voiced = dbs[ia:ib] > thr
        w = np.array([weight(t[0]) for t in toks]); cum = np.concatenate([[0], np.cumsum(w)])
        # ancrage global (programmation dynamique) : chaque pause franche est associée à une frontière de mot
        bound_idx = [i + 1 for i, t in enumerate(toks[:-1]) if t[1]]
        P = [(p0, p1) for (p0, p1) in pauses if p1 - p0 >= 0.12]
        exp = {bi: a + (b - a) * cum[bi] / cum[-1] for bi in range(1, n)}
        INF = 1e9; K = n  # f[i][j] : coût minimal pour les i premières pauses, frontières utilisées < j
        f = [[INF] * (K + 1) for _ in range(len(P) + 1)]; back_ = {}
        for j in range(K + 1): f[0][j] = 0.0
        for i in range(1, len(P) + 1):
            c = (P[i - 1][0] + P[i - 1][1]) / 2
            for j in range(1, K + 1):
                best = (f[i - 1][j] + 0.45, ("skip", None))  # pause ignorée (fermeture de consonne)
                for bi in range(1, j):
                    dt = abs(c - exp[bi]); strong = toks[bi - 1][1] in ".؟?:…!"; pun = bool(toks[bi - 1][1])
                    cost = f[i - 1][bi] + dt - (0.25 if strong else 0.12 if pun else 0.0) - min(P[i - 1][1] - P[i - 1][0], .5) * .6
                    if cost < best[0]: best = (cost, ("use", bi))
                f[i][j] = best[0]; back_[(i, j)] = best[1]
        anchors = {}; i, j = len(P), K
        while i > 0:
            act = back_[(i, j)]
            if act[0] == "use": anchors[act[1]] = P[i - 1]; j = act[1]
            i -= 1
        # temps voisé cumulé
        vt = np.concatenate([[0], np.cumsum(voiced) * hop])  # voisé jusqu'à l'indice
        def v2t(v):  # temps voisé → temps réel
            i = int(np.searchsorted(vt, v)); return a + min(i, len(voiced)) * hop
        total_v = vt[-1]
        # frontières par segments entre ancres
        keys = [0] + sorted(anchors) + [n]; bounds = {}  # index mot → (fin mot précédent, début mot suivant)
        starts = [None] * n; ends = [None] * n; used_b = []
        for k0, k1 in zip(keys, keys[1:]):
            t0 = a if k0 == 0 else anchors[k0][1]; t1 = b if k1 == n else anchors[k1][0]
            i0, i1 = int((t0 - a) / hop), int((t1 - a) / hop)
            vloc = np.concatenate([[0], np.cumsum(voiced[i0:i1]) * hop]); tv = vloc[-1]
            seg_w = w[k0:k1]; cw = np.concatenate([[0], np.cumsum(seg_w)])
            for j in range(k0, k1 + 1):
                if j == k0: bt = t0
                elif j == k1: bt = t1
                else:
                    target = tv * cw[j - k0] / cw[-1]
                    ii = int(np.searchsorted(vloc, target)); bt = t0 + min(ii, i1 - i0) * hop
                    # recalage sur le creux d'énergie le plus proche (±80 ms)
                    near = [(abs((p0 + p1) / 2 - bt), (p0 + p1) / 2) for (p0, p1) in pauses if abs((p0 + p1) / 2 - bt) < 0.22 and (p1 - p0) >= 0.08 and all(abs((p0 + p1) / 2 - u) > 0.18 for u in used_b)]
                    if near: bt = min(near)[1]; used_b.append(bt)  # une micro-pause est une frontière de mot quasi certaine
                    else:
                        c = int((bt - a) / hop); lo, hi = max(c - 8, 0), min(c + 9, len(dbs[ia:ib]))
                        bt = a + (lo + int(np.argmin(dbs[ia + lo: ia + hi]))) * hop
                if j < k1: starts[j] = bt
                if j > k0: ends[j - 1] = bt
        for j in range(1, n):
            if starts[j] is not None and starts[j - 1] is not None and starts[j] < starts[j - 1] + 0.12: starts[j] = starts[j - 1] + 0.12; ends[j - 1] = starts[j]
        for j in range(n):
            if starts[j] is None: starts[j] = a
            if ends[j] is None: ends[j] = b
            words.append({"w": toks[j][0], "p": toks[j][1], "start": round(float(starts[j]), 3), "end": round(float(max(ends[j], starts[j] + .08)), 3), "seg": (a, b)})
        report.append((a, b, len(pauses), len(anchors), len(bound_idx)))
    json.dump(words, open(out, "w"), ensure_ascii=False, indent=1)
    for r in report: print("phrase %.2f-%.2f  pauses internes=%d  ancrées=%d / ponctuations=%d" % r)
    return words
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
