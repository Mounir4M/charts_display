#!/usr/bin/env python3
"""White Friday sans regret — épisode 01. Rend le Reel 1080x1920 @30fps.
Usage: python3 build.py   (voiceover.m4a + jingle/ + fonts/ requis)
Plans vidéo optionnels: footage/s1_dressing.mp4, s3_tenue.mp4, s4_exemples.mp4 (9:16)
sont incrustés automatiquement s'ils existent (sinon fond typographique)."""
import os, subprocess, math
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

R = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
IVORY, CHOC, BORD, SAND = (247, 241, 230), (74, 46, 36), (110, 22, 40), (224, 212, 192)
DUR = 51.73

def font(name, size, var=None):
    f = ImageFont.truetype(os.path.join(R, "fonts", name), size)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

AR = lambda s: font("Cairo%5Bslnt%2Cwght%5D.ttf", s, "Bold")
SERIF = lambda s: font("PlayfairDisplay%5Bwght%5D.ttf", s, "Bold")

from PIL import features
RAQM = features.check('raqm')
def ar(t): return t if RAQM else get_display(arabic_reshaper.reshape(t))
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def prog(t, a, d=0.5): return ease((t - a) / d)

def text(d, xy, s, f, fill, anchor="mm", arabic=True, alpha=1.0, bg=IVORY):
    if alpha <= 0: return
    c = tuple(int(bg[i] + (fill[i] - bg[i]) * alpha) for i in range(3))
    d.text(xy, ar(s) if arabic else s, font=f, fill=c, anchor=anchor)

# ---- sous-titres (début, fin, texte) — alignés sur le script + pauses détectées dans l'audio
SUBS = [
 (0.62, 2.40, "البرومو قربات…", 1), (2.40, 3.95, "ولكن واش عارفة شنو خاصك،", 1),
 (3.95, 5.54, "ولا غادي تعرفيه غير ملي تشوفي التخفيضات؟", 1),
 (6.15, 9.39, "White Friday sans regret… avec IN&OUT.", 0),
 (9.89, 12.5, "فهاد السلسلة، غادي نوجدو اختياراتنا خطوة بخطوة.", 1),
 (12.5, 15.35, "وأول خطوة… كتبدأ قدّام البلاكار ديالك.", 1),
 (15.80, 18.68, "تفكري فآخر مرة بغيتي توجدي راسك وبقيتي حايرة:", 1),
 (19.04, 21.93, "فين كنتي غادية؟ وشنو كان ناقص باش تكملي اللبسة؟", 1),
 (22.36, 27.22, "مثلاً، عندك سراول للخدمة، ولكن كتقلّبي على صباط مريح كيناسبهم.", 1),
 (27.60, 36.68, "ولا عندك روبات كيعجبوك، وباقي خاصك جاكيطة تنسّقيها معاهم.", 1),
 (37.13, 42.96, "خدي تيليفونك وكتبي: شنو ناقصني؟ لفين غنلبسو؟ ومع شنو من الحوايج اللي عندي؟", 1),
 (43.46, 47.24, "بداي بثلاث حاجات عندك ليهم استعمال واضح.", 1),
 (47.68, 49.0, "فالحلقة الجاية، غنشوفو كيفاش تقارني بين القطع وتختاري اللي يناسبك.", 1),
 (49.0, 50.2, "تابعيني باش نكملو هاد الخطوات مع بعضياتنا.", 1),
]

