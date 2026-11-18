#!/usr/bin/env python3
"""White Friday sans regret — épisode 01 (version animée, images + transitions).
Usage: python3 build.py [numéros d'images]   → out/reel_01_v3.mp4
Pré-requis: voiceover.m4a, jingle/signature_jingle.wav, fonts/, art.py"""
import os, sys, math, subprocess
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageChops
import art

R = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 51.73
IVORY, CHOC, BORD, SAND, SANDD = (248, 239, 234), (40, 39, 34), (127, 74, 34), (204, 178, 151), (233, 220, 207)
OCRE, CARAMEL = (208, 154, 68), (179, 113, 55)
CAIRO, PLAY = "Cairo%5Bslnt%2Cwght%5D.ttf", "CormorantGaramond%5Bwght%5D.ttf"
AMIRI = "Amiri-Bold.ttf"

# ---------------------------------------------------------------- utilitaires
_fc, _tc, _cache = {}, {}, {}
def font(name, size, var="Bold"):
    if name == AMIRI: size = int(size * 1.1)
    k = (name, size, var)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(R, "fonts", name), size)
        try: f.set_variation_by_name(var)
        except Exception: pass
        _fc[k] = f
    return _fc[k]

def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def easeio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def pr(t, a, d=.6, f=ease): return f((t - a) / d)
def lerp(a, b, k): return a + (b - a) * k
def cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]

def with_alpha(im, al):
    if al >= .999: return im
    if al <= 0: return None
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * al))))

def paste(dst, im, x, y, al=1.0):
    if im is None: return
    im = with_alpha(im, al)
    if im is None: return
    dst.paste(im, (int(x), int(y)), im)

def paste_c(dst, im, cx, cy, al=1.0, s=1.0):
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    paste(dst, im, cx - im.width / 2, cy - im.height / 2, al)

def text_layer(s, name, size, color, var="Bold"):
    key = (s, name, size, color, var)
    if key in _tc: return _tc[key]
    f = font(name, size, var)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    b = d.textbbox((0, 0), s, font=f, anchor="ls")
    pad = 16
    w, h = int(b[2] - b[0]) + pad * 2, int(b[3] - b[1]) + pad * 2
    im = Image.new("RGBA", (w, h), color + (0,))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, font=f, fill=color + (255,), anchor="ls")
    _tc[key] = im
    return im

def put_text(dst, s, cx, cy, name, size, color, t, t0, dur=.7, mode="wipe_r", var="Bold", al=1.0, rise=36):
    p = pr(t, t0, dur)
    if p <= 0: return
    im = text_layer(s, name, size, color, var)
    if mode in ("wipe_r", "wipe_l"):
        w = int(im.width * p)
        if w < 1: return
        box = (im.width - w, 0, im.width, im.height) if mode == "wipe_r" else (0, 0, w, im.height)
        paste(dst, im.crop(box), cx - im.width / 2 + box[0], cy - im.height / 2, al)
    else:  # rise
        paste(dst, im, cx - im.width / 2, cy - im.height / 2 + (1 - p) * rise, al * p)

def chip(dst, s, cx, cy, fg, bg, t, t0, size=50, outline=None, pad=(44, 22), al=1.0):
    p = pr(t, t0, .5, back)
    if p <= 0: return
    im = text_layer(s, AMIRI, int(size * 1.2), fg)
    w, h = im.width - 32 + pad[0] * 2, im.height - 32 + pad[1] * 2
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(base)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(bg + (255,)) if bg else None, outline=(outline + (255,)) if outline else None, width=5)
    base.paste(im, (pad[0] - 16, pad[1] - 16), im)
    paste_c(dst, base, cx, cy, al * clamp(p * 2), max(.01, p))

def noise_tile(i):
    rng = np.random.default_rng(100 + i)
    n = rng.normal(128, 28, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(n).resize((W, H), Image.NEAREST).convert("RGB")

def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * .75)) ** 2 + ((y - H / 2) / (H * .75)) ** 2)
    return Image.fromarray((np.clip(d - .55, 0, 1) * 60).astype(np.uint8))

def bg_ivory():
    def mk():
        y = np.linspace(0, 1, H)[:, None, None]
        a = np.array(IVORY, np.float32) * (1 - .035 * y) + np.array(SANDD, np.float32) * (.035 * y)
        return Image.fromarray(np.broadcast_to(a, (H, W, 3)).astype(np.uint8))
    return cached("bg_ivory", mk).copy()

