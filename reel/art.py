"""Illustrations éditoriales vectorielles (supersamplées) pour le Reel IN&OUT.
Toutes les pièces sont dessinées dans un repère « mannequin » 700x1500, puis
réutilisées en pose à plat (flat-lay) et portées par le mannequin."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

SS = 2  # supersampling
SKIN = (221, 177, 146); SKIN_D = (196, 150, 120); HAIR = (52, 34, 28)
CHOC = (92, 58, 44); BORD = (122, 26, 46); CREAM = (236, 224, 202); IVORY_K = (244, 238, 226)
TAN = (176, 124, 82); WHITE = (246, 244, 238); NUDE = (214, 170, 140); DENIM = (96, 120, 150)
FW, FH = 700, 1500

def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)

class Layer:
    def __init__(self, w=FW, h=FH):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * SS, y * SS) for x, y in pts]
    def poly(self, pts, fill): self.d.polygon(self.P(pts), fill=fill + (255,) if len(fill) == 3 else fill)
    def rrect(self, box, r, fill):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), r * SS, fill=fill + (255,) if len(fill) == 3 else fill)
    def ell(self, box, fill):
        x0, y0, x1, y1 = box
        self.d.ellipse((x0 * SS, y0 * SS, x1 * SS, y1 * SS), fill=fill + (255,) if len(fill) == 3 else fill)
    def line(self, pts, fill, w):
        self.d.line(self.P(pts), fill=fill + (255,) if len(fill) == 3 else fill, width=int(w * SS), joint="curve")
    def finish(self, texture=0.05, seed=1):
        """Texture de tissu + ombrage doux; renvoie l'image à taille finale."""
        a = np.asarray(self.im).astype(np.float32)
        rng = np.random.default_rng(seed)
        n = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) - 128
        a[..., :3] *= (1 + (n[..., None] / 128) * texture * 3)
        out = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
        return out.resize((self.w, self.h), Image.LANCZOS)

def chaikin(pts, n=3, closed=True):
    for _ in range(n):
        out = []
        m = len(pts)
        for i in range(m if closed else m - 1):
            p, q = pts[i], pts[(i + 1) % m]
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        pts = out
    return pts

def shadow_poly(L, pts, alpha=46):
    alpha = int(alpha * 0.35)
    s = Image.new("RGBA", L.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).polygon(L.P(pts), fill=(30, 15, 10, alpha))
    s = s.filter(ImageFilter.GaussianBlur(22 * SS))
    mask = L.im.split()[3]
    s.putalpha(ImageChops.multiply(s.split()[3], mask))
    L.im = Image.alpha_composite(L.im, s)
    L.d = ImageDraw.Draw(L.im)

# ---------------- pièces (repère mannequin) ----------------
def trousers(L, c=CHOC):
    pts = [(268, 560), (432, 560), (472, 735), (512, 1388), (374, 1388), (350, 835), (326, 1388), (188, 1388), (228, 735)]
    L.poly(pts, c)
    L.poly([(268, 560), (432, 560), (436, 592), (264, 592)], _shade(c, .82))  # ceinture
    for x0, x1 in [(300, 262), (400, 438)]:
        L.line([(x0, 780), (x1, 1380)], _shade(c, .72), 3)  # pli central
    shadow_poly(L, [(350, 760), (420, 760), (440, 1380), (380, 1380)], 40)
    for bx in (350,):
        L.ell((bx - 7, 568, bx + 7, 582), _shade(c, 1.35))

def knit_top(L, c=IVORY_K):
    L.poly([(262, 232), (438, 232), (448, 420), (442, 610), (258, 610), (252, 420)], c)
    L.poly([(212, 255), (264, 232), (258, 430), (246, 656), (190, 650), (198, 430)], _shade(c, .96))
    L.poly([(488, 255), (436, 232), (442, 430), (454, 656), (510, 650), (502, 430)], _shade(c, .96))
    L.poly([(306, 222), (394, 222), (380, 252), (320, 252)], _shade(c, .8))  # col rond
    L.line([(200, 640), (246, 646)], _shade(c, .8), 6); L.line([(454, 646), (500, 640)], _shade(c, .8), 6)
    shadow_poly(L, [(262, 430), (330, 430), (330, 610), (262, 610)], 30)

def loafers(L, c=TAN):
    for sgn in (-1, 1):
        cx = 350 + sgn * 80
        o = 8 * sgn
        L.poly(chaikin([(cx - 86 + o, 1404), (cx + 86 + o, 1404), (cx + 96 + o, 1438), (cx - 96 + o, 1440)], 3), c)
        L.rrect((cx - 92 + o, 1438, cx + 92 + o, 1450), 5, _shade(c, .45))
        L.poly(chaikin([(cx - 34 + o, 1412), (cx + 34 + o, 1412), (cx + 28 + o, 1426), (cx - 28 + o, 1426)], 2), _shade(c, 1.22))

