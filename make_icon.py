# Maakt assets/icon.png + assets/icon.ico voor DraveComic.
# Eigen ontwerp: een paarse stripbladzijde met vakjes, een gouden BAM!-ster en een tekstballon.
# Copyright (C) 2026 Dravenlock (Roger & Claudio). GNU GPL v3.0. Pillow nodig.
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
N = 512
img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((16, 16, N - 16, N - 16), radius=100, fill=(22, 19, 31, 255), outline=(127, 119, 221, 255), width=12)
gl = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ImageDraw.Draw(gl).ellipse((90, 110, 430, 450), fill=(127, 119, 221, 110))
img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(45)))
d = ImageDraw.Draw(img)
# de bladzijde met vakjes (iets schuin)
blad = Image.new("RGBA", (N, N), (0, 0, 0, 0))
b = ImageDraw.Draw(blad)
b.rounded_rectangle((120, 110, 392, 430), radius=14, fill=(239, 234, 255, 255))
for r in ((140, 130, 372, 250), (140, 266, 250, 410), (266, 266, 372, 410)):
    b.rectangle(r, fill=(181, 156, 255, 255), outline=(22, 19, 31, 255), width=8)
blad = blad.rotate(-8, center=(256, 270), resample=Image.BICUBIC)
img = Image.alpha_composite(img, blad)
d = ImageDraw.Draw(img)


def ster(cx, cy, r1, r2, n=12, draai=0):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / n + draai
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def letter(grootte):
    for f in ("ariblk.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, grootte)
        except Exception:
            pass
    return ImageFont.load_default()


# gouden BAM!-ster rechtsboven
d.polygon(ster(370, 150, 120, 74, 12, 0.2), fill=(22, 19, 31, 255))
d.polygon(ster(370, 150, 106, 64, 12, 0.2), fill=(255, 200, 87, 255))
lag = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ImageDraw.Draw(lag).text((370, 150), "BAM!", font=letter(64), fill=(200, 40, 60, 255), anchor="mm",
                         stroke_width=5, stroke_fill=(22, 19, 31, 255))
img = Image.alpha_composite(img, lag.rotate(12, center=(370, 150), resample=Image.BICUBIC))
d = ImageDraw.Draw(img)
# tekstballon linksonder
d.ellipse((46, 318, 250, 452), fill=(255, 255, 255, 255), outline=(22, 19, 31, 255), width=9)
d.polygon([(170, 440), (230, 488), (200, 432)], fill=(255, 255, 255, 255), outline=(22, 19, 31, 255))
d.line([(170, 444), (230, 488), (206, 438)], fill=(22, 19, 31, 255), width=9)
d.ellipse((46, 318, 250, 452), outline=(22, 19, 31, 255), width=9)
for x in (104, 148, 192):
    d.ellipse((x - 13, 372, x + 13, 398), fill=(127, 119, 221, 255))

os.makedirs(os.path.join(HIER, "assets"), exist_ok=True)
img.save(os.path.join(HIER, "assets", "icon.png"))
img.save(os.path.join(HIER, "assets", "icon.ico"), format="ICO",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icoon klaar")