def bg_bord():
    def mk():
        y = np.linspace(0, 1, H)[:, None, None]
        a = np.array(BORD, np.float32) * (1 - .35 * y) + np.array((96, 55, 24), np.float32) * (.35 * y)
        return Image.fromarray(np.broadcast_to(a, (H, W, 3)).astype(np.uint8))
    return cached("bg_bord", mk).copy()

def header(im, dark=False):
    d = ImageDraw.Draw(im); c = IVORY if dark else CHOC; c2 = SAND if dark else BORD
    d.text((90, 112), "ACADÉMIE IN&OUT", font=font(PLAY, 32, "Bold"), fill=c, anchor="lm")
    d.text((W - 90, 112), "N° 01", font=font(PLAY, 30), fill=c2, anchor="rm")
    d.line((90, 152, W - 90, 152), fill=(176, 130, 92) if dark else SANDD, width=3)

def zellige_band(im, y, a=.35):
    z = cached("zel", lambda: art.zellige(W, 100, (205, 185, 155), (247, 241, 230), 100))
    paste(im, z, 0, y, a)

def sprites():
    def mk():
        return {"flats": art.make_flats(), "work": art.outfit_layers("work"), "dress": art.outfit_layers("dress"),
                "door": art.wood_door(560, 1380), "arch": art.arch(660, 1280, SANDD)}
    return cached("sprites", mk)

def figure(dst, kind, cx, top, s, t, t0, parts, appear=None):
    for name, im in sprites()[kind]:
        if name != "body" and name not in parts: continue
        ta = (appear or {}).get(name, t0)
        p = pr(t, ta, .55, back) if name != "body" else pr(t, t0 - .3, .5)
        if p <= 0: continue
        off = (1 - clamp(p)) * 60 if name != "body" else 0
        l = im if s == 1 else im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        paste(dst, l, cx - 350 * s, top - off, clamp(p * 1.6))

# ---------------------------------------------------------------- scènes
def _tag():
    im = Image.new("RGBA", (300, 190), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(40, 95), (100, 20), (280, 20), (280, 170), (100, 170)], fill=IVORY + (255,))
    d.ellipse((84, 78, 116, 110), fill=BORD + (255,))
    d.rounded_rectangle((140, 66, 250, 84), 9, fill=SAND + (255,)); d.rounded_rectangle((140, 104, 220, 120), 8, fill=SAND + (255,))
    return im

def _notif(i):
    def mk():
        im = Image.new("RGBA", (700, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, 699, 149), 36, fill=(247, 241, 230, 235))
        d.ellipse((28, 32, 114, 118), fill=[CHOC, BORD, (176, 124, 82)][i] + (255,))
        d.rounded_rectangle((140, 40, 560, 66), 13, fill=(190, 176, 156, 255)); d.rounded_rectangle((140, 84, 440, 106), 11, fill=(215, 203, 184, 255))
        return im
    return cached(("notif", i), mk)

def s_promo(t):
    im = bg_bord(); d = ImageDraw.Draw(im)
    for i, (r, c) in enumerate([(420, (143, 88, 44)), (300, (158, 99, 50)), (200, (176, 114, 58))]):
        cx, cy = 300 + i * 260 + math.sin(t * .8 + i) * 30, 700 + i * 340 - t * 25
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    tag = cached("tag", _tag)
    for i, (x, y, rot) in enumerate([(260, 640, -14), (720, 540, 10), (480, 980, -6), (800, 1180, 16), (200, 1250, 8)]):
        p = pr(t, .1 + i * .18, .7, back)
        im2 = tag.rotate(rot + math.sin(t * 1.2 + i) * 3, Image.BICUBIC, expand=True)
        paste_c(im, im2, x, y + (1 - p) * 500 - t * (12 + 5 * i), clamp(p * 1.5), 1.0 + .25 * (i % 2))
    for i in range(3):
        p = pr(t, .3 + i * .25, .8, back)
        paste_c(im, _notif(i), 540, 760 + i * 190 - (1 - p) * 700, clamp(p * 1.5))
    header(im, True)
    put_text(im, "عارفة شنو خاصك؟", 540, 330, AMIRI, 112, IVORY, t, 1.1, .8, "wipe_r")
    return im