def heels(L, c=NUDE):
    for sgn in (-1, 1):
        cx = 350 + sgn * 62
        pts = chaikin([(cx - 40, 1404), (cx + 40, 1404), (cx + 46, 1432), (cx + 10 * sgn, 1452), (cx - 46, 1440)], 3)
        L.poly(pts, c)
        L.line(chaikin([(cx - 30, 1410), (cx + 30, 1410)], 1, False), _shade(c, .8), 3)

def dress(L, c=BORD):
    L.poly([(286, 226), (414, 226), (446, 254), (440, 420), (430, 572), (548, 1190), (152, 1190), (270, 572), (260, 420), (254, 254)], c)
    L.poly([(212, 255), (262, 236), (256, 430), (244, 690), (196, 684), (200, 430)], _shade(c, .95))
    L.poly([(488, 255), (438, 236), (444, 430), (456, 690), (504, 684), (500, 430)], _shade(c, .95))
    L.poly([(270, 560), (430, 560), (432, 592), (268, 592)], _shade(c, .75))
    L.poly([(298, 224), (402, 224), (350, 300)], _shade(c, .7))  # décolleté en V
    for x0, x1 in [(300, 258), (350, 350), (400, 442)]:
        L.line([(x0, 640), (x1, 1180)], _shade(c, .8), 3)
    shadow_poly(L, [(350, 600), (520, 600), (548, 1190), (350, 1190)], 42)

def blazer(L, c=CREAM):
    # dos / épaules
    L.poly([(204, 252), (262, 228), (438, 228), (496, 252), (506, 690), (194, 690)], _shade(c, .9))
    # devants ouverts
    L.poly([(262, 228), (346, 232), (326, 340), (326, 790), (232, 790), (250, 430)], c)
    L.poly([(438, 228), (354, 232), (374, 340), (374, 790), (468, 790), (450, 430)], c)
    L.poly([(262, 228), (346, 232), (322, 340), (300, 420)], _shade(c, .8))  # revers
    L.poly([(438, 228), (354, 232), (378, 340), (400, 420)], _shade(c, .8))
    L.poly([(200, 255), (264, 230), (254, 440), (238, 720), (178, 712), (186, 440)], c)
    L.poly([(500, 255), (436, 230), (446, 440), (462, 720), (522, 712), (514, 440)], c)
    shadow_poly(L, [(326, 340), (372, 340), (372, 790), (326, 790)], 38)
    for yy in (520, 600): L.ell((330, yy, 342, yy + 12), _shade(c, .55))

def figure_base(L, hair_style=0):
    hair_back = chaikin([(300, 78), (350, 52), (402, 78), (426, 150), (436, 250), (424, 340), (384, 346), (392, 220), (310, 220), (318, 346), (276, 340), (264, 250), (274, 150)], 3)
    L.poly(hair_back, HAIR)
    L.poly([(332, 160), (368, 160), (372, 236), (328, 236)], SKIN_D)
    L.ell((306, 70, 394, 184), SKIN)
    L.poly(chaikin([(300, 112), (312, 78), (350, 62), (392, 80), (402, 114), (386, 96), (350, 84), (316, 98)], 3), HAIR)
    L.poly([(194, 640), (244, 646), (240, 690), (210, 704), (190, 676)], SKIN)
    L.poly([(506, 640), (456, 646), (460, 690), (490, 704), (510, 676)], SKIN)
    L.poly([(304, 760), (350, 760), (342, 1412), (310, 1412)], SKIN)
    L.poly([(350, 760), (396, 760), (390, 1412), (358, 1412)], SKIN)

def outfit_layers(kind):
    """Retourne la liste ordonnée de couches (nom, image) pour que chaque pièce arrive séparément."""
    layers = []
    L = Layer(); figure_base(L); layers.append(("body", L.finish(0.0)))
    if kind == "work":
        L = Layer(); knit_top(L); layers.append(("top", L.finish(.05, 2)))
        L = Layer(); trousers(L); layers.append(("trousers", L.finish(.06, 3)))
        L = Layer(); loafers(L); layers.append(("shoes", L.finish(.03, 4)))
    else:
        L = Layer(); heels(L); layers.append(("shoes", L.finish(.03, 5)))
        L = Layer(); dress(L); layers.append(("dress", L.finish(.06, 6)))
        L = Layer(); blazer(L); layers.append(("blazer", L.finish(.05, 7)))
    return layers

# ---------------- flat-lay ----------------
def flat(fn, bbox, margin=20, **kw):
    L = Layer(); fn(L, **kw)
    im = L.finish(.06, 11)
    x0, y0, x1, y1 = bbox
    return im.crop((x0 - margin, y0 - margin, x1 + margin, y1 + margin))

