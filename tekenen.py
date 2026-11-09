# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""tekenen.py - het tekengereedschap van DraveComic (stuk 2).

Elke bladzijde heeft lagen: doorzichtige plaatjes van LB x LH pixels boven de vakjes.
Gereedschap: pen, potlood, inkt-penseel (snel = dun), gum, emmertje (vullen), en vormen:
lijn, rechthoek, cirkel, pijl en snelheidsstrepen.
Alles werkt in bladzijde-eenheden (1000 x 1414); een laag is LS keer zo scherp.
"""
import math
import random

import numpy as np
from PyQt6.QtCore import QPointF, QRect, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF

PB, PH = 1000.0, 1414.0
LS = 1.5
LB, LH = int(PB * LS), int(PH * LS)

UIT_DE_HAND = ("pen", "potlood", "penseel", "gum")
VORMEN = ("lijn", "rechthoek", "cirkel", "pijl", "snelheid")


def lege_laag():
    im = QImage(LB, LH, QImage.Format.Format_ARGB32_Premultiplied)
    im.fill(Qt.GlobalColor.transparent)
    return im


class Gereedschap:
    def __init__(self):
        self.soort = "pen"
        self.kleur = QColor("#111111")
        self.dikte = 6.0              # in bladzijde-eenheden
        self.gevuld = False
        self.binnen = True            # binnen het vakje blijven


def _pen(kleur, w):
    p = QPen(kleur, max(0.5, w))
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


class Streek:
    """Eén keer tekenen met pen, potlood, penseel of gum, direct in de laag."""

    def __init__(self, laag, g, pt, clip=None, druk=None):
        self.laag, self.g, self.clip = laag, g, clip
        self.vorige = pt
        self.breedte = g.dikte
        self.druk = druk              # 0.6.0: drukgevoeligheid van een tekentablet (0..1), None = muis
        self.kader = QRectF(pt.x(), pt.y(), 0, 0)
        self.voor = laag.copy()       # voor ongedaan maken (wordt bij klaar() bijgesneden)
        self._stip(pt)

    def _painter(self):
        p = QPainter(self.laag)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(LS, LS)
        if self.clip is not None:
            p.setClipRect(self.clip)
        if self.g.soort == "gum":
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        return p

    def _kleur(self):
        k = QColor(self.g.kleur)
        if self.g.soort == "potlood":
            k.setAlpha(150 if self.druk is None else int(50 + 170 * self.druk))
        return k

    def _f(self):
        """Hoe hard je drukt met de tablet-pen: zacht = dun, hard = dik (de muis blijft gewoon 1)."""
        return 1.0 if self.druk is None else 0.12 + 0.88 * max(0.0, min(1.0, self.druk))

    def _w(self):
        if self.g.soort == "potlood":
            return max(0.6, self.g.dikte * 0.5 * self._f())
        if self.g.soort == "gum":
            return self.g.dikte * 2.0 * (1.0 if self.druk is None else 0.4 + 0.6 * self.druk)
        return max(0.5, self.breedte * self._f())

    def _stip(self, pt):
        p = self._painter()
        w = self._w()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._kleur() if self.g.soort != "gum" else QColor("black"))
        p.drawEllipse(pt, w / 2, w / 2)
        p.end()
        self._groei(pt, w)

    def _groei(self, pt, w):
        self.kader = self.kader.united(QRectF(pt.x() - w, pt.y() - w, 2 * w, 2 * w))

    def beweeg(self, pt):
        d = math.hypot(pt.x() - self.vorige.x(), pt.y() - self.vorige.y())
        if d < 0.6:
            return
        if self.g.soort == "penseel":
            # inkt-penseel: hoe sneller je beweegt, hoe dunner de lijn (zoals een echte kwast)
            doel = self.g.dikte * max(0.25, min(1.3, 1.3 - d / 25.0))
            self.breedte += (doel - self.breedte) * 0.35
        p = self._painter()
        k = self._kleur() if self.g.soort != "gum" else QColor("black")
        p.setPen(_pen(k, self._w()))
        p.drawLine(self.vorige, pt)
        p.end()
        self._groei(pt, self._w())
        self._groei(self.vorige, self._w())
        self.vorige = pt

    def klaar(self):
        """Geeft (rechthoek in laag-pixels, beeld ervoor, beeld erna) voor ongedaan maken."""
        r = QRect(int(self.kader.x() * LS) - 4, int(self.kader.y() * LS) - 4,
                  int(self.kader.width() * LS) + 8, int(self.kader.height() * LS) + 8).intersected(QRect(0, 0, LB, LH))
        voor = self.voor.copy(r)
        self.voor = None
        return r, voor, self.laag.copy(r)


def teken_vorm(p, soort, a, b, kleur, dikte, gevuld=False):
    """Tekent een vorm van punt a naar punt b (painter staat al in bladzijde-eenheden)."""
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(a, b).normalized()
    pen = _pen(kleur, dikte)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin if soort == "rechthoek" else Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(kleur) if gevuld else Qt.BrushStyle.NoBrush)
    if soort == "lijn":
        p.drawLine(a, b)
    elif soort == "rechthoek":
        p.drawRect(r)
    elif soort == "cirkel":
        p.drawEllipse(r)
    elif soort == "pijl":
        dx, dy = b.x() - a.x(), b.y() - a.y()
        lengte = math.hypot(dx, dy)
        if lengte < 1:
            return
        ux, uy = dx / lengte, dy / lengte
        kop = max(22.0, dikte * 4)
        voet = QPointF(b.x() - ux * kop, b.y() - uy * kop)
        p.drawLine(a, voet)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(kleur)
        p.drawPolygon(QPolygonF([b, QPointF(voet.x() - uy * kop * 0.6, voet.y() + ux * kop * 0.6),
                                 QPointF(voet.x() + uy * kop * 0.6, voet.y() - ux * kop * 0.6)]))
    elif soort == "snelheid":
        # snelheidsstrepen: dunne, puntige strepen in de sleeprichting, verspreid over de breedte
        dx, dy = b.x() - a.x(), b.y() - a.y()
        lengte = math.hypot(dx, dy)
        if lengte < 10:
            return
        ux, uy = dx / lengte, dy / lengte
        nx, ny = -uy, ux
        breed = max(40.0, lengte * 0.6)
        rnd = random.Random(int(a.x() * 7 + a.y() * 13))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(kleur)
        n = max(5, int(breed / 14))
        for i in range(n):
            off = (i / (n - 1) - 0.5) * breed + rnd.uniform(-5, 5)
            begin = rnd.uniform(0, 0.35) * lengte
            eind = rnd.uniform(0.65, 1.0) * lengte
            w = max(1.5, dikte * rnd.uniform(0.4, 1.0))
            sx, sy = a.x() + nx * off + ux * begin, a.y() + ny * off + uy * begin
            ex, ey = a.x() + nx * off + ux * eind, a.y() + ny * off + uy * eind
            p.drawPolygon(QPolygonF([QPointF(sx, sy), QPointF(ex + nx * w / 2, ey + ny * w / 2),
                                     QPointF(ex - nx * w / 2, ey - ny * w / 2)]))


def zet_vorm(laag, soort, a, b, kleur, dikte, gevuld, clip=None):
    """Zet een vorm echt in de laag. Geeft (rechthoek, ervoor, erna) voor ongedaan maken."""
    marge = dikte * 4 + 40
    kader = QRectF(a, b).normalized().adjusted(-marge, -marge, marge, marge)
    if soort == "snelheid":
        lengte = math.hypot(b.x() - a.x(), b.y() - a.y())
        kader = kader.adjusted(-lengte, -lengte, lengte, lengte)
    r = QRect(int(kader.x() * LS), int(kader.y() * LS), int(kader.width() * LS), int(kader.height() * LS)) \
        .intersected(QRect(0, 0, LB, LH))
    voor = laag.copy(r)
    p = QPainter(laag)
    p.scale(LS, LS)
    if clip is not None:
        p.setClipRect(clip)
    teken_vorm(p, soort, a, b, kleur, dikte, gevuld)
    p.end()
    return r, voor, laag.copy(r)


def _als_array(im):
    im = im.convertToFormat(QImage.Format.Format_ARGB32)
    w, h = im.width(), im.height()
    ptr = im.constBits()
    ptr.setsize(im.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(h, im.bytesPerLine())[:, :w * 4].reshape(h, w, 4)
    return a.copy()


def vul(samen, laag, pt, kleur, clip=None, marge=40):
    """Emmertje: vult het gebied rond pt (bladzijde-eenheden) dat op 'samen' (de hele bladzijde zoals je hem ziet,
    op laag-resolutie) dezelfde kleur heeft. De verf komt in 'laag'. Geeft (rechthoek, ervoor, erna) of None."""
    x, y = int(pt.x() * LS), int(pt.y() * LS)
    if not (0 <= x < LB and 0 <= y < LH):
        return None
    a = _als_array(samen).astype(np.int16)
    zaad = a[y, x]
    mask = np.abs(a - zaad).sum(axis=2) <= marge
    if clip is not None:
        c = np.zeros_like(mask)
        x0, y0 = max(0, int(clip.left() * LS)), max(0, int(clip.top() * LS))
        x1, y1 = min(LB, int(clip.right() * LS) + 1), min(LH, int(clip.bottom() * LS) + 1)
        c[y0:y1, x0:x1] = True
        mask &= c
    if not mask[y, x]:
        return None
    h, w = mask.shape
    gevuld = np.zeros_like(mask)
    stapel = [(x, y)]
    while stapel:
        sx, sy = stapel.pop()
        if gevuld[sy, sx] or not mask[sy, sx]:
            continue
        rij = mask[sy]
        links = np.flatnonzero(~rij[:sx + 1])
        l = links[-1] + 1 if links.size else 0
        rechts = np.flatnonzero(~rij[sx:])
        r = sx + rechts[0] - 1 if rechts.size else w - 1
        gevuld[sy, l:r + 1] = True
        for ny in (sy - 1, sy + 1):
            if 0 <= ny < h:
                seg = mask[ny, l:r + 1] & ~gevuld[ny, l:r + 1]
                if seg.any():
                    d = np.diff(np.concatenate(([0], seg.astype(np.int8))))
                    for s in np.flatnonzero(d == 1):
                        stapel.append((l + int(s), ny))
    # 2 pixels uitzetten, zodat er geen wit randje langs de (zachte) lijnen blijft
    for _ in range(2):
        g = gevuld.copy()
        g[1:, :] |= gevuld[:-1, :]
        g[:-1, :] |= gevuld[1:, :]
        g[:, 1:] |= gevuld[:, :-1]
        g[:, :-1] |= gevuld[:, 1:]
        if clip is not None:
            g &= c
        gevuld = g
    ys, xs = np.nonzero(gevuld)
    if not ys.size:
        return None
    rect = QRect(int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
    laagje = np.zeros((h, w, 4), np.uint8)
    laagje[gevuld] = (kleur.blue(), kleur.green(), kleur.red(), 255)
    qi = QImage(laagje.data, w, h, w * 4, QImage.Format.Format_ARGB32_Premultiplied).copy()
    voor = laag.copy(rect)
    p = QPainter(laag)
    p.drawImage(0, 0, qi)
    p.end()
    return rect, voor, laag.copy(rect)
