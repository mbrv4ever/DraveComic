# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""achtergrond.py - achtergronden, laag op laag (stuk 5).

Een achtergrond is een stapel lagen (onderste eerst), per vakje (vakje["achtergrond"]) of voor de
hele bladzijde (pagina["achtergrond"]). Elke laag is een dict:
  soort: een van SOORTEN, k1/k2: kleuren, zaad: getal voor 'anders' (sterren, bomen, huizen...),
  dekking (0-1), zicht (aan/uit), spiegel (links-rechts omdraaien)
  en bij soort 'plaat': id, zoom, dx, dy (zoals een gewoon plaatje in een vakje).
Alles wordt met de hand getekend (geen plaatjes van anderen), dus vrij te gebruiken.
Sommige lagen zijn 'vol' (lucht, kamer...), andere zijn doorzichtig erboven (bergen, stad, bos...),
zodat je ze kunt stapelen: lucht -> bergen -> bos -> regen.
"""
import json
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                         QPolygonF, QRadialGradient)

SOORTEN = ("kleur", "verloop", "lucht", "avond", "nacht", "bergen", "heuvels", "stad", "bos", "zee", "kamer",
           "snelheid", "vaart", "knal", "stippen", "regen", "sneeuw", "plaat")

NAMEN = {
    "kleur": ("Effen kleur", "Plain colour"), "verloop": ("Kleurverloop", "Gradient"), "lucht": ("Lucht", "Sky"),
    "avond": ("Zonsondergang", "Sunset"), "nacht": ("Nacht", "Night"), "bergen": ("Bergen", "Mountains"),
    "heuvels": ("Heuvels", "Hills"), "stad": ("Stad", "City"), "bos": ("Bos", "Forest"), "zee": ("Zee", "Sea"),
    "kamer": ("Kamer", "Room"), "snelheid": ("Actielijnen", "Action lines"), "vaart": ("Vaartstrepen", "Speed streaks"),
    "knal": ("Knal", "Burst"), "stippen": ("Stippen", "Dots"), "regen": ("Regen", "Rain"), "sneeuw": ("Sneeuw", "Snow"),
    "plaat": ("Eigen plaatje", "Own picture"), "tekening": ("Zelf tekenen", "Draw it yourself"),
}

# welke kleuren een laag heeft (naam NL, naam EN); leeg = geen kleurknop
KLEUREN = {
    "kleur": (("Kleur", "Colour"),),
    "verloop": (("Boven", "Top"), ("Onder", "Bottom")),
    "lucht": (("Boven", "Top"), ("Onder", "Bottom")),
    "avond": (("Boven", "Top"), ("Onder", "Bottom")),
    "nacht": (("Boven", "Top"), ("Onder", "Bottom")),
    "bergen": (("Bergen", "Mountains"), ("Sneeuw", "Snow")),
    "heuvels": (("Voor", "Front"), ("Achter", "Back")),
    "stad": (("Huizen", "Buildings"), ("Ramen", "Windows")),
    "bos": (("Bomen", "Trees"), ("Stammen", "Trunks")),
    "zee": (("Water", "Water"), ("Diep", "Deep")),
    "kamer": (("Muur", "Wall"), ("Vloer", "Floor")),
    "snelheid": (("Lijnen", "Lines"),), "vaart": (("Strepen", "Streaks"),),
    "knal": (("Binnen", "Inside"), ("Buiten", "Outside")),
    "stippen": (("Stippen", "Dots"),), "regen": (("Regen", "Rain"),), "sneeuw": (("Sneeuw", "Snow"),),
    "plaat": (),
}

STANDAARD = {
    "kleur": ("#ffffff", None), "verloop": ("#7F77DD", "#ffd166"), "lucht": ("#3d8bfd", "#d4ecff"),
    "avond": ("#3b2a6b", "#ffb347"), "nacht": ("#070b24", "#2a3a78"), "bergen": ("#5b6f99", "#ffffff"),
    "heuvels": ("#4caf50", "#9ad86e"), "stad": ("#353a56", "#ffd166"), "bos": ("#2f6b3a", "#6b4a2b"),
    "zee": ("#2d7ff9", "#0c3c8c"), "kamer": ("#f2e3c6", "#a0522d"), "snelheid": ("#111111", None),
    "vaart": ("#111111", None), "knal": ("#ffd166", "#e23b3b"), "stippen": ("#ff6fb5", None),
    "regen": ("#9fc4ff", None), "sneeuw": ("#ffffff", None), "plaat": (None, None),
}

# lagen die een heel vakje vullen (de rest is doorzichtig en kan erbovenop)
VOL = ("kleur", "verloop", "lucht", "avond", "nacht", "kamer")


def nieuw(soort, zaad=None):
    k1, k2 = STANDAARD.get(soort, ("#ffffff", None))
    d = dict(soort=soort, k1=k1, k2=k2, zaad=zaad if zaad is not None else random.randint(1, 99999),
             dekking=1.0, zicht=True, spiegel=False)
    if soort == "plaat":
        d.update(id=None, zoom=1.0, dx=0.0, dy=0.0)
    return d


def naam(soort, nl=True):
    n = NAMEN.get(soort, (soort, soort))
    return n[0] if nl else n[1]


def gebruikte_beelden(lagen):
    return {l["id"] for l in (lagen or []) if l.get("soort") == "plaat" and l.get("id")}


# ------------------------------------------------------------------ hulpjes
def _k(s, d="#000000"):
    return QColor(s) if s else QColor(d)


def _lichter(c, f):
    c = QColor(c)
    return c.lighter(int(f)) if f >= 100 else c.darker(int(10000 / f))


def _meng(a, b, t):
    a, b = QColor(a), QColor(b)
    return QColor(int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


def _lijn(w, h):
    return max(1.2, min(w, h) / 260.0)


def _verloop(p, w, h, stops):
    g = QLinearGradient(0, 0, 0, h)
    for t, c in stops:
        g.setColorAt(t, QColor(c))
    p.fillRect(QRectF(0, 0, w, h), QBrush(g))


def _wolk(p, cx, cy, s, rand):
    pad = QPainterPath()
    pad.addEllipse(QRectF(cx - s * 1.6, cy - s * 0.45, s * 3.2, s * 0.95))
    for dx, dy, r in ((-0.9, -0.15, 0.55), (-0.25, -0.45, 0.75), (0.55, -0.3, 0.62), (1.1, 0.0, 0.42)):
        b = QPainterPath()
        b.addEllipse(QPointF(cx + dx * s, cy + dy * s), r * s, r * s * 0.92)
        pad = pad.united(b)
    p.setPen(QPen(rand, max(1.0, s * 0.06)))
    p.setBrush(QColor("#ffffff"))
    p.drawPath(pad.simplified())


# ------------------------------------------------------------------ de soorten
def _m_kleur(p, w, h, sp, rnd):
    p.fillRect(QRectF(0, 0, w, h), _k(sp.get("k1"), "#ffffff"))


def _m_verloop(p, w, h, sp, rnd):
    _verloop(p, w, h, ((0, _k(sp.get("k1"))), (1, _k(sp.get("k2"), "#ffffff"))))


def _m_lucht(p, w, h, sp, rnd):
    _verloop(p, w, h, ((0, _k(sp.get("k1"))), (1, _k(sp.get("k2"), "#ffffff"))))
    n = max(3, int(w / 230) + 2)
    for _ in range(n):
        s = min(w, h) * rnd.uniform(0.05, 0.11) + 8
        _wolk(p, rnd.uniform(0.03, 0.97) * w, rnd.uniform(0.08, 0.55) * h, s, QColor("#a9c3e6"))


def _m_avond(p, w, h, sp, rnd):
    boven, onder = _k(sp.get("k1")), _k(sp.get("k2"), "#ffb347")
    _verloop(p, w, h, ((0, boven), (0.55, _meng(boven, QColor("#e2557a"), 0.85)), (1, onder)))
    cx, cy, r = rnd.uniform(0.3, 0.7) * w, h * 0.8, min(w, h) * 0.16
    g = QRadialGradient(QPointF(cx, cy), r * 2.6)
    g.setColorAt(0, QColor(255, 230, 150, 170))
    g.setColorAt(1, QColor(255, 230, 150, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, cy), r * 2.6, r * 2.6)
    p.setBrush(QColor("#ffe08a"))
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setBrush(QColor(120, 40, 90, 120))
    for _ in range(max(2, int(w / 300) + 2)):
        y = rnd.uniform(0.25, 0.7) * h
        x = rnd.uniform(-0.1, 0.8) * w
        p.drawRoundedRect(QRectF(x, y, rnd.uniform(0.2, 0.45) * w, h * 0.018 + 3), 4, 4)


def _m_nacht(p, w, h, sp, rnd):
    _verloop(p, w, h, ((0, _k(sp.get("k1"))), (1, _k(sp.get("k2"), "#2a3a78"))))
    p.setPen(Qt.PenStyle.NoPen)
    n = min(500, int(w * h / 5000) + 20)
    for _ in range(n):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h * 0.85), rnd.choice((0.6, 0.8, 1.0, 1.3, 1.9)) * max(0.7, min(w, h) / 480.0)
        p.setBrush(QColor(255, 255, rnd.randint(210, 255), rnd.randint(150, 255)))
        p.drawEllipse(QPointF(x, y), r, r)
    mx, my, mr = rnd.uniform(0.6, 0.85) * w, rnd.uniform(0.12, 0.28) * h, min(w, h) * 0.09
    g = QRadialGradient(QPointF(mx, my), mr * 3)
    g.setColorAt(0, QColor(255, 244, 194, 90))
    g.setColorAt(1, QColor(255, 244, 194, 0))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(mx, my), mr * 3, mr * 3)
    maan = QPainterPath()
    maan.addEllipse(QPointF(mx, my), mr, mr)
    hap = QPainterPath()
    hap.addEllipse(QPointF(mx + mr * 0.45, my - mr * 0.2), mr * 0.85, mr * 0.85)
    p.setBrush(QColor("#fff4c2"))
    p.drawPath(maan.subtracted(hap))


def _bergrij(p, w, h, rnd, kleur, sneeuw, basis, hoogte, n, lijn):
    stap = w * 1.2 / n
    toppen = []
    for i in range(n + 1):
        toppen.append((-w * 0.1 + stap * (i + rnd.uniform(0.2, 0.8)), basis - rnd.uniform(0.45, 1.0) * hoogte))
    pts = [QPointF(-w * 0.15, basis)]
    for i, (x, y) in enumerate(toppen):
        pts.append(QPointF(x, y))
        if i < len(toppen) - 1:
            nx, ny = toppen[i + 1]
            dal = max(y, ny) + rnd.uniform(0.15, 0.35) * hoogte
            pts.append(QPointF(x + (nx - x) * rnd.uniform(0.4, 0.6), min(dal, basis)))
    pts += [QPointF(w * 1.15, basis), QPointF(w * 1.15, h + 2), QPointF(-w * 0.15, h + 2)]
    p.setPen(QPen(QColor("#1a1a2a"), lijn))
    p.setBrush(kleur)
    p.drawPolygon(QPolygonF(pts))
    if sneeuw is None:
        return
    p.setBrush(sneeuw)
    p.setPen(QPen(QColor("#1a1a2a"), lijn * 0.6))
    # sneeuwkapjes op de hoge toppen: vast stukje omlaag langs beide hellingen, met een kartelrand
    kap = hoogte * 0.16
    for i in range(1, len(pts) - 3):
        top, links, rechts = pts[i], pts[i - 1], pts[i + 1]
        if top.y() > basis - hoogte * 0.55 or links.y() <= top.y() or rechts.y() <= top.y():
            continue

        def op(ander, d):
            t = min(1.0, d / max(1e-6, ander.y() - top.y()))
            return QPointF(top.x() + (ander.x() - top.x()) * t, top.y() + (ander.y() - top.y()) * t)

        a, b = op(links, kap), op(rechts, kap * 0.8)
        m1 = QPointF(a.x() + (b.x() - a.x()) * 0.3, top.y() + kap * 0.55)
        m2 = QPointF(a.x() + (b.x() - a.x()) * 0.5, top.y() + kap * 0.95)
        m3 = QPointF(a.x() + (b.x() - a.x()) * 0.72, top.y() + kap * 0.5)
        p.drawPolygon(QPolygonF([top, b, m3, m2, m1, a]))


def _m_bergen(p, w, h, sp, rnd):
    k = _k(sp.get("k1"), "#5b6f99")
    sneeuw = _k(sp.get("k2"), "#ffffff")
    lijn = _lijn(w, h)
    _bergrij(p, w, h, rnd, _meng(k, QColor("#dfe6f5"), 0.45), _meng(sneeuw, QColor("#dfe6f5"), 0.3),
             h * 0.62, h * 0.32, max(4, int(w / 160)), lijn * 0.8)
    _bergrij(p, w, h, rnd, k, sneeuw, h * 0.8, h * 0.4, max(3, int(w / 230)), lijn)


def _heuvel(p, w, h, rnd, kleur, basis, golf, lijn):
    pad = QPainterPath(QPointF(-10, h + 2))
    pad.lineTo(-10, basis)
    n = 3
    stap = (w + 20) / n
    x = -10
    y = basis
    for _ in range(n):
        ny = basis + rnd.uniform(-golf, golf)
        pad.cubicTo(QPointF(x + stap * 0.35, y - golf * rnd.uniform(0.6, 1.4)),
                    QPointF(x + stap * 0.65, ny - golf * rnd.uniform(0.6, 1.4)), QPointF(x + stap, ny))
        x += stap
        y = ny
    pad.lineTo(w + 10, h + 2)
    pad.closeSubpath()
    p.setPen(QPen(QColor("#1a2a1a"), lijn))
    p.setBrush(kleur)
    p.drawPath(pad)


def _m_heuvels(p, w, h, sp, rnd):
    lijn = _lijn(w, h)
    _heuvel(p, w, h, rnd, _k(sp.get("k2"), "#9ad86e"), h * 0.62, h * 0.08, lijn * 0.8)
    _heuvel(p, w, h, rnd, _k(sp.get("k1"), "#4caf50"), h * 0.76, h * 0.07, lijn)


def _m_stad(p, w, h, sp, rnd):
    huis, raam = _k(sp.get("k1"), "#353a56"), _k(sp.get("k2"), "#ffd166")
    lijn = _lijn(w, h)
    for rij, (licht, hmin, hmax) in enumerate(((150, 0.35, 0.7), (100, 0.22, 0.55))):
        kleur = _meng(huis, QColor("#c9cfe6"), 0.45) if rij == 0 else huis
        x = -rnd.uniform(0, 0.05) * w
        while x < w:
            bw = rnd.uniform(0.07, 0.15) * w
            bh = rnd.uniform(hmin, hmax) * h
            r = QRectF(x, h - bh, bw, bh + 2)
            p.setPen(QPen(QColor("#141522"), lijn * (0.7 if rij == 0 else 1.0)))
            p.setBrush(kleur)
            p.drawRect(r)
            if rnd.random() < 0.3:              # antenne of torentje
                p.drawLine(QPointF(x + bw * 0.5, h - bh), QPointF(x + bw * 0.5, h - bh - bh * 0.12))
            if rij == 1:
                rw, rh = bw / 7.0, bw / 6.0
                yy = h - bh + rh
                while yy < h - rh * 2:
                    xx = x + rw
                    while xx < x + bw - rw * 1.5:
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(raam if rnd.random() < 0.55 else _lichter(huis, 130))
                        p.drawRect(QRectF(xx, yy, rw, rh))
                        xx += rw * 2
                    yy += rh * 2
            x += bw + rnd.uniform(-0.01, 0.02) * w


def _den(p, x, voet, hoogte, kleur, stam, lijn):
    b = hoogte * 0.42
    p.setPen(QPen(QColor("#13261a"), lijn))
    p.setBrush(stam)
    p.drawRect(QRectF(x - b * 0.09, voet - hoogte * 0.16, b * 0.18, hoogte * 0.16 + 2))
    p.setBrush(kleur)
    for i, (f, bf) in enumerate(((0.0, 1.0), (0.28, 0.8), (0.52, 0.58))):
        y0 = voet - hoogte * 0.12 - hoogte * f
        top = y0 - hoogte * 0.45
        p.drawPolygon(QPolygonF([QPointF(x - b * bf / 2, y0), QPointF(x, top), QPointF(x + b * bf / 2, y0)]))


def _m_bos(p, w, h, sp, rnd):
    boom, stam = _k(sp.get("k1"), "#2f6b3a"), _k(sp.get("k2"), "#6b4a2b")
    lijn = _lijn(w, h)
    for rij in range(2):
        kleur = _meng(boom, QColor("#cfe3d2"), 0.45) if rij == 0 else boom
        n = max(5, int(w / (55 if rij == 0 else 75)))
        xs = sorted(rnd.uniform(-0.03, 1.03) * w for _ in range(n))
        for x in xs:
            hoogte = rnd.uniform(0.25, 0.4) * h if rij == 0 else rnd.uniform(0.32, 0.52) * h
            voet = h * (0.86 if rij == 0 else 1.0) + rnd.uniform(-0.02, 0.02) * h
            _den(p, x, voet, hoogte, kleur, stam, lijn * (0.7 if rij == 0 else 1.0))


def _m_zee(p, w, h, sp, rnd):
    water, diep = _k(sp.get("k1"), "#2d7ff9"), _k(sp.get("k2"), "#0c3c8c")
    y0 = h * 0.62
    g = QLinearGradient(0, y0, 0, h)
    g.setColorAt(0, _lichter(water, 125))
    g.setColorAt(1, diep)
    p.fillRect(QRectF(0, y0, w, h - y0), QBrush(g))
    p.setPen(QPen(QColor("#0b1d40"), _lijn(w, h)))
    p.drawLine(QPointF(0, y0), QPointF(w, y0))
    p.setPen(QPen(QColor(255, 255, 255, 200), _lijn(w, h) * 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for _ in range(int(w * (h - y0) / 2500) + 6):
        y = rnd.uniform(y0 + 4, h - 2)
        t = (y - y0) / max(1.0, h - y0)
        lw = (0.02 + t * 0.05) * w
        x = rnd.uniform(0, w)
        pad = QPainterPath(QPointF(x, y))
        pad.quadTo(QPointF(x + lw / 4, y - lw * 0.18), QPointF(x + lw / 2, y))
        pad.quadTo(QPointF(x + lw * 0.75, y - lw * 0.18), QPointF(x + lw, y))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(pad)


def _m_kamer(p, w, h, sp, rnd):
    muur, vloer = _k(sp.get("k1"), "#f2e3c6"), _k(sp.get("k2"), "#a0522d")
    lijn = _lijn(w, h)
    p.fillRect(QRectF(0, 0, w, h), muur)
    yv = h * 0.72
    p.fillRect(QRectF(0, yv, w, h - yv), vloer)
    p.setPen(QPen(_lichter(vloer, 70), lijn))
    for i in range(1, 6):
        y = yv + (h - yv) * (i / 6.0) ** 1.3
        p.drawLine(QPointF(0, y), QPointF(w, y))
    p.setPen(QPen(QColor("#2a2218"), lijn))
    p.setBrush(_lichter(muur, 80))
    p.drawRect(QRectF(-2, yv - h * 0.03, w + 4, h * 0.03))
    # raam met lucht
    links = rnd.random() < 0.5
    rw, rh = w * 0.3, h * 0.34
    rx = w * 0.1 if links else w * 0.6
    ry = h * 0.14
    g = QLinearGradient(0, ry, 0, ry + rh)
    g.setColorAt(0, QColor("#5aa6ff"))
    g.setColorAt(1, QColor("#d4ecff"))
    p.setBrush(QBrush(g))
    p.setPen(QPen(QColor("#2a2218"), lijn * 2))
    p.drawRect(QRectF(rx, ry, rw, rh))
    p.setPen(QPen(QColor("#ffffff"), lijn * 3))
    p.drawLine(QPointF(rx + rw / 2, ry), QPointF(rx + rw / 2, ry + rh))
    p.drawLine(QPointF(rx, ry + rh / 2), QPointF(rx + rw, ry + rh / 2))
    # schilderijtje
    fx = w * 0.66 if links else w * 0.12
    fw, fh = w * 0.18, h * 0.16
    p.setPen(QPen(QColor("#2a2218"), lijn * 1.5))
    p.setBrush(QColor("#c8a046"))
    p.drawRect(QRectF(fx, h * 0.2, fw, fh))
    p.setBrush(QColor("#7fb3d5"))
    p.drawRect(QRectF(fx + fw * 0.12, h * 0.2 + fh * 0.14, fw * 0.76, fh * 0.72))
    p.setBrush(QColor("#4caf50"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(fx + fw * 0.12, h * 0.2 + fh * 0.55, fw * 0.76, fh * 0.6))


def _m_snelheid(p, w, h, sp, rnd):
    kleur = _k(sp.get("k1"), "#111111")
    cx, cy = w / 2, h / 2
    groot = math.hypot(w, h)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(kleur)
    n = 110
    for i in range(n):
        hoek = 2 * math.pi * (i + rnd.uniform(-0.35, 0.35)) / n
        binnen = rnd.uniform(0.28, 0.42)
        bx, by = cx + math.cos(hoek) * w * binnen, cy + math.sin(hoek) * h * binnen
        breed = rnd.uniform(0.006, 0.02)
        a1, a2 = hoek - breed, hoek + breed
        p.drawPolygon(QPolygonF([QPointF(bx, by), QPointF(cx + math.cos(a1) * groot, cy + math.sin(a1) * groot),
                                 QPointF(cx + math.cos(a2) * groot, cy + math.sin(a2) * groot)]))


def _m_vaart(p, w, h, sp, rnd):
    kleur = _k(sp.get("k1"), "#111111")
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(kleur)
    for _ in range(int(h / 14) + 8):
        y = rnd.uniform(0, h)
        lengte = rnd.uniform(0.25, 0.85) * w
        dik = rnd.uniform(0.6, 2.6) * _lijn(w, h)
        x1 = w + 2
        p.drawPolygon(QPolygonF([QPointF(x1, y - dik), QPointF(x1 - lengte, y), QPointF(x1, y + dik)]))


def _m_knal(p, w, h, sp, rnd):
    binnen, buiten = _k(sp.get("k1"), "#ffd166"), _k(sp.get("k2"), "#e23b3b")
    cx, cy = w / 2, h / 2

    def ster(fa, fb, n):
        pts = []
        for i in range(n * 2):
            hoek = math.pi * i / n + rnd.uniform(-0.05, 0.05)
            f = (fa if i % 2 == 0 else fb) * rnd.uniform(0.85, 1.1)
            pts.append(QPointF(cx + math.cos(hoek) * w * f, cy + math.sin(hoek) * h * f))
        return QPolygonF(pts)

    p.setPen(QPen(QColor("#111111"), _lijn(w, h) * 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                  Qt.PenJoinStyle.MiterJoin))
    p.setBrush(buiten)
    p.drawPolygon(ster(0.62, 0.34, 16))
    p.setBrush(binnen)
    p.drawPolygon(ster(0.4, 0.22, 12))
    p.setBrush(QColor("#fffbe6"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), w * 0.1, h * 0.1)


def _m_stippen(p, w, h, sp, rnd):
    kleur = _k(sp.get("k1"), "#ff6fb5")
    d = max(w, h) / 34.0
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(kleur)
    hoek = rnd.choice(((0, 0), (1, 0), (0, 1), (1, 1)))
    rij = 0
    y = 0.0
    while y < h + d:
        x = (d / 2) if rij % 2 else 0.0
        while x < w + d:
            tx = x / w if hoek[0] == 0 else 1 - x / w
            ty = y / h if hoek[1] == 0 else 1 - y / h
            t = max(0.0, min(1.0, (tx + ty) / 2))
            r = d * 0.48 * (1.0 - t * 0.85)
            if r > 0.4:
                p.drawEllipse(QPointF(x, y), r, r)
            x += d
        y += d * 0.87
        rij += 1


def _m_regen(p, w, h, sp, rnd):
    kleur = _k(sp.get("k1"), "#9fc4ff")
    p.setPen(QPen(kleur, _lijn(w, h) * 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for _ in range(min(600, int(w * h / 2500) + 30)):
        x, y = rnd.uniform(-0.1, 1.0) * w, rnd.uniform(-0.05, 1.0) * h
        l = rnd.uniform(0.03, 0.07) * h
        p.drawLine(QPointF(x, y), QPointF(x + l * 0.3, y + l))


def _m_sneeuw(p, w, h, sp, rnd):
    kleur = _k(sp.get("k1"), "#ffffff")
    p.setPen(QPen(QColor(120, 140, 170, 140), _lijn(w, h) * 0.6))
    p.setBrush(kleur)
    for _ in range(min(600, int(w * h / 2200) + 30)):
        r = rnd.choice((1.2, 1.6, 2.2, 3.0)) * _lijn(w, h)
        p.drawEllipse(QPointF(rnd.uniform(0, w), rnd.uniform(0, h)), r, r)


MOTIEF = {
    "kleur": _m_kleur, "verloop": _m_verloop, "lucht": _m_lucht, "avond": _m_avond, "nacht": _m_nacht,
    "bergen": _m_bergen, "heuvels": _m_heuvels, "stad": _m_stad, "bos": _m_bos, "zee": _m_zee, "kamer": _m_kamer,
    "snelheid": _m_snelheid, "vaart": _m_vaart, "knal": _m_knal, "stippen": _m_stippen, "regen": _m_regen,
    "sneeuw": _m_sneeuw,
}

# ------------------------------------------------------------------ tekenen (met een kleine voorraad kant-en-klare beelden)
_VOORRAAD = {}
_VOLGORDE = []


def _sleutel(sp, pw, ph, w, h):
    s = {k: sp.get(k) for k in ("soort", "k1", "k2", "zaad", "spiegel")}
    return json.dumps(s, sort_keys=True) + "|%d|%d|%.1f|%.1f" % (pw, ph, w, h)


def _maak(sp, pw, ph, w, h):
    im = QImage(max(1, pw), max(1, ph), QImage.Format.Format_ARGB32_Premultiplied)
    im.fill(Qt.GlobalColor.transparent)
    p = QPainter(im)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(pw / w, ph / h)
    if sp.get("spiegel"):
        p.translate(w, 0)
        p.scale(-1, 1)
    p.setClipRect(QRectF(0, 0, w, h))
    rnd = random.Random(int(sp.get("zaad") or 1))
    try:
        MOTIEF[sp["soort"]](p, w, h, sp, rnd)
    finally:
        p.end()
    return im


def beeld_van(sp, w, h, schaal):
    """De laag als plaatje van w x h eenheden op 'schaal' pixels per eenheid (uit de voorraad als hij er al is)."""
    pw = int(min(3200, max(8, w * schaal)))
    ph = int(min(4600, max(8, h * schaal)))
    k = _sleutel(sp, pw, ph, w, h)
    im = _VOORRAAD.get(k)
    if im is None:
        im = _maak(sp, pw, ph, w, h)
        _VOORRAAD[k] = im
        _VOLGORDE.append(k)
        while len(_VOLGORDE) > 80:
            _VOORRAAD.pop(_VOLGORDE.pop(0), None)
    return im


def teken(p, lagen, r, beelden):
    """Tekent een stapel achtergrondlagen (onderste eerst) in rechthoek r (painter in bladzijde-eenheden)."""
    if not lagen:
        return
    t = p.worldTransform()
    schaal = max(0.2, math.hypot(t.m11(), t.m12()))
    p.save()
    p.setClipRect(r, Qt.ClipOperation.IntersectClip)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for sp in lagen:
        if not sp.get("zicht", True):
            continue
        p.setOpacity(max(0.0, min(1.0, sp.get("dekking", 1.0))))
        soort = sp.get("soort")
        if soort == "plaat":
            im = beelden.beeld(sp.get("id")) if sp.get("id") else None
            if im is None or im.isNull():
                continue
            basis = max(r.width() / im.width(), r.height() / im.height())
            s = basis * sp.get("zoom", 1.0)
            bw, bh = im.width() * s, im.height() * s
            doel = QRectF(r.center().x() - bw / 2 + sp.get("dx", 0), r.center().y() - bh / 2 + sp.get("dy", 0), bw, bh)
            if sp.get("spiegel"):
                p.save()
                p.translate(doel.center().x(), 0)
                p.scale(-1, 1)
                p.translate(-doel.center().x(), 0)
                p.drawImage(doel, im)
                p.restore()
            else:
                p.drawImage(doel, im)
        elif soort in MOTIEF:
            p.drawImage(r, beeld_van(sp, r.width(), r.height(), schaal))
    p.setOpacity(1.0)
    p.restore()


def voorbeeld(soort, bw=104, bh=70):
    """Klein plaatje voor de knoppen."""
    pm = QPixmap(bw, bh)
    pm.fill(QColor("#cfc8e6") if soort not in VOL else QColor("#ffffff"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if soort in MOTIEF:
        sp = nieuw(soort, zaad=7)
        if soort in ("bergen", "heuvels", "stad", "bos", "zee", "regen", "sneeuw"):
            # laat zien hoe hij erbovenop werkt: met een luchtje eronder
            onder = nieuw("nacht" if soort == "sneeuw" else "lucht", zaad=3)
            p.drawImage(QRectF(0, 0, bw, bh), _maak(onder, bw * 2, bh * 2, 300, 200))
        p.drawImage(QRectF(0, 0, bw, bh), _maak(sp, bw * 2, bh * 2, 300, 200))
    p.setPen(QPen(QColor("#4a3d66"), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(1, 1, bw - 2, bh - 2))
    p.end()
    return pm
