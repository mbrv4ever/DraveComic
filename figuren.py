# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""figuren.py - de personage-kast (0.6.0).

Een figuur teken je één keer, bewaar je in de kast, en zet je daarna met één klik in elk vakje.
In de kast staat elke figuur als PNG (met doorzichtige achtergrond) in DraveComic-data/Personages.
Op de bladzijde is een figuur een ding in pagina["teksten"] met soort "figuur" (verschuifbaar, groter/kleiner).
"""
import os
import re

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QRect
from PyQt6.QtGui import QImage


def map_(data):
    m = os.path.join(data, "Personages")
    os.makedirs(m, exist_ok=True)
    return m


def lijst(data):
    m = map_(data)
    return [(os.path.splitext(n)[0], os.path.join(m, n)) for n in sorted(os.listdir(m), key=str.lower)
            if n.lower().endswith(".png")]


def veilige_naam(naam):
    naam = re.sub(r'[\\/:*?"<>|]', "", (naam or "").strip())[:60]
    return naam or "Figuur"


def vrije_naam(data, naam):
    naam = veilige_naam(naam)
    m, n, kandidaat = map_(data), 2, naam
    while os.path.exists(os.path.join(m, kandidaat + ".png")):
        kandidaat = "%s %d" % (naam, n)
        n += 1
    return kandidaat


def bijgesneden(im):
    """Snijdt de doorzichtige rand weg. Geeft (beeld, rechthoek binnen het origineel) of (None, None) als alles leeg is."""
    im = im.convertToFormat(QImage.Format.Format_ARGB32)
    w, h = im.width(), im.height()
    if w == 0 or h == 0:
        return None, None
    try:
        import numpy as np
        ptr = im.constBits()
        ptr.setsize(im.sizeInBytes())
        rij = im.bytesPerLine() // 4
        a = (np.frombuffer(ptr, dtype=np.uint32).reshape(h, rij)[:, :w] >> 24) > 8
        ys = np.where(a.any(axis=1))[0]
        xs = np.where(a.any(axis=0))[0]
        if len(xs) == 0:
            return None, None
        x0, x1, y0, y1 = int(xs[0]), int(xs[-1]), int(ys[0]), int(ys[-1])
    except Exception:
        # zonder numpy: grof per 2 pixels zoeken
        x0, y0, x1, y1 = w, h, -1, -1
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                if (im.pixel(x, y) >> 24) > 8:
                    x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
        if x1 < 0:
            return None, None
    marge = 6
    r = QRect(max(0, x0 - marge), max(0, y0 - marge), 0, 0)
    r.setRight(min(w - 1, x1 + marge))
    r.setBottom(min(h - 1, y1 + marge))
    return im.copy(r), r


def png_bytes(im):
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    im.save(buf, "PNG")
    buf.close()
    return bytes(ba)


def bewaar(data, naam, im):
    naam = vrije_naam(data, naam)
    pad = os.path.join(map_(data), naam + ".png")
    im.save(pad, "PNG")
    return naam, pad


def hernoem(data, oud_pad, nieuw):
    nieuw = vrije_naam(data, nieuw)
    pad = os.path.join(map_(data), nieuw + ".png")
    os.replace(oud_pad, pad)
    return nieuw, pad


def nieuw_ding(bid, naam, im_w, im_h, doos):
    """Een figuur op de bladzijde, passend in 'doos' (x, y, w, h): onderaan in het midden, 70% van de hoogte."""
    x, y, w, h = doos
    hh = h * 0.7
    ww = hh * im_w / max(1, im_h)
    if ww > w * 0.9:
        ww = w * 0.9
        hh = ww * im_h / max(1, im_w)
    return dict(soort="figuur", bid=bid, naam=naam, x=round(x + (w - ww) / 2), y=round(y + h - hh - h * 0.04),
                w=round(ww), h=round(hh), spiegel=False, staart=None, tekst="")