def make_flats():
    F = {}
    F["trousers"] = flat(trousers, (186, 558, 514, 1390))
    F["dress"] = flat(dress, (150, 222, 550, 1192))
    F["blazer"] = flat(blazer, (176, 226, 524, 792))
    F["top"] = flat(knit_top, (188, 220, 512, 658))
    # chaussures à plat (un pied) — dessinées localement
    def shoe_loafer(L, c=TAN):
        up = chaikin([(30, 124), (34, 64), (96, 40), (150, 66), (250, 80), (316, 112), (318, 126)], 3)
        L.poly(up, c); L.rrect((26, 118, 322, 140), 8, _shade(c, .45))
        L.poly(chaikin([(120, 70), (214, 82), (200, 100), (120, 92)], 2), _shade(c, 1.25))
        L.line(chaikin([(60, 112), (180, 108), (300, 118)], 2, False), _shade(c, .7), 2)
    L = Layer(340, 180); shoe_loafer(L); F["loafer"] = L.finish(.04, 21)
    def sneaker(L):
        up = chaikin([(30, 128), (34, 56), (110, 40), (160, 78), (250, 86), (318, 112), (320, 128)], 3)
        L.poly(up, WHITE); L.rrect((26, 120, 324, 146), 10, (222, 217, 206))
        L.poly(chaikin([(200, 84), (252, 88), (318, 112), (316, 124), (206, 124)], 2), (232, 226, 214))
        for k in range(3): L.line([(130 + k * 20, 62 + k * 8), (168 + k * 20, 88 + k * 8)], (170, 165, 155), 3)
        L.poly(chaikin([(30, 90), (70, 82), (72, 124), (30, 126)], 2), (192, 150, 120))
    L = Layer(340, 180); sneaker(L); F["sneaker"] = L.finish(.03, 22)
    def boot(L, c=CHOC):
        up = chaikin([(46, 126), (50, 14), (170, 14), (176, 84), (260, 92), (322, 116), (322, 128)], 2)
        L.poly(up, c); L.rrect((40, 120, 326, 148), 8, _shade(c, .5))
        L.rrect((52, 22, 168, 42), 6, _shade(c, 1.25))
    L = Layer(340, 180); boot(L); F["boot"] = L.finish(.05, 23)
    def pump(L, c=NUDE):
        L.poly(chaikin([(30, 130), (36, 70), (110, 50), (170, 90), (300, 118), (310, 132)], 3), c)
        L.rrect((26, 126, 300, 140), 6, _shade(c, .7))
    L = Layer(340, 180); pump(L); F["pump"] = L.finish(.03, 24)
    def shirt_blue(L):
        pass
    return F

# ---------------- décor ----------------
def arch(w, h, color):
    """Arche en fer à cheval (touche marocaine discrète)."""
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = w * SS // 2
    d.rectangle((0, r, w * SS, h * SS), fill=color + (255,)); d.ellipse((0, 0, w * SS, 2 * r), fill=color + (255,))
    return im.resize((w, h), Image.LANCZOS)

def zellige(w, h, c1, c2, cell=90):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    import math
    for gy in range(0, h + cell, cell):
        for gx in range(0, w + cell, cell):
            cx, cy = gx + cell / 2, gy + cell / 2
            pts = []
            for k in range(16):
                a = k * math.pi / 8 - math.pi / 2; r = cell * (0.46 if k % 2 == 0 else 0.26)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            d.polygon(pts, fill=c1 + (255,))
            d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=c2 + (255,))
    return im

def wood_door(w, h):
    base = np.zeros((h, w, 3), np.float32); base[...] = (178, 132, 92)
    rng = np.random.default_rng(7)
    g = rng.normal(0, 1, (1, w)).astype(np.float32); g = np.repeat(g, h, axis=0)
    g = np.asarray(Image.fromarray(((g * 30) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) - 128
    base += g[..., None] * 0.35
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((36, 40, w - 36, h - 40), 14, outline=(140, 98, 66, 255), width=6)
    return im

def hanger_item(img, hook=True):
    """Pièce à plat sur cintre."""
    w, h = img.size
    out = Image.new("RGBA", (w, h + 90), (0, 0, 0, 0))
    out.paste(img, (0, 90), img)
    d = ImageDraw.Draw(out)
    d.line([(w // 2, 60), (w // 2, 40)], fill=(90, 70, 60, 255), width=6)
    d.arc((w // 2 - 14, 14, w // 2 + 14, 46), 180, 360, fill=(90, 70, 60, 255), width=6)
    d.line([(w // 2 - 120, 130), (w // 2, 62), (w // 2 + 120, 130)], fill=(90, 70, 60, 255), width=6)
    return out

if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    F = make_flats()
    sheet = Image.new("RGB", (2400, 1300), (247, 241, 230)); x = 20
    for k in ("trousers", "dress", "blazer", "top"):
        im = F[k]; s = 1000 / im.height; im = im.resize((int(im.width * s * .9), int(1000 * .9)))
        sheet.paste(im, (x, 20), im); x += im.width + 20
    y = 1050; x = 20
    for k in ("loafer", "sneaker", "boot", "pump"):
        sheet.paste(F[k], (x, y), F[k]); x += 360
    sheet.save("out/sprites_flats.png")
    for kind in ("work", "dress"):
        base = Image.new("RGB", (FW, FH), (247, 241, 230))
        for n, l in outfit_layers(kind): base.paste(l, (0, 0), l)
        base.save(f"out/sprite_fig_{kind}.png")