def hanging_rack(im, t, cx, y_bar, items, scale=.5, gap=250):
    ImageDraw.Draw(im).rounded_rectangle((cx - 460, y_bar - 8, cx + 460, y_bar + 8), 8, fill=(120, 86, 64))
    F = sprites()["flats"]; n = len(items)
    for i, k in enumerate(items):
        hi = cached(("hang", k), lambda k=k: art.hanger_item(F[k]))
        im2 = hi.resize((int(hi.width * scale), int(hi.height * scale)), Image.LANCZOS)
        im2 = im2.rotate(math.sin(t * 1.4 + i * 1.3) * 2.2, Image.BICUBIC, expand=True, center=(im2.width / 2, 0))
        paste(im, im2, cx - (n - 1) * gap / 2 + i * gap - im2.width / 2, y_bar - 40)

def s_dressing(t):
    im = bg_ivory()
    p = pr(t, 2.2, 1.0)
    paste(im, sprites()["arch"], 210, 260 - (1 - p) * 80, p)
    header(im); zellige_band(im, 1560)
    hanging_rack(im, t, 540, 520, ["dress", "blazer", "top"], scale=.55, gap=300)
    put_text(im, "عارفة شنو خاصك؟", 540, 330, AMIRI, 112, CHOC, t, 1.1, .01, "wipe_r")
    return im

def s_sig(t):
    im = bg_bord(); d = ImageDraw.Draw(im)
    d.ellipse((-300, 1100, 700, 2100), fill=(143, 88, 44)); d.ellipse((500, -300, 1300, 500), fill=(143, 88, 44))
    header(im, True)
    put_text(im, "White Friday", 540, 700, PLAY, 138, IVORY, t, 5.7, .8, "wipe_l")
    put_text(im, "sans regret", 540, 860, PLAY, 138, IVORY, t, 6.4, .8, "wipe_l")
    p = pr(t, 7.2, .7)
    d.line((540 - 150 * p, 960, 540 + 150 * p, 960), fill=OCRE, width=5)
    put_text(im, "avec IN&OUT", 540, 1060, PLAY, 90, SAND, t, 7.6, .7, "rise")
    chip(im, "01 — شنو ناقصني؟", 540, 1330, BORD, IVORY, t, 8.5, 60)
    return im

def s_wardrobe(t):
    im = bg_ivory(); d = ImageDraw.Draw(im)
    header(im)
    d.rectangle((90, 190, W - 90, 1470), fill=(214, 194, 164)); d.rectangle((90, 190, W - 90, 400), fill=(200, 178, 148))
    hanging_rack(im, t, 540, 560, ["blazer", "dress", "top"], scale=.5, gap=300)
    F = sprites()["flats"]
    for i, k in enumerate(["loafer", "sneaker", "boot"]):
        paste_c(im, F[k], 340 + i * 200, 1390, 1.0, .6)
    dr = sprites()["door"]; op = easeio((t - 12.9) / 1.8)
    paste(im, dr, 90 - 530 * op, 190)
    paste(im, dr.transpose(Image.FLIP_LEFT_RIGHT), 530 + 520 * op, 190)
    if op < .98:
        d.rounded_rectangle((520 - 530 * op, 760, 534 - 530 * op, 960), 7, fill=(92, 62, 44))
        d.rounded_rectangle((546 + 520 * op, 760, 560 + 520 * op, 960), 7, fill=(92, 62, 44))
    put_text(im, "خطوة بخطوة", 540, 330, AMIRI, 120, CHOC, t, 10.3, .8, "wipe_r")
    put_text(im, "قدّام البلاكار", 540, 470, AMIRI, 84, BORD, t, 13.2, .8, "wipe_r")
    return im

def s_ask(t):
    im = bg_ivory(); header(im)
    paste(im, sprites()["arch"], 210, 250)
    figure(im, "work", 540, 250, .86, t, 16.1, ["top", "trousers"], {"top": 16.3, "trousers": 17.0})
    p = pr(t, 18.2, .6, back)
    if p > 0:
        pulse = 1 + .08 * math.sin((t - 18.2) * 5)
        paste_c(im, text_layer("؟", AMIRI, 150, BORD), 540, 1300, clamp(p), pulse)
        r = 90 * pulse; ImageDraw.Draw(im).ellipse((540 - r, 1300 - r, 540 + r, 1300 + r), outline=BORD, width=6)
    put_text(im, "فين كنتي غادية؟", 540, 300, AMIRI, 92, CHOC, t, 16.0, .7, "wipe_r")
    return im

def ex_layout(im):
    paste(im, sprites()["arch"].resize((430, 880), Image.LANCZOS), 90, 360)
    header(im); zellige_band(im, 1560)