def wrap(d, s, f, maxw, arabic):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(ar(t) if arabic else t, font=f) > maxw and cur:
            lines.append(cur); cur = w
        else: cur = t
    lines.append(cur)
    return lines[:2] if len(lines) <= 2 else [" ".join(words[:len(words)//2]), " ".join(words[len(words)//2:])]

def draw_subs(d, t):
    for a, b, s, isar in SUBS:
        if a <= t < b:
            f = AR(46) if isar else font("Cairo%5Bslnt%2Cwght%5D.ttf", 44, "SemiBold")
            lines = wrap(d, s, f, 860, isar)
            y0 = 1480  # zone de sécurité Instagram: au-dessus de l'UI du bas (≈ 250 px)
            pad = 26; h = len(lines) * 66 + pad * 2
            box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box)
            bd.rounded_rectangle((90, y0 - pad, W - 90, y0 - pad + h), 28, fill=(74, 46, 36, 215))
            return box, lines, f, y0, isar
    return None

def vid_frame(name, t):
    p = os.path.join(R, "footage", name)
    return p if os.path.exists(p) else None

# ---- scènes
def scene(t):
    img = Image.new("RGB", (W, H), IVORY); d = ImageDraw.Draw(img)
    # lignes éditoriales discrètes
    d.line((90, 150, W - 90, 150), fill=SAND, width=3); d.line((90, H - 330, W - 90, H - 330), fill=SAND, width=3)
    text(d, (90, 110), "ACADÉMIE IN&OUT", font("Cairo%5Bslnt%2Cwght%5D.ttf", 28, "SemiBold"), CHOC, "lm", False)
    text(d, (W - 90, 110), "N° 01", SERIF(30), BORD, "rm", False)

    if t < 5.5:  # 1. accroche — écran promo stylisé sans remise, puis dressing
        if t < 2.6:
            for i in range(3):
                x = 140 + i * 30 + (1 - prog(t, 0.1 + i * 0.25, 0.6)) * 900
                d.rounded_rectangle((x, 380 + i * 330, x + 640, 640 + i * 330), 36, fill=[CHOC, BORD, SAND][i])
                d.ellipse((x + 40, 420 + i * 330, x + 150, 530 + i * 330), fill=IVORY)
                d.rounded_rectangle((x + 190, 440 + i * 330, x + 560, 470 + i * 330), 14, fill=IVORY)
                d.rounded_rectangle((x + 190, 500 + i * 330, x + 470, 524 + i * 330), 12, fill=IVORY)
            text(d, (W // 2, 1280), "PROMO", SERIF(90), BORD, "mm", False, prog(t, 0.8))
        else:  # dressing ouvert (barre + cintres)
            u = prog(t, 2.6, 0.7)
            d.rectangle((140, 560, W - 140, 580), fill=CHOC)
            cols = [(90, 60, 50), BORD, (205, 190, 165), (60, 40, 35), (150, 120, 95)]
            for i, c in enumerate(cols):
                x = 250 + i * 150
                d.polygon([(x, 580), (x + 50, 620), (x + 100, 580)], outline=CHOC, width=4)
                d.rounded_rectangle((x - 20, 620, x + 120, max(641, 620 + int(700 * u) - 80 * (i % 2))), 20, fill=c)
        text(d, (W // 2, 360), "عارفة شنو خاصك؟", AR(120), CHOC, "mm", True, prog(t, 1.2, 0.6))
    elif t < 9.9:  # 2. signature
        a = prog(t, 5.55, 0.5)
        text(d, (W // 2, 700), "White Friday", SERIF(130), CHOC, "mm", False, a)
        text(d, (W // 2, 840), "sans regret", SERIF(130), CHOC, "mm", False, prog(t, 6.2, 0.5))
        d.line((W // 2 - 140, 940, W // 2 + 140, 940), fill=BORD, width=6)
        text(d, (W // 2, 1040), "avec IN&OUT", font("PlayfairDisplay%5Bwght%5D.ttf", 84, "Italic" if False else "Bold"), BORD, "mm", False, prog(t, 7.4, 0.5))
        text(d, (W // 2, 1250), "01 — شنو ناقصني؟", AR(84), CHOC, "mm", True, prog(t, 8.5, 0.5))
    elif t < 15.8:  # 3. série
        text(d, (W // 2, 560), "خطوة بخطوة", AR(130), CHOC, "mm", True, prog(t, 10.0))
        text(d, (W // 2, 780), "الخطوة الأولى", AR(70), BORD, "mm", True, prog(t, 11.5))
        text(d, (W // 2, 1000), "قدّام البلاكار", AR(110), CHOC, "mm", True, prog(t, 13.0))
    elif t < 22.4:  # 4. situation: tenue commencée
        text(d, (W // 2, 520), "كنتي غادية فين؟", AR(100), CHOC, "mm", True, prog(t, 15.9))
        for i, (lab, c) in enumerate([("سراول", CHOC), ("جاكيطة", (150, 120, 95)), ("؟", None)]):
            x, y = W // 2, 800 + i * 230
            a = prog(t, 18.0 + i * 1.2)
            if c: d.rounded_rectangle((250, y - 80, W - 250, y + 80), 40, fill=tuple(int(IVORY[k] + (c[k] - IVORY[k]) * a) for k in range(3)))
            else: d.rounded_rectangle((250, y - 80, W - 250, y + 80), 40, outline=BORD, width=6)
            text(d, (x, y), lab, AR(80), IVORY if c else BORD, "mm", True, a, bg=IVORY if not c else IVORY)
    elif t < 36.7:  # 5. deux exemples
        ex = t < 27.5
        k0 = 22.4 if ex else 27.6
        pairs = [("سراول للخدمة", "صباط مريح؟"), ("روب", "جاكيطة؟")][0 if ex else 1]
        text(d, (W // 2, 520), "مثال " + ("1" if ex else "2"), AR(70), BORD, "mm", True, prog(t, k0))
        d.rounded_rectangle((200, 700, W - 200, 960), 46, fill=CHOC)
        text(d, (W // 2, 830), pairs[0], AR(90), IVORY, "mm", True, prog(t, k0 + 0.4))
        text(d, (W // 2, 1060), "+", SERIF(100), BORD, "mm", False, prog(t, k0 + 1.4))
        d.rounded_rectangle((200, 1150, W - 200, 1410), 46, outline=BORD, width=7)
        text(d, (W // 2, 1280), pairs[1], AR(90), BORD, "mm", True, prog(t, k0 + 2.0))
    elif t < 44:  # 6. liste pratique (notes qui se remplissent)
        d.rounded_rectangle((110, 330, W - 110, 1400), 40, fill=(255, 251, 243), outline=SAND, width=4)
        qs = ["شنو ناقصني؟", "لفين غنلبسو؟", "مع شنو غننسّقو؟"]
        for i, q in enumerate(qs):
            a = prog(t, 37.4 + i * 1.7)
            text(d, (W - 190, 520 + i * 200), q, AR(78), CHOC, "rm", True, a, bg=(255, 251, 243))
            d.ellipse((150, 480 + i * 200, 210, 540 + i * 200), outline=BORD, width=5)
            if a > 0.95: d.line((162, 512 + i * 200, 178, 530 + i * 200, 204, 490 + i * 200), fill=BORD, width=7)
        a = prog(t, 43.0, 0.5)
        text(d, (W // 2, 1180), "صباط مريح — للخدمة", AR(66), BORD, "mm", True, a, bg=(255, 251, 243))
        text(d, (W // 2, 1280), "مع السراول اللي عندي", AR(66), BORD, "mm", True, prog(t, 43.2, 0.5), bg=(255, 251, 243))
    else:  # 7. fin
        text(d, (W // 2, 560), "الحلقة الجاية:", AR(80), BORD, "mm", True, prog(t, 47.7))
        text(d, (W // 2, 720), "كيفاش نقارنو ونختارو؟", AR(84), CHOC, "mm", True, prog(t, 48.0))
        text(d, (W // 2, 980), "تابعيني باش نكملو الخطوات", AR(70), CHOC, "mm", True, prog(t, 49.2))
        text(d, (W // 2, 1250), "Académie IN&OUT · Btissam Goumara", font("Cairo%5Bslnt%2Cwght%5D.ttf", 36, "SemiBold"), CHOC, "mm", False, prog(t, 50.0))
    return img

def main():
    out = os.path.join(R, "out"); fr = os.path.join(out, "frames"); os.makedirs(fr, exist_ok=True)
    n = int(DUR * FPS)
    for i in range(n):
        t = i / FPS
        img = scene(t).convert("RGBA")
        d = ImageDraw.Draw(img)
        s = draw_subs(d, t)
        if s:
            box, lines, f, y0, isar = s
            img = Image.alpha_composite(img, box); d = ImageDraw.Draw(img)
            for j, l in enumerate(lines):
                d.text((W // 2, y0 + 33 + j * 66), ar(l) if isar else l, font=f, fill=IVORY, anchor="mm")
        img.convert("RGB").save(os.path.join(fr, f"f{i:05d}.jpg"), quality=92)
    jingle = os.path.join(R, "jingle", "signature_jingle.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(fr, "f%05d.jpg"),
           "-i", os.path.join(R, "voiceover.m4a"), "-i", jingle,
           "-f", "lavfi", "-t", str(DUR), "-i", "sine=f=220:sample_rate=44100",
           "-filter_complex",
           "[1:a]volume=1.0[v];[2:a]adelay=5400|5400,volume=0.9[j];"
           "[3:a]volume=0.025,lowpass=f=500,tremolo=f=0.25:d=0.6[m];"
           "[v][j][m]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5[a]",
           "-map", "0:v", "-map", "[a]", "-t", str(DUR), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-c:a", "aac", "-b:a", "192k", os.path.join(out, "reel_01_v1.mp4")]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
