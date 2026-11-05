# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""ballonnen.py - tekstballonnen, vertelblokjes en geluidswoorden (stuk 3).

Een tekst-ding is een dict in pagina["teksten"]:
  soort: praat / denk / schreeuw / verteller / geluid
  x, y, w, h: het tekstvak (bladzijde-eenheden), staart: [x, y] (punt waar de ballon naar wijst)
  tekst, grootte (letterhoogte), kleur (letters), vulling, draai (graden, geluid), ster (geluid: ster erachter)
Letters: Comic Neue (ballonnen) en Bangers (geluidswoorden), allebei vrij (SIL Open Font License).
"""
import math
import os

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontDatabase, QFontMetricsF, QPainter, QPainterPath, QPen, QPolygonF

SOORTEN = ("praat", "denk", "schreeuw", "verteller", "geluid")
LETTER = {"tekst": "Comic Sans MS", "geluid": "Impact"}


def laad_letters(map_):
    """Laadt de meegeleverde letters (na het maken van de QApplication)."""
    for naam, soort in (("ComicNeue-Bold.ttf", "tekst"), ("ComicNeue-Regular.ttf", None), ("Bangers-Regular.ttf", "geluid")):
        p = os.path.join(map_, naam)
        if os.path.exists(p):
            i = QFontDatabase.addApplicationFont(p)
            fam = QFontDatabase.applicationFontFamilies(i) if i >= 0 else []
            if fam and soort:
                LETTER[soort] = fam[0]


def nieuw(soort, x, y):
    """Een nieuw tekst-ding met gewone beginwaarden, met het midden op (x, y)."""
    if soort == "geluid":
        w, h = 360, 170
        d = dict(tekst="BAM!", grootte=0, kleur="#ffd166", vulling="#e23b3b", draai=-8, ster=True)
    elif soort == "verteller":
        w, h = 380, 110
        d = dict(tekst="Ondertussen..." if _nl() else "Meanwhile...", grootte=26, kleur="#111111", vulling="#fff2a8")
    else:
        w, h = 300, 130
        tekst = {"praat": ("Hallo!", "Hello!"), "denk": ("Hmm...", "Hmm..."), "schreeuw": ("HELP!", "HELP!")}[soort]
        d = dict(tekst=tekst[0] if _nl() else tekst[1], grootte=30 if soort != "schreeuw" else 38,
                 kleur="#111111", vulling="#ffffff")
    d.update(soort=soort, x=round(x - w / 2), y=round(y - h / 2), w=w, h=h, staart=[x + 40, y + h / 2 + 120])
    if soort in ("verteller", "geluid"):
        d["staart"] = None
    return d


def _nl():
    import locale
    try:
        t = (locale.getlocale()[0] or "") + (locale.getdefaultlocale()[0] or "")
    except Exception:
        t = ""
    return "nl" in t.lower() or "dutch" in t.lower() or not t


def vak(t):
    return QRectF(t["x"], t["y"], t["w"], t["h"])


def buitenkant(t):
    """De rechthoek van de hele vorm (ballon is iets groter dan het tekstvak)."""
    r = vak(t)
    if t["soort"] in ("praat", "denk", "schreeuw"):
        dx, dy = r.width() * 0.16, r.height() * 0.22
        if t["soort"] == "schreeuw":
            dx, dy = dx * 1.5, dy * 1.5
        r = r.adjusted(-dx, -dy, dx, dy)
    elif t["soort"] == "verteller":
        r = r.adjusted(-14, -10, 14, 10)
    return r


def _staart_veelhoek(r, punt, breed):
    c = r.center()
    dx, dy = punt.x() - c.x(), punt.y() - c.y()
    l = math.hypot(dx, dy) or 1
    nx, ny = -dy / l, dx / l
    return QPolygonF([QPointF(c.x() + nx * breed, c.y() + ny * breed), punt,
                      QPointF(c.x() - nx * breed * 0.4, c.y() - ny * breed * 0.4)])


def vorm(t):
    """De omtrek van de ballon (QPainterPath), of None voor een geluidswoord."""
    s = t["soort"]
    r = buitenkant(t)
    pad = QPainterPath()
    st = t.get("staart")
    punt = QPointF(st[0], st[1]) if st else None
    if s == "praat":
        pad.addEllipse(r)
        if punt is not None and not r.contains(punt):
            staart = QPainterPath()
            staart.addPolygon(_staart_veelhoek(r, punt, min(r.width(), r.height()) * 0.24))
            staart.closeSubpath()
            pad = pad.united(staart)
    elif s == "denk":
        # wolkje: een ring van rondjes langs de ellips, plus 3 kleiner wordende belletjes naar de staart
        cx, cy, a, b = r.center().x(), r.center().y(), r.width() / 2, r.height() / 2
        n = max(8, int((a + b) / 28))
        pad.addEllipse(r.adjusted(a * 0.12, b * 0.12, -a * 0.12, -b * 0.12))
        for i in range(n):
            hoek = 2 * math.pi * i / n
            px, py = cx + a * 0.86 * math.cos(hoek), cy + b * 0.86 * math.sin(hoek)
            rr = (a + b) / n * 1.15
            bol = QPainterPath()
            bol.addEllipse(QPointF(px, py), rr, rr * 0.9)
            pad = pad.united(bol)
        if punt is not None and not r.contains(punt):
            for k, f in enumerate((0.35, 0.62, 0.86)):
                bx = cx + (punt.x() - cx) * (0.55 + f * 0.45)
                by = cy + (punt.y() - cy) * (0.55 + f * 0.45)
                rr = (a + b) * 0.09 * (1.0 - k * 0.28)
                pad.addEllipse(QPointF(bx, by), rr, rr)
    elif s == "schreeuw":
        cx, cy, a, b = r.center().x(), r.center().y(), r.width() / 2, r.height() / 2
        n = 22
        pts = []
        for i in range(n * 2):
            hoek = math.pi * i / n
            f = 1.0 if i % 2 == 0 else 0.78
            pts.append(QPointF(cx + a * f * math.cos(hoek), cy + b * f * math.sin(hoek)))
        pad.addPolygon(QPolygonF(pts))
        pad.closeSubpath()
        if punt is not None and not r.contains(punt):
            staart = QPainterPath()
            staart.addPolygon(_staart_veelhoek(r, punt, min(a, b) * 0.3))
            staart.closeSubpath()
            pad = pad.united(staart)
    elif s == "verteller":
        pad.addRect(r)
    else:
        return None
    return pad.simplified()


def letter_van(t):
    """(familie, vet, schuin) van een tekst-ding; standaard: stripletters."""
    geluid = t.get("soort") == "geluid"
    fam = t.get("letter") or LETTER["geluid" if geluid else "tekst"]
    return fam, bool(t.get("vet", not geluid)), bool(t.get("schuin", False))


def _passende_letter(familie, tekst, r, max_px, vet=True, schuin=False):
    """Grootste lettergrootte waarmee de tekst (met afbreken) in rechthoek r past."""
    f = QFont(familie)
    f.setBold(vet)
    f.setItalic(schuin)
    lo, hi = 8.0, max(10.0, max_px)
    for _ in range(14):
        mid = (lo + hi) / 2
        f.setPixelSize(int(mid))
        fm = QFontMetricsF(f)
        br = fm.boundingRect(r, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), tekst)
        if br.width() <= r.width() + 0.5 and br.height() <= r.height() + 0.5:
            lo = mid
        else:
            hi = mid
    f.setPixelSize(int(lo))
    return f


def _ster(r, n=14):
    cx, cy, a, b = r.center().x(), r.center().y(), r.width() / 2, r.height() / 2
    pts = []
    for i in range(n * 2):
        hoek = math.pi * i / n + 0.1
        f = 1.0 if i % 2 == 0 else 0.62
        pts.append(QPointF(cx + a * f * math.cos(hoek), cy + b * f * math.sin(hoek)))
    return QPolygonF(pts)


def teken(p, t):
    """Tekent één tekst-ding (painter in bladzijde-eenheden)."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    s = t["soort"]
    r = vak(t)
    tekst = t.get("tekst", "")
    if s == "geluid":
        p.translate(r.center())
        p.rotate(t.get("draai", 0))
        r0 = QRectF(-r.width() / 2, -r.height() / 2, r.width(), r.height())
        if t.get("ster", True):
            p.setPen(QPen(QColor("#111111"), 6))
            p.setBrush(QColor(t.get("vulling", "#e23b3b")))
            p.drawPolygon(_ster(r0.adjusted(-r0.width() * 0.18, -r0.height() * 0.35, r0.width() * 0.18, r0.height() * 0.35)))
        binnen = r0.adjusted(r0.width() * 0.06, r0.height() * 0.08, -r0.width() * 0.06, -r0.height() * 0.08)
        fam, vet, schuin = letter_van(t)
        f = _passende_letter(fam, tekst, binnen, binnen.height() * 1.1, vet=vet, schuin=schuin)
        # letters als omtrek: dikke zwarte rand + gekleurde vulling (zoals in een echte strip)
        pad = QPainterPath()
        fm = QFontMetricsF(f)
        regels = tekst.split("\n") or [""]
        hoogte = fm.height() * len(regels)
        y = binnen.center().y() - hoogte / 2 + fm.ascent()
        for regel in regels:
            pad.addText(QPointF(binnen.center().x() - fm.horizontalAdvance(regel) / 2, y), f, regel)
            y += fm.height()
        dik = max(4.0, f.pixelSize() * 0.09)
        p.setPen(QPen(QColor("#111111"), dik * 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(pad)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(t.get("kleur", "#ffd166")))
        p.drawPath(pad)
        p.restore()
        return
    pad = vorm(t)
    p.setPen(QPen(QColor("#111111"), 4 if s != "schreeuw" else 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                  Qt.PenJoinStyle.RoundJoin))
    p.setBrush(QColor(t.get("vulling", "#ffffff")))
    p.drawPath(pad)
    fam, vet, schuin = letter_van(t)
    f = QFont(fam)
    f.setBold(vet)
    f.setItalic(schuin)
    f.setPixelSize(max(8, int(t.get("grootte", 30))))
    fm = QFontMetricsF(f)
    br = fm.boundingRect(r, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), tekst)
    if br.height() > r.height() or br.width() > r.width() + 1:
        f = _passende_letter(fam, tekst, r, t.get("grootte", 30), vet=vet, schuin=schuin)
    p.setFont(f)
    p.setPen(QColor(t.get("kleur", "#111111")))
    p.drawText(r, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), tekst)
    p.restore()


def raak(t, pt):
    """Ligt punt pt op dit tekst-ding?"""
    if t["soort"] == "geluid":
        r = vak(t)
        # het punt terugdraaien naar het rechte vak
        hoek = -math.radians(t.get("draai", 0))
        c = r.center()
        dx, dy = pt.x() - c.x(), pt.y() - c.y()
        q = QPointF(c.x() + dx * math.cos(hoek) - dy * math.sin(hoek), c.y() + dx * math.sin(hoek) + dy * math.cos(hoek))
        return r.adjusted(-30, -30, 30, 30).contains(q)
    pad = vorm(t)
    return (pad is not None and pad.contains(pt)) or buitenkant(t).contains(pt)