def s_ex1(t):
    im = bg_ivory(); ex_layout(im)
    F = sprites()["flats"]; shoe_t = 26.7
    parts = ["top", "trousers"] + (["shoes"] if t > shoe_t + .3 else [])
    figure(im, "work", 305, 330, .62, t, 22.4, parts, {"top": 22.4, "trousers": 22.5, "shoes": shoe_t + .3})
    chip(im, "عندك", 305, 300, IVORY, CHOC, t, 23.1, 44)
    chip(im, "سراول للخدمة", 305, 1330, CHOC, None, t, 23.2, 44, outline=CHOC)
    put_text(im, "صباط مريح؟", 790, 440, AMIRI, 62, BORD, t, 23.6, .6, "wipe_r")
    for i, k in enumerate(["loafer", "sneaker", "boot"]):
        p = pr(t, 23.9 + i * .45, .7, back)
        keep = i == 0
        fade = 1.0 if (keep or t < shoe_t) else max(.25, 1 - (t - shoe_t) * 2.0)
        bx, by, sc = 790, 640 + i * 230, .78
        if keep and t > shoe_t:
            q = pr(t, shoe_t, .6, easeio)
            bx, by, sc = lerp(790, 330, q), lerp(by, 1310, q), lerp(.78, .6, q)
            fade = 1 - pr(t, shoe_t + .35, .35)
            p = 1
        paste_c(im, F[k], bx + (1 - p) * 500, by, clamp(p * 1.4) * fade, sc)
        if keep and shoe_t - .6 < t < shoe_t + .5:
            rr = pr(t, shoe_t - .6, .4, back)
            ImageDraw.Draw(im).rounded_rectangle((790 - 170 * rr, by - 84 * rr, 790 + 170 * rr, by + 84 * rr), 40, outline=BORD, width=6)
    return im

def s_ex2(t):
    im = bg_ivory(); ex_layout(im)
    F = sprites()["flats"]; bl_t = 33.4; s = .62
    figure(im, "dress", 305, 330, s, t, 27.9, ["shoes", "dress"], {"shoes": 27.9, "dress": 28.1})
    chip(im, "عندك", 305, 300, IVORY, CHOC, t, 28.8, 44)
    put_text(im, "جاكيطة؟", 790, 440, AMIRI, 70, BORD, t, 30.0, .6, "wipe_r")
    tx, ty = 305 - 350 * s + 156 * s, 330 + 206 * s
    bl = F["blazer"]
    if t < bl_t:
        p = pr(t, 30.5, .9, back)
        ImageDraw.Draw(im).rounded_rectangle((640, 520, 940, 1040), 60, outline=BORD, width=5)
        paste_c(im, bl, 790 + (1 - p) * 500, 780, clamp(p * 1.4), .58)
    elif t < bl_t + .9:
        q = pr(t, bl_t, .8, easeio)
        paste_c(im, bl, lerp(790, tx + bl.width * s / 2, q), lerp(780, ty + bl.height * s / 2, q), 1.0, lerp(.58, s, q))
    else:
        paste(im, bl.resize((int(bl.width * s), int(bl.height * s)), Image.LANCZOS), tx, ty)
    chip(im, "قطعة وحدة، ماشي لبسة كاملة", 540, 1420, IVORY, BORD, t, 34.6, 48)
    return im

def phone_sprite():
    def mk():
        w, h = 640, 1240
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 78, fill=(40, 28, 24, 255))
        d.rounded_rectangle((18, 18, w - 19, h - 19), 62, fill=(252, 247, 238, 255))
        d.rounded_rectangle((w // 2 - 70, 34, w // 2 + 70, 62), 14, fill=(40, 28, 24, 255))
        d.rectangle((18, 90, w - 19, 210), fill=BORD + (255,))
        for i in range(8): d.line((40, 330 + i * 130, w - 40, 330 + i * 130), fill=(226, 214, 194, 255), width=3)
        return im
    return cached("phone", mk)

def s_list(t):
    im = bg_ivory(); header(im); d = ImageDraw.Draw(im)
    p = pr(t, 37.3, .9, back)
    cx, cy = 540, 840 + (1 - p) * 900
    paste_c(im, phone_sprite(), cx, cy, clamp(p * 1.5))
    if p > .6:
        ox, oy = cx - 320, cy - 620
        put_text(im, "ملاحظات", cx, oy + 150, AMIRI, 60, IVORY, t, 37.9, .5, "wipe_r")
        for i, (q, tt) in enumerate(zip(["شنو ناقصني؟", "لفين غنلبسو؟", "مع شنو غننسّقو؟"], [38.2, 39.7, 41.2])):
            y = oy + 330 + i * 130
            if pr(t, tt, .7) > 0:
                put_text(im, q, cx + 250 - text_layer(q, AMIRI, 58, CHOC).width / 2 + 16, y, AMIRI, 58, CHOC, t, tt, .7, "wipe_r")
                d.ellipse((ox + 52, y - 26, ox + 104, y + 26), outline=BORD, width=5)
                if t > tt + .8:
                    d.line((ox + 62, y, ox + 76, y + 14), fill=BORD, width=7); d.line((ox + 76, y + 14, ox + 98, y - 18), fill=BORD, width=7)
        pn = pr(t, 42.8, .6, back)
        if pn > 0:
            note = Image.new("RGBA", (560, 250), (0, 0, 0, 0)); ImageDraw.Draw(note).rounded_rectangle((0, 0, 559, 249), 26, fill=(236, 214, 176, 255))
            a = text_layer("صباط مريح — للخدمة", AMIRI, 44, BORD); b = text_layer("مع السراول اللي عندي", AMIRI, 44, BORD)
            note.paste(a, (280 - a.width // 2, 40), a); note.paste(b, (280 - b.width // 2, 140), b)
            paste_c(im, note.rotate(-3, Image.BICUBIC, expand=True), cx, oy + 880, clamp(pn * 1.5), pn)
    return im

def s_three(t):
    im = bg_ivory(); header(im); zellige_band(im, 1560); d = ImageDraw.Draw(im)
    put_text(im, "٣ حاجات", 540, 380, AMIRI, 150, CHOC, t, 43.7, .7, "wipe_r")
    F = sprites()["flats"]
    for i, (k, s) in enumerate([("trousers", .30), ("dress", .32), ("blazer", .42)]):
        p = pr(t, 44.2 + i * .5, .7, back); x = 230 + i * 310
        if p > 0:
            r = 140 * p; d.ellipse((x - r, 860 - r, x + r, 860 + r), fill=SANDD)
            paste_c(im, F[k], x, 860, clamp(p * 1.4), s * p)
            if p > .8: d.text((x, 1100), str(i + 1), font=font(PLAY, 90), fill=OCRE, anchor="mm")
    put_text(im, "استعمال واضح", 540, 1320, AMIRI, 74, BORD, t, 46.1, .7, "wipe_r")
    return im

def s_end(t):
    im = bg_bord(); d = ImageDraw.Draw(im)
    d.ellipse((-300, 1200, 700, 2200), fill=(143, 88, 44)); d.ellipse((560, -250, 1360, 550), fill=(143, 88, 44))
    header(im, True)
    put_text(im, "الحلقة الجاية:", 540, 640, AMIRI, 70, SAND, t, 48.0, .6, "wipe_r")
    put_text(im, "كيفاش نقارنو", 540, 800, AMIRI, 112, IVORY, t, 48.3, .7, "wipe_r")
    put_text(im, "ونختارو؟", 540, 950, AMIRI, 112, IVORY, t, 48.6, .7, "wipe_r")
    chip(im, "تابعيني باش نكملو الخطوات", 540, 1200, BORD, IVORY, t, 49.4, 50)
    put_text(im, "Académie IN&OUT · Btissam Goumara", 540, 1330, PLAY, 44, SAND, t, 50.1, .6, "rise", "SemiBold")
    return im

SCENES = [  # (début, scène, transition entrante, durée)
    (0.0, s_promo, None, 0), (2.4, s_dressing, "iris", .7), (5.5, s_sig, "wipe_up", .6),
    (9.9, s_wardrobe, "push_l", .6), (15.8, s_ask, "zoom", .7), (22.4, s_ex1, "wipe_l", .6),
    (27.6, s_ex2, "push_u", .6), (37.1, s_list, "iris", .7), (43.5, s_three, "push_r", .6),
    (47.7, s_end, "wipe_up", .6),
]

def transition(a, b, p, kind):
    p = easeio(p)
    if kind == "iris":
        m = Image.new("L", (W, H), 0); r = int(p * 1500)
        ImageDraw.Draw(m).ellipse((W / 2 - r, H * .45 - r, W / 2 + r, H * .45 + r), fill=255)
        return Image.composite(b, a, m)
    if kind == "wipe_up":
        out = a.copy(); y = int(H * (1 - p)); out.paste(b.crop((0, y, W, H)), (0, y))
        ImageDraw.Draw(out).rectangle((0, max(0, y - 10), W, y), fill=SAND); return out
    if kind == "wipe_l":
        out = a.copy(); x = int(W * p); out.paste(b.crop((0, 0, x, H)), (0, 0))
        ImageDraw.Draw(out).rectangle((x, 0, x + 10, H), fill=SAND); return out
    if kind.startswith("push"):
        out = Image.new("RGB", (W, H))
        if kind == "push_l": out.paste(a, (int(-W * p), 0)); out.paste(b, (int(W - W * p), 0))
        elif kind == "push_r": out.paste(a, (int(W * p), 0)); out.paste(b, (int(-W + W * p), 0))
        else: out.paste(a, (0, int(-H * p))); out.paste(b, (0, int(H - H * p)))
        return out
    if kind == "zoom":
        s = 1 + .12 * p; ox, oy = int(W * (s - 1) / 2), int(H * (s - 1) / 2)
        a2 = a.resize((int(W * s), int(H * s)), Image.BICUBIC).crop((ox, oy, ox + W, oy + H))
        return Image.blend(a2, b, p)
    return b

def compose(t):
    i = 0
    for k, s in enumerate(SCENES):
        if s[0] <= t: i = k
    t0, fn, kind, d = SCENES[i]
    if kind and t - t0 < d:
        return transition(SCENES[i - 1][1](t).convert("RGB"), fn(t).convert("RGB"), (t - t0) / d, kind)
    return fn(t)

def overlays(im, idx):
    im = im.convert("RGB")
    g = cached(("grain", idx % 3), lambda: noise_tile(idx % 3))
    im = Image.blend(im, ImageChops.overlay(im, g), .10)
    return Image.composite(Image.new("RGB", (W, H), (40, 24, 20)), im, cached("vig", vignette))

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

def wrap2(s, f, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = c
    lines.append(cur)
    if len(lines) > 2:
        h = len(words) // 2; lines = [" ".join(words[:h]), " ".join(words[h:])]
    return lines

def subs(im, t):
    for a, b, s, isar in SUBS:
        if a <= t < b:
            f = font(CAIRO, 46, "Bold") if isar else font(CAIRO, 42, "SemiBold")
            lines = wrap2(s, f, 840)
            y0, hh = 1490, len(lines) * 66 + 44
            k = clamp((t - a) / .15) * clamp((b - t) / .15)
            box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(box).rounded_rectangle((90, y0, W - 90, y0 + hh), 30, fill=(40, 39, 34, int(228 * k)))
            im = Image.alpha_composite(im.convert("RGBA"), box); d = ImageDraw.Draw(im)
            for j, l in enumerate(lines):
                d.text((W // 2, y0 + 55 + j * 66), l, font=f, fill=(247, 241, 230, int(255 * k)), anchor="mm")
            return im.convert("RGB")
    return im

def render(i):
    t = i / FPS
    im = subs(overlays(compose(t), i), t)
    im.save(os.path.join(R, "out", "frames", f"f{i:05d}.jpg"), quality=92)
    return i

def main():
    os.makedirs(os.path.join(R, "out", "frames"), exist_ok=True)
    n = int(DUR * FPS)
    idx = [int(a) for a in sys.argv[1:] if a.isdigit()]
    todo = idx if idx else list(range(n))
    if "--encode" in sys.argv: todo = idx
    with Pool(4) as p:
        for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=8)):
            if k % 300 == 0: print(k, "/", len(todo), flush=True)
    if idx and "--encode" not in sys.argv: return
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(R, "out", "frames", "f%05d.jpg"),
           "-i", os.path.join(R, "voiceover.m4a"), "-i", os.path.join(R, "jingle", "signature_jingle.wav"),
           "-f", "lavfi", "-t", str(DUR), "-i", "sine=f=196:sample_rate=44100",
           "-filter_complex",
           "[1:a]volume=1.0[v];[2:a]adelay=5450|5450,volume=.9[j];"
           "[3:a]volume=.02,lowpass=f=420,tremolo=f=.22:d=.7[m];"
           "[v][j][m]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5[a]",
           "-map", "0:v", "-map", "[a]", "-t", str(DUR), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
           "-preset", "medium", "-c:a", "aac", "-b:a", "192k", os.path.join(R, "out", "reel_01_v3.mp4")]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
