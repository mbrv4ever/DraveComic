# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""DraveComic - maak je eigen stripboek. Groot en duidelijk.

Stuk 1: bladzijden, vakjes (kant-en-klare indelingen of zelf trekken), plaatjes invoegen
(schuiven, zoomen), een rand per vakje, ongedaan maken, opslaan als project (.dcomic) en
een bladzijde bewaren als plaatje (PNG).
Stuk 2: tekenen (pen, potlood, inkt-penseel, gum, emmertje, kleur pakken, vormen) in lagen.
Stuk 3: tekstballonnen (praten, denken, schreeuwen), vertelblokjes en geluidswoorden (BAM!).
Stuk 4: kaft (voor en achter), bladzijden verslepen, het hele boek als PDF of als plaatjes, en bladeren.
Stuk 5: achtergronden, laag op laag: per vakje of voor de hele bladzijde; kant-en-klaar (lucht, bergen, stad,
bos, actielijnen, knal...), een eigen plaatje of zelf tekenen (een tekenlaag achter de plaatjes).
Alle gegevens staan naast de app in de map DraveComic-data (portable).
"""
import copy
import hashlib
import math
import json
import locale
import os
import sys
import time
import traceback
import zipfile

from PyQt6.QtCore import QEasingCurve, QMarginsF, QVariantAnimation, QBuffer, QByteArray, QIODevice, QPointF, QRect, QRectF, QSize, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (QAction, QColor, QFont, QPageLayout, QPageSize, QPdfWriter, QDesktopServices, QIcon, QImage, QKeySequence, QPainter, QPen, QPixmap,
                         QShortcut)
from PyQt6.QtWidgets import (QAbstractItemView, QDialog, QApplication, QButtonGroup, QCheckBox, QColorDialog, QFileDialog, QInputDialog,
                             QFontComboBox, QPlainTextEdit, QTabWidget, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QListView, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
                             QSlider, QSpinBox, QVBoxLayout, QWidget)

import achtergrond as ach
import ballonnen as bl
import tekenen as tk
import drukker as dk
import figuren as fg
import planner as pl

VERSIE = "0.6.0"
APP = "DraveComic"


def _base():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def _res(*delen):
    b = getattr(sys, "_MEIPASS", None) or _base()
    p = os.path.join(b, *delen)
    return p if os.path.exists(p) else os.path.join(_base(), *delen)


DATA = os.path.join(_base(), "DraveComic-data")
os.makedirs(DATA, exist_ok=True)
INSTEL = os.path.join(DATA, "instellingen.json")
MIJN = os.path.join(DATA, "Mijn strips")
LOG = os.path.join(DATA, "error.log")


def _log(t):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + t + "\n")
    except Exception:
        pass


def _taal():
    try:
        t = (locale.getlocale()[0] or "") + (locale.getdefaultlocale()[0] or "")
    except Exception:
        t = ""
    return "nl" if ("nl" in t.lower() or "dutch" in t.lower() or not t) else "en"


NL = _taal() == "nl"
TX = {
    "nieuw": ("📄  Nieuw", "📄  New"), "open": ("📂  Openen", "📂  Open"), "opslaan": ("💾  Opslaan", "💾  Save"),
    "opslaan_als": ("Opslaan als…", "Save as…"), "png_lang": ("Bladzijde als plaatje", "Page as image"), "png": ("📷  Plaatje", "📷  Image"),
    "pagina": ("Bladzijden", "Pages"), "p_bij": ("+ Bladzijde", "+ Page"), "p_weg": ("− Weg", "− Remove"),
    "p_op": ("▲", "▲"), "p_neer": ("▼", "▼"),
    "indeling": ("Indeling (kies het aantal vakjes)", "Layout (choose the number of panels)"),
    "strip": ("Strip (3 rijen)", "Strip (3 rows)"), "tekenvak": ("✚  Zelf een vakje trekken", "✚  Draw a panel yourself"),
    "modus": ("Wat doet de muis?", "What does the mouse do?"),
    "m_vak": ("✋  Vakje verplaatsen", "✋  Move panel"), "m_plaat": ("🖐  Plaatje schuiven", "🖐  Move picture"),
    "vakje": ("Het gekozen vakje", "The chosen panel"),
    "plaat_in": ("📷  Plaatje invoegen", "📷  Insert picture"), "plaat_weg": ("Plaatje eruit", "Remove picture"),
    "passend": ("Plaatje passend", "Fit picture"), "zoom": ("Zoom", "Zoom"), "rand": ("Rand (dikte)", "Border (width)"),
    "vak_weg": ("❌  Vakje weghalen", "❌  Delete panel"), "ruimte": ("Ruimte tussen de vakjes", "Space between panels"),
    "ongedaan": ("↶  Ongedaan", "↶  Undo"), "opnieuw": ("↷  Opnieuw", "↷  Redo"),
    "geen_vak": ("Klik op een vakje om het te kiezen.", "Click a panel to choose it."),
    "hint": ("Dubbelklik op een vakje om er een plaatje in te zetten. Sleep een plaatje vanuit de Verkenner. "
             "Draai aan het muiswiel om in te zoomen.",
             "Double-click a panel to put a picture in it. Drag a picture from Explorer. Turn the mouse wheel to zoom."),
    "bewaard": ("Opgeslagen: %s", "Saved: %s"), "vraag_bewaren": ("Wil je je strip eerst opslaan?", "Save your comic first?"),
    "kies_plaat": ("Kies een plaatje", "Choose a picture"), "plaatjes": ("Plaatjes", "Pictures"),
    "project": ("DraveComic-strip", "DraveComic comic"), "fout_open": ("Dit bestand kon ik niet openen.", "I could not open this file."),
    "naamloos": ("Nieuwe strip", "New comic"), "blz": ("Bladzijde %d", "Page %d"),
    "eerst_vak": ("Kies eerst een vakje (klik erop).", "First choose a panel (click it)."),
    "png_klaar": ("Bladzijde bewaard als plaatje:\n%s", "Page saved as image:\n%s"),
    "snelgids": ("📖  Snelgids", "📖  Guide"), "over": ("ⓘ  Over", "ⓘ  About"),
    "over_tekst": ("DraveComic %s\n\nMaak je eigen stripboek.\n\nGratis (donationware) · GNU GPL v3.0\n"
                   "service@dravenlock.nl · dravenlock.nl",
                   "DraveComic %s\n\nMake your own comic book.\n\nFree (donationware) · GNU GPL v3.0\n"
                   "service@dravenlock.nl · dravenlock.nl"),
    "a_klein": ("A−", "A−"), "a_groot": ("A+", "A+"),
    "tab_vak": ("▦ Vakjes", "▦ Panels"),
    "pdf": ("📕  PDF", "📕  PDF"), "bladeren": ("📖  Bladeren", "📖  Read"),
    "alle_png": ("Alle bladzijden als plaatjes", "All pages as images"), "kaft_voor": ("📕 Voorkant", "📕 Front cover"),
    "kaft_achter": ("📗 Achterkant", "📗 Back cover"), "voorkant": ("Voorkant", "Front"), "achterkant": ("Achterkant", "Back"),
    "kaft_er": ("Er is al een %s. Je vindt hem in de lijst.", "There already is a %s. It is in the list."),
    "door": ("door ...", "by ..."), "achter_tekst": ("Gemaakt met DraveComic", "Made with DraveComic"),
    "pdf_klaar": ("Je boek staat in een PDF (%d bladzijden):\n%s\n\nWil je hem nu openen?",
                  "Your book is in a PDF (%d pages):\n%s\n\nOpen it now?"),
    "png_alle_klaar": ("%d plaatjes bewaard in:\n%s", "%d images saved in:\n%s"),
    "kies_map": ("Kies een map voor de plaatjes", "Choose a folder for the images"),
    "blader_hulp": ("◀ ▶ of de pijltjestoetsen: bladeren   ·   Spatie: twee bladzijden naast elkaar   ·   Esc: sluiten",
                    "◀ ▶ or the arrow keys: turn pages   ·   Space: two pages side by side   ·   Esc: close"),
    "sleep_hint": ("Sleep een bladzijde om de volgorde te veranderen.", "Drag a page to change the order."), "tab_teken": ("✏ Tekenen", "✏ Draw"), "tab_tekst": ("💬 Tekst", "💬 Text"),
    "t_nieuw": ("Nieuw (klik om toe te voegen)", "New (click to add)"),
    "t_praat": ("💬 Praatballon", "💬 Speech"), "t_denk": ("💭 Denkwolk", "💭 Thought"),
    "t_schreeuw": ("🗯 Schreeuw", "🗯 Shout"), "t_verteller": ("📜 Vertelblokje", "📜 Caption"),
    "t_geluid": ("💥 Geluidswoord", "💥 Sound effect"), "t_gekozen": ("Gekozen tekst", "Chosen text"),
    "t_geen": ("Klik op een ballon of geluidswoord om hem te kiezen.", "Click a balloon or sound effect to choose it."),
    "t_grootte": ("Lettergrootte", "Letter size"), "t_lettertype": ("Lettertype", "Font"),
    "t_vet": ("B  Vet", "B  Bold"), "t_schuin": ("I  Schuin", "I  Italic"), "t_strip": ("↺ Strip", "↺ Comic"), "t_letter": ("Letterkleur", "Letter colour"),
    "t_vulling": ("Vulkleur", "Fill colour"), "t_draai": ("Draaien", "Rotate"), "t_ster": ("Ster erachter", "Star behind"),
    "t_staart": ("Staartje aan", "Tail on"), "t_voor": ("Naar voren", "To front"), "t_achter": ("Naar achteren", "To back"),
    "t_weg": ("❌  Tekst weghalen", "❌  Delete text"), "t_woorden": ("Snel een geluidswoord", "Quick sound word"),
    "t_hint": ("Sleep een ballon om hem te verplaatsen; sleep aan de oranje blokjes om hem groter te maken. "
               "Sleep de gele bol om het staartje naar de prater te laten wijzen. Typ de tekst in het vak hierboven.",
               "Drag a balloon to move it; drag the orange squares to resize. Drag the yellow ball to point the tail "
               "at the speaker. Type the text in the box above."),
    "gereedschap": ("Gereedschap", "Tools"), "vormen": ("Vormen", "Shapes"),
    "g_pen": ("✒ Pen", "✒ Pen"), "g_potlood": ("✏ Potlood", "✏ Pencil"), "g_penseel": ("🖌 Penseel", "🖌 Ink brush"),
    "g_gum": ("🧽 Gum", "🧽 Eraser"), "g_emmer": ("🪣 Emmertje", "🪣 Fill"), "g_pipet": ("💧 Kleur pakken", "💧 Pick colour"),
    "g_lijn": ("╱ Lijn", "╱ Line"), "g_rechthoek": ("▭ Rechthoek", "▭ Rectangle"), "g_cirkel": ("◯ Cirkel", "◯ Circle"),
    "g_pijl": ("➜ Pijl", "➜ Arrow"), "g_snelheid": ("≡ Snelheid", "≡ Speed lines"),
    "gevuld": ("Vorm gevuld", "Filled shape"), "kleur": ("Kleur", "Colour"), "andere_kleur": ("Andere kleur…", "Other colour…"),
    "dikte": ("Dikte", "Size"), "binnen": ("Binnen het vakje blijven", "Stay inside the panel"),
    "lagen": ("Lagen (bovenste staat bovenaan)", "Layers (top one first)"), "l_bij": ("+ Laag", "+ Layer"),
    "l_weg": ("− Laag", "− Layer"), "dekking": ("Doorzichtig", "Opacity"), "laag": ("Laag %d", "Layer %d"),
    "inkt": ("Inkt", "Ink"), "laag_naam": ("Naam van de laag:", "Layer name:"),
    "laag_uit": ("Deze laag staat uit (het oogje). Zet hem eerst aan.", "This layer is hidden. Show it first."),
    "teken_hint": ("Teken met de linkermuisknop. Met [ en ] maak je de lijn dunner of dikker. "
                   "Het penseel wordt dunner als je snel beweegt, net als echte inkt. "
                   "Dubbelklik op een laag om hem een naam te geven; het vinkje zet hem aan of uit.",
                   "Draw with the left mouse button. [ and ] make the line thinner or thicker. "
                   "The brush gets thinner when you move fast, like real ink. "
                   "Double-click a layer to name it; the tick shows or hides it."),
    "tab_ach": ("🌄 Achtergrond", "🌄 Background"),
    "drukker": ("🖨  Drukker", "🖨  Printer"), "planner": ("📝  Planner", "📝  Planner"),
    "druk_leeg": ("Er zijn nog geen bladzijden (naast de kaft).", "There are no pages yet (besides the cover)."),
    "druk_map": ("Kies een map voor de drukklare PDF's", "Choose a folder for the print-ready PDFs"),
    "druk_binnen": ("binnenwerk", "inside"), "druk_kaft": ("kaft", "cover"),
    "druk_fout": ("Het maken van de PDF's lukte niet:\n%s", "Making the PDFs failed:\n%s"),
    "druk_klaar": ("Klaar voor de drukker!\n\nBinnenwerk: %d bladzijden\nRug: %.1f mm\nKaft: %.1f x %.1f mm (met afloop)\n\n%s\n%s\n\nWil je de map openen?",
                   "Ready for the printer!\n\nInside: %d pages\nSpine: %.1f mm\nCover: %.1f x %.1f mm (with bleed)\n\n%s\n%s\n\nOpen the folder?"),
    "plan_bewaard": ("Het plan is bewaard in je strip (sla de strip nog wel op).", "The plan is kept in your comic (do save the comic)."),
    "plan_vraag": ("Ik zet nu %d bladzijde(n) klaar, met vakjes, ballonnen en wat er in elk vakje moet komen.\nDoorgaan?",
                   "I will now add %d page(s), with panels, balloons and what goes in each panel.\nContinue?"),
    "plan_klaar": ("%d bladzijde(n) klaargezet. In elk leeg vakje staat wat erin moet komen.", "%d page(s) added. Every empty panel shows what goes in it."),
    "tab_fig": ("🦸 Figuren", "🦸 Characters"),
    "f_kast": ("Personage-kast", "Character closet"),
    "f_uitleg": ("Teken je figuur één keer (tabblad Tekenen), klik op het vakje en dan op 'Bewaar uit tekening'. "
                 "Daarna zet je hem met één klik op elke bladzijde.",
                 "Draw your character once (Draw tab), click the panel, then 'Save from drawing'. "
                 "After that you put it on any page with one click."),
    "f_plaats": ("▶  Op de bladzijde zetten", "▶  Put on the page"),
    "f_uit_tekening": ("✏  Bewaar uit tekening (gekozen vakje)", "✏  Save from drawing (chosen panel)"),
    "f_eigen": ("📷  Eigen plaatje in de kast", "📷  Own picture into the closet"),
    "f_naam": ("Naam…", "Name…"), "f_uit_kast": ("🗑  Uit de kast", "🗑  Out of the closet"),
    "f_gekozen": ("Gekozen figuur", "Chosen character"),
    "f_geen": ("Klik op een figuur op de bladzijde om hem te kiezen.", "Click a character on the page to choose it."),
    "f_spiegel": ("⇆ Spiegelen", "⇆ Mirror"), "f_weg": ("❌  Figuur weghalen", "❌  Remove character"),
    "f_hint": ("Sleep een figuur om hem te verplaatsen. Sleep aan de oranje blokjes om hem groter of kleiner te maken. "
               "De kast staat in DraveComic-data\\Personages.",
               "Drag a character to move it. Drag the orange handles to make it bigger or smaller. "
               "The closet is in DraveComic-data\\Personages."),
    "f_kast_leeg": ("De kast is nog leeg. Bewaar eerst een figuur uit je tekening of een eigen plaatje.",
                    "The closet is still empty. First save a character from your drawing or your own picture."),
    "f_geen_tekening": ("Ik vind hier geen tekening. Teken eerst je figuur (tabblad Tekenen) in het gekozen vakje.",
                        "I find no drawing here. First draw your character (Draw tab) in the chosen panel."),
    "f_naam_vraag": ("Hoe heet deze figuur?", "What is this character called?"), "f_standaard": ("Mijn held", "My hero"),
    "f_vervang": ("'%s' staat in de kast.\n\nWil je de tekening hier meteen vervangen door de figuur? "
                  "Dan kun je hem verschuiven en groter of kleiner maken.",
                  "'%s' is in the closet.\n\nReplace the drawing here by the character right away? "
                  "Then you can move it and make it bigger or smaller."),
    "f_bewaard": ("'%s' staat in de kast.", "'%s' is in the closet."),
    "f_weg_vraag": ("'%s' uit de kast halen?\n(Op bladzijden waar hij al staat, blijft hij staan.)",
                    "Remove '%s' from the closet?\n(Pages where it already is keep it.)"),

    "tablet_gevonden": ("✍  Tekentablet gevonden: druk zacht voor een dunne lijn, hard voor een dikke. De achterkant van de pen is de gum.",
                        "✍  Drawing tablet found: press lightly for a thin line, hard for a thick one. The back of the pen is the eraser."),
    "b_sluit": ("✕  Sluiten", "✕  Close"), "b_dubbel": ("⧉  Twee naast elkaar", "⧉  Two side by side"),
    "a_voor": ("Achtergrond voor", "Background for"), "a_vak": ("▦  Gekozen vakje", "▦  Chosen panel"),
    "a_pag": ("📄  Hele bladzijde", "📄  Whole page"),
    "a_lagen": ("Lagen (bovenste staat bovenaan)", "Layers (top one first)"),
    "a_leeg": ("Nog geen achtergrond. Kies hieronder wat je wilt toevoegen.", "No background yet. Choose below what to add."),
    "a_gekozen": ("Gekozen laag", "Chosen layer"), "a_anders": ("🎲  Anders", "🎲  Shuffle"),
    "a_spiegel": ("⇆  Spiegelen", "⇆  Mirror"), "a_weg": ("❌  Laag weg", "❌  Remove layer"),
    "a_alle": ("📋  Ook in alle vakjes", "📋  Also in all panels"), "a_toevoegen": ("Laag toevoegen", "Add a layer"),
    "a_plaat": ("📷  Eigen plaatje", "📷  Own picture"), "a_teken": ("✏  Zelf tekenen", "✏  Draw it yourself"),
    "a_tekening": ("Achtergrond-tekening", "Background drawing"),
    "a_teken_klaar": ("Teken nu je achtergrond. Deze laag ligt achter de plaatjes (zie het vinkje bij de lagen).",
                      "Draw your background now. This layer lies behind the pictures (see the tick under the layers)."),
    "a_achter": ("🌄  Achter de plaatjes (achtergrond)", "🌄  Behind the pictures (background)"),
    "a_alle_vraag": ("De achtergrond van dit vakje ook in alle andere vakjes van deze bladzijde zetten?\n"
                     "(Wat daar nu als achtergrond staat, wordt vervangen.)",
                     "Put the background of this panel in all other panels of this page too?\n"
                     "(Their current backgrounds are replaced.)"),
    "a_hint": ("Stapel lagen: eerst een lucht, dan bergen of een stad, dan bomen of regen erbovenop. "
               "Een eigen plaatje schuif je door te slepen in het vakje; met het muiswiel zoom je in. "
               "Heeft een vakje geen eigen achtergrond, dan zie je die van de bladzijde erdoorheen. "
               "Tip: een plaatje in een vakje met doorzichtige delen (PNG) laat de achtergrond zien.",
               "Stack layers: first a sky, then mountains or a city, then trees or rain on top. "
               "Drag in the panel to move your own picture; the mouse wheel zooms. "
               "A panel without its own background shows the page background. "
               "Tip: a picture with see-through parts (PNG) shows the background."),
}


def T(k):
    v = TX.get(k, (k, k))
    return v[0] if NL else v[1]


# ------------------------------------------------------------------ het boek (gewone dicts: makkelijk opslaan + ongedaan maken)
PB, PH = 1000.0, 1414.0            # een bladzijde (A4-verhouding), in eigen eenheden
MARGE = 40.0


def indeling(soort, ruimte=20.0):
    """Vakjes voor een kant-en-klare indeling. soort: 1, 2, 3, 4, 6 of 'strip'."""
    x0, y0, b, h, r = MARGE, MARGE, PB - 2 * MARGE, PH - 2 * MARGE, ruimte

    def rij(y, hh, n):
        w = (b - (n - 1) * r) / n
        return [(x0 + i * (w + r), y, w, hh) for i in range(n)]

    if soort == 1:
        rs = [(x0, y0, b, h)]
    elif soort == 2:
        hh = (h - r) / 2
        rs = rij(y0, hh, 1) + rij(y0 + hh + r, hh, 1)
    elif soort == 3:
        hh = (h - r) / 2
        rs = rij(y0, hh, 1) + rij(y0 + hh + r, hh, 2)
    elif soort == 4:
        hh = (h - r) / 2
        rs = rij(y0, hh, 2) + rij(y0 + hh + r, hh, 2)
    elif soort == 6:
        hh = (h - 2 * r) / 3
        rs = rij(y0, hh, 2) + rij(y0 + hh + r, hh, 2) + rij(y0 + 2 * (hh + r), hh, 2)
    else:                                    # strip: 3 rijen, 2-3-2
        hh = (h - 2 * r) / 3
        rs = rij(y0, hh, 2) + rij(y0 + hh + r, hh, 3) + rij(y0 + 2 * (hh + r), hh, 2)
    return [dict(x=round(x, 1), y=round(y, 1), w=round(w, 1), h=round(hh2, 1), rand=6, beeld=None)
            for x, y, w, hh2 in rs]


def nieuw_boek():
    return dict(versie=1, titel=T("naamloos"), ruimte=20, paginas=[dict(vakjes=indeling(4))])


# ------------------------------------------------------------------ tekenen van een bladzijde (ook voor PNG en straks PDF)
class Beelden:
    """De plaatjes van het boek: id -> bytes (zo gaan ze mee in het projectbestand) en een QImage-cache."""

    def __init__(self):
        self.data, self.cache = {}, {}
        self.lagen = {}               # laag-id -> QImage (doorzichtig, tk.LB x tk.LH)

    def nieuwe_laag(self):
        lid = "l" + hashlib.md5(("%f%d" % (time.time(), len(self.lagen))).encode()).hexdigest()[:12]
        self.lagen[lid] = tk.lege_laag()
        return lid

    def voeg_toe(self, pad):
        with open(pad, "rb") as f:
            b = f.read()
        im = QImage.fromData(b)
        if im.isNull():
            return None
        bid = hashlib.md5(b).hexdigest()[:16]
        self.data[bid], self.cache[bid] = b, im
        return bid

    def voeg_bytes(self, b):
        im = QImage.fromData(b)
        if im.isNull():
            return None
        bid = hashlib.md5(b).hexdigest()[:16]
        self.data[bid], self.cache[bid] = b, im
        return bid

    def beeld(self, bid):
        if bid not in self.cache and bid in self.data:
            self.cache[bid] = QImage.fromData(self.data[bid])
        return self.cache.get(bid)


def zorg_lagen(pag, beelden):
    """Elke bladzijde heeft minstens één laag (ook bij een strip van versie 0.1)."""
    if not pag.get("lagen"):
        pag["lagen"] = [dict(id=beelden.nieuwe_laag(), naam=T("inkt"), zicht=True, dekking=1.0)]
    for l in pag["lagen"]:
        if l["id"] not in beelden.lagen:
            beelden.lagen[l["id"]] = tk.lege_laag()


def teken_pagina(p, pag, beelden, schaal=1.0, gekozen=None, hulp=False, wenk=None):
    """Tekent bladzijde 'pag' met painter p in eenheden * schaal (oorsprong 0,0)."""
    p.save()
    p.scale(schaal, schaal)
    p.fillRect(QRectF(0, 0, PB, PH), QColor("#ffffff"))
    # achtergronden (laag op laag): eerst de hele bladzijde, dan per vakje
    try:
        ach.teken(p, pag.get("achtergrond"), QRectF(0, 0, PB, PH), beelden)
        for v in pag["vakjes"]:
            if v.get("achtergrond"):
                ach.teken(p, v["achtergrond"], QRectF(v["x"], v["y"], v["w"], v["h"]), beelden)
    except Exception as e:
        _log("achtergrond tekenen: %s" % e)
    # zelf getekende achtergrond-lagen liggen achter de plaatjes
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for l in pag.get("lagen", []):
        im = beelden.lagen.get(l["id"])
        if im is not None and l.get("zicht", True) and l.get("achter"):
            p.setOpacity(max(0.0, min(1.0, l.get("dekking", 1.0))))
            p.drawImage(QRectF(0, 0, PB, PH), im)
    p.setOpacity(1.0)
    for i, v in enumerate(pag["vakjes"]):
        r = QRectF(v["x"], v["y"], v["w"], v["h"])
        b = v.get("beeld")
        im = beelden.beeld(b["id"]) if b else None
        if im is not None and not im.isNull():
            p.save()
            p.setClipRect(r)
            basis = max(r.width() / im.width(), r.height() / im.height())
            s = basis * b.get("zoom", 1.0)
            w, h = im.width() * s, im.height() * s
            doel = QRectF(r.center().x() - w / 2 + b.get("dx", 0), r.center().y() - h / 2 + b.get("dy", 0), w, h)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawImage(doel, im)
            p.restore()
        elif hulp and v.get("plan"):
            p.setPen(QColor("#8a80b8"))
            f = p.font()
            f.setPixelSize(24)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(r.adjusted(18, 14, -18, -14), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom |
                                                        Qt.TextFlag.TextWordWrap), "📝 " + v["plan"])
        elif (hulp if wenk is None else wenk) and not v.get("achtergrond") and not pag.get("achtergrond"):
            p.setPen(QColor("#b9b2d6"))
            f = p.font()
            f.setPixelSize(26)
            p.setFont(f)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "📷\n" + ("dubbelklik" if NL else "double-click"))
        if v.get("rand", 6) > 0:
            pen = QPen(QColor("#111111"), v.get("rand", 6))
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            d = v.get("rand", 6) / 2
            p.drawRect(r.adjusted(d, d, -d, -d))
    # de getekende lagen liggen boven de vakjes
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    for l in pag.get("lagen", []):
        im = beelden.lagen.get(l["id"])
        if im is not None and l.get("zicht", True) and not l.get("achter"):
            p.setOpacity(max(0.0, min(1.0, l.get("dekking", 1.0))))
            p.drawImage(QRectF(0, 0, PB, PH), im)
    p.setOpacity(1.0)
    # ballonnen, vertelblokjes en geluidswoorden liggen bovenop
    for t in pag.get("teksten", []):
        try:
            bl.teken(p, t)
        except Exception as e:
            _log("tekst tekenen: %s" % e)
    for i, v in enumerate(pag["vakjes"]):
        r = QRectF(v["x"], v["y"], v["w"], v["h"])
        if hulp and i == gekozen:
            p.setPen(QPen(QColor("#ffb020"), 5, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(r.adjusted(-4, -4, 4, 4))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#ffb020"))
            for hx, hy in _hoeken(r):
                p.drawRect(QRectF(hx - 11, hy - 11, 22, 22))
    p.restore()


def _hoeken(r):
    """De 8 grepen van een vakje: hoeken en middens van de zijden."""
    return [(r.left(), r.top()), (r.center().x(), r.top()), (r.right(), r.top()), (r.right(), r.center().y()),
            (r.right(), r.bottom()), (r.center().x(), r.bottom()), (r.left(), r.bottom()), (r.left(), r.center().y())]


# ------------------------------------------------------------------ het tekenvlak
class Vlak(QWidget):
    veranderd = pyqtSignal()          # na een echte wijziging (voor ongedaan maken + miniaturen)
    gekozen_ander = pyqtSignal()

    def __init__(self, hoofd):
        super().__init__()
        self.h = hoofd
        self.setMinimumSize(500, 500)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.gekozen = None
        self.modus = "vak"            # vak / plaat / nieuwvak / verf
        self.sleep = None             # (soort, start-punt, origineel)
        self.streek = None
        self.muis = None
        self.tgekozen = None          # gekozen tekst-ding (index in pagina["teksten"])
        self.druk, self.druk_tijd, self.tablet_gum = None, 0.0, False   # tekentablet (0.6.0)
        self.tablet_gemeld = False

    # -- omrekenen
    def _maat(self):
        s = min((self.width() - 40) / PB, (self.height() - 40) / PH)
        ox = (self.width() - PB * s) / 2
        oy = (self.height() - PH * s) / 2
        return s, ox, oy

    def naar_pagina(self, pos):
        s, ox, oy = self._maat()
        return QPointF((pos.x() - ox) / s, (pos.y() - oy) / s)

    @property
    def pag(self):
        return self.h.boek["paginas"][self.h.nu]

    def vak_op(self, pt):
        for i in range(len(self.pag["vakjes"]) - 1, -1, -1):
            v = self.pag["vakjes"][i]
            if QRectF(v["x"], v["y"], v["w"], v["h"]).contains(pt):
                return i
        return None

    def greep_op(self, pt):
        if self.gekozen is None or self.gekozen >= len(self.pag["vakjes"]):
            return None
        v = self.pag["vakjes"][self.gekozen]
        s, _, _ = self._maat()
        straal = 16 / s
        for i, (hx, hy) in enumerate(_hoeken(QRectF(v["x"], v["y"], v["w"], v["h"]))):
            if abs(pt.x() - hx) <= straal and abs(pt.y() - hy) <= straal:
                return i
        return None

    # -- tekenen
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#0d0b14"))
        s, ox, oy = self._maat()
        p.fillRect(QRectF(ox + 8, oy + 10, PB * s, PH * s), QColor(0, 0, 0, 120))      # schaduw
        p.translate(ox, oy)
        teken_pagina(p, self.pag, self.h.beelden, s, self.gekozen, hulp=True,
                     wenk=self.modus in ("vak", "plaat", "nieuwvak"))
        if self.sleep and self.sleep[0] == "nieuw":
            a, b = self.sleep[1], self.sleep[2]
            p.setPen(QPen(QColor("#7F77DD"), 3, Qt.PenStyle.DashLine))
            p.setBrush(QColor(127, 119, 221, 50))
            p.drawRect(QRectF(a.x() * s, a.y() * s, (b.x() - a.x()) * s, (b.y() - a.y()) * s).normalized())
        if self.modus == "tekst" and self._tekst() is not None:
            t = self._tekst()
            p.save()
            p.scale(s, s)
            p.setPen(QPen(QColor("#ffb020"), 3, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(bl.buitenkant(t).adjusted(-6, -6, 6, 6))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#ffb020"))
            for hx, hy in _hoeken(bl.vak(t)):
                p.drawRect(QRectF(hx - 10, hy - 10, 20, 20))
            if t.get("staart"):
                p.setPen(QPen(QColor("#111111"), 3))
                p.setBrush(QColor("#ffe14a"))
                p.drawEllipse(QPointF(*t["staart"]), 16, 16)
            p.restore()
        if self.modus == "verf":
            g = self.h.gs
            if self.sleep and self.sleep[0] == "vorm":
                p.save()
                p.scale(s, s)
                if self.sleep[3] is not None:
                    p.setClipRect(self.sleep[3])
                tk.teken_vorm(p, g.soort, self.sleep[1], self.sleep[2], g.kleur, g.dikte, g.gevuld)
                p.restore()
            if self.muis is not None and g.soort in tk.UIT_DE_HAND + tk.VORMEN:
                w = g.dikte * (2.0 if g.soort == "gum" else (0.5 if g.soort == "potlood" else 1.0))
                rr = max(3.0, w * s / 2)
                c = QPointF(self.muis.x() * s, self.muis.y() * s)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#000000"), 3))
                p.drawEllipse(c, rr, rr)
                p.setPen(QPen(QColor("#ffffff"), 1.5))
                p.drawEllipse(c, rr, rr)
        p.end()

    # -- teksten
    def _teksten(self):
        return self.pag.setdefault("teksten", [])

    def _tekst(self):
        ts = self.pag.get("teksten", [])
        return ts[self.tgekozen] if self.tgekozen is not None and 0 <= self.tgekozen < len(ts) else None

    def _tekst_druk(self, pt):
        s, _, _ = self._maat()
        straal = 18 / s
        t = self._tekst()
        if t is not None:
            st = t.get("staart")
            if st and math.hypot(pt.x() - st[0], pt.y() - st[1]) <= straal + 6:
                self.sleep = ["staart", pt, list(st)]
                return
            for i, (hx, hy) in enumerate(_hoeken(bl.vak(t))):
                if abs(pt.x() - hx) <= straal and abs(pt.y() - hy) <= straal:
                    self.sleep = ["tgreep", pt, copy.deepcopy(t), i]
                    return
        gevonden = None
        for i in range(len(self._teksten()) - 1, -1, -1):
            if bl.raak(self._teksten()[i], pt):
                gevonden = i
                break
        self.tgekozen = gevonden
        self.h.tekst_bij()
        self.sleep = ["tschuif", pt, copy.deepcopy(self._teksten()[gevonden])] if gevonden is not None else None
        self.update()

    def _tekst_beweeg(self, pt):
        soort, start = self.sleep[0], self.sleep[1]
        dx, dy = pt.x() - start.x(), pt.y() - start.y()
        t = self._tekst()
        if t is None:
            return
        if soort == "staart":
            t["staart"] = [min(PB, max(0, self.sleep[2][0] + dx)), min(PH, max(0, self.sleep[2][1] + dy))]
        elif soort == "tschuif":
            o = self.sleep[2]
            t["x"], t["y"] = round(o["x"] + dx), round(o["y"] + dy)
        elif soort == "tgreep":
            o, g = self.sleep[2], self.sleep[3]
            l, tp, rr, b = o["x"], o["y"], o["x"] + o["w"], o["y"] + o["h"]
            if g in (0, 6, 7):
                l = min(l + dx, rr - 50)
            if g in (2, 3, 4):
                rr = max(rr + dx, l + 50)
            if g in (0, 1, 2):
                tp = min(tp + dy, b - 40)
            if g in (4, 5, 6):
                b = max(b + dy, tp + 40)
            t["x"], t["y"], t["w"], t["h"] = round(l), round(tp), round(rr - l), round(b - tp)
        self.update()

    def _clip(self, pt):
        if not self.h.gs.binnen:
            return None
        i = self.vak_op(pt)
        if i is None:
            return None
        v = self.pag["vakjes"][i]
        return QRectF(v["x"], v["y"], v["w"], v["h"])

    def tabletEvent(self, e):
        """Tekentablet: we onthouden hoe hard de pen drukt en of het de gum-kant is. Daarna laat Qt er
        gewoon een muis-gebeurtenis van maken, zodat alles verder werkt zoals met de muis."""
        try:
            self.druk = float(e.pressure())
            self.druk_tijd = time.monotonic()
            from PyQt6.QtGui import QPointingDevice
            self.tablet_gum = e.pointerType() == QPointingDevice.PointerType.Eraser
            if self.streek is not None and self.sleep and self.sleep[0] == "streek":
                self.streek.druk = self.druk
            if not self.tablet_gemeld and self.modus == "verf":
                self.tablet_gemeld = True
                self.h.statusBar().showMessage(T("tablet_gevonden"), 10000)
        except Exception:
            pass
        e.ignore()

    def _tablet(self):
        """Komt deze muis-gebeurtenis van de tablet-pen? (vlak na een tablet-gebeurtenis)"""
        return self.druk is not None and time.monotonic() - self.druk_tijd < 0.25

    def _verf_druk(self, pt):
        g, h = self.h.gs, self.h
        if self._tablet() and self.tablet_gum and g.soort != "gum":
            g = copy.copy(g)
            g.soort = "gum"

        laag, lid = h.huidige_laag()
        if g.soort == "pipet":
            im = h.samen_beeld()
            x, y = int(pt.x() * tk.LS), int(pt.y() * tk.LS)
            if 0 <= x < im.width() and 0 <= y < im.height():
                h.zet_kleur(QColor(im.pixel(x, y)))
            return
        if laag is None:
            h.statusBar().showMessage(T("laag_uit"), 6000)
            return
        clip = self._clip(pt)
        if g.soort in tk.UIT_DE_HAND:
            self.streek = tk.Streek(laag, g, pt, clip, druk=self.druk if self._tablet() else None)
            self.sleep = ["streek", pt]
        elif g.soort == "emmer":
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                res = tk.vul(h.samen_beeld(), laag, pt, g.kleur, clip)
            finally:
                QApplication.restoreOverrideCursor()
            if res:
                h.pixel_stap(lid, *res)
        elif g.soort in tk.VORMEN:
            self.sleep = ["vorm", pt, pt, clip]
        self.update()

    # -- muis
    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        pt = self.naar_pagina(e.position())
        if self.modus == "verf":
            self._verf_druk(pt)
            return
        if self.modus == "tekst":
            self._tekst_druk(pt)
            return
        if self.modus == "achter":
            i = self.vak_op(pt)
            if self.h.ach_doel == "vak" and i != self.gekozen and i is not None:
                self.gekozen = i
                self.gekozen_ander.emit()
            sp = self.h.ach_laag()
            if sp is not None and sp.get("soort") == "plaat" and (self.h.ach_doel == "pagina" or i == self.gekozen):
                self.sleep = ["achplaat", pt, dict(dx=sp.get("dx", 0.0), dy=sp.get("dy", 0.0))]
            else:
                self.sleep = None
            self.update()
            return
        if self.modus == "nieuwvak":
            self.sleep = ["nieuw", pt, pt]
            return
        g = self.greep_op(pt)
        if g is not None:
            self.sleep = ["greep", pt, copy.deepcopy(self.pag["vakjes"][self.gekozen]), g]
            return
        i = self.vak_op(pt)
        if i != self.gekozen:
            self.gekozen = i
            self.gekozen_ander.emit()
        if i is None:
            self.sleep = None
        elif self.modus == "plaat" and self.pag["vakjes"][i].get("beeld"):
            self.sleep = ["plaat", pt, copy.deepcopy(self.pag["vakjes"][i]["beeld"])]
        else:
            self.sleep = ["vak", pt, copy.deepcopy(self.pag["vakjes"][i])]
        self.update()

    def mouseMoveEvent(self, e):
        pt = self.naar_pagina(e.position())
        if self.modus == "verf":
            self.muis = pt
            self.setCursor(Qt.CursorShape.CrossCursor if self.h.gs.soort in ("emmer", "pipet") else Qt.CursorShape.BlankCursor)
            if self.sleep and self.sleep[0] == "streek" and self.streek:
                self.streek.beweeg(pt)
            elif self.sleep and self.sleep[0] == "vorm":
                self.sleep[2] = pt
            self.update()
            return
        if self.modus == "tekst":
            if self.sleep:
                self._tekst_beweeg(pt)
            else:
                t = self._tekst()
                op = any(bl.raak(x, pt) for x in self._teksten())
                self.setCursor(Qt.CursorShape.SizeAllCursor if op else Qt.CursorShape.ArrowCursor)
            return
        if self.modus == "achter":
            if self.sleep and self.sleep[0] == "achplaat":
                sp = self.h.ach_laag()
                if sp is not None:
                    sp["dx"] = self.sleep[2]["dx"] + pt.x() - self.sleep[1].x()
                    sp["dy"] = self.sleep[2]["dy"] + pt.y() - self.sleep[1].y()
                self.update()
            else:
                sp = self.h.ach_laag()
                plaat = sp is not None and sp.get("soort") == "plaat"
                self.setCursor(Qt.CursorShape.OpenHandCursor if plaat else Qt.CursorShape.PointingHandCursor)
            return
        if not self.sleep:
            g = self.greep_op(pt)
            vormen = [Qt.CursorShape.SizeFDiagCursor, Qt.CursorShape.SizeVerCursor, Qt.CursorShape.SizeBDiagCursor,
                      Qt.CursorShape.SizeHorCursor] * 2
            if g is not None:
                self.setCursor(vormen[g])
            elif self.modus == "nieuwvak":
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self.vak_op(pt) is not None:
                self.setCursor(Qt.CursorShape.OpenHandCursor if self.modus == "plaat" else Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        soort, start = self.sleep[0], self.sleep[1]
        dx, dy = pt.x() - start.x(), pt.y() - start.y()
        if soort == "nieuw":
            self.sleep[2] = pt
        elif soort == "plaat":
            b = self.pag["vakjes"][self.gekozen]["beeld"]
            b["dx"], b["dy"] = self.sleep[2].get("dx", 0) + dx, self.sleep[2].get("dy", 0) + dy
        elif soort == "vak":
            v, o = self.pag["vakjes"][self.gekozen], self.sleep[2]
            v["x"] = _klik(min(max(0, o["x"] + dx), PB - o["w"]))
            v["y"] = _klik(min(max(0, o["y"] + dy), PH - o["h"]))
        elif soort == "greep":
            v, o, g = self.pag["vakjes"][self.gekozen], self.sleep[2], self.sleep[3]
            l, t, r, b = o["x"], o["y"], o["x"] + o["w"], o["y"] + o["h"]
            if g in (0, 6, 7):
                l = min(_klik(l + dx), r - 60)
            if g in (2, 3, 4):
                r = max(_klik(r + dx), l + 60)
            if g in (0, 1, 2):
                t = min(_klik(t + dy), b - 60)
            if g in (4, 5, 6):
                b = max(_klik(b + dy), t + 60)
            v["x"], v["y"], v["w"], v["h"] = max(0, l), max(0, t), min(PB, r) - max(0, l), min(PH, b) - max(0, t)
        self.update()

    def mouseReleaseEvent(self, e):
        if not self.sleep:
            return
        soort = self.sleep[0]
        if soort == "streek" and self.streek:
            rr, voor, na = self.streek.klaar()
            self.streek = None
            self.sleep = None
            self.h.pixel_stap(self.h.huidige_laag()[1], rr, voor, na)
            self.update()
            return
        if soort == "vorm":
            a, b, clip = self.sleep[1], self.sleep[2], self.sleep[3]
            self.sleep = None
            laag, lid = self.h.huidige_laag()
            g = self.h.gs
            if laag is not None and (abs(b.x() - a.x()) > 2 or abs(b.y() - a.y()) > 2):
                self.h.pixel_stap(lid, *tk.zet_vorm(laag, g.soort, a, b, g.kleur, g.dikte, g.gevuld, clip))
            self.update()
            return
        if soort in ("staart", "tschuif", "tgreep"):
            self.sleep = None
            self.veranderd.emit()
            self.update()
            return
        if soort == "nieuw":
            a, b = self.sleep[1], self.sleep[2]
            r = QRectF(a, b).normalized()
            if r.width() > 40 and r.height() > 40:
                self.pag["vakjes"].append(dict(x=_klik(r.x()), y=_klik(r.y()), w=_klik(r.width()), h=_klik(r.height()),
                                               rand=6, beeld=None))
                self.gekozen = len(self.pag["vakjes"]) - 1
                self.gekozen_ander.emit()
                self.veranderd.emit()
        else:
            self.veranderd.emit()
        self.sleep = None
        self.update()

    def leaveEvent(self, e):
        self.muis = None
        self.update()

    def mouseDoubleClickEvent(self, e):
        if self.modus in ("verf", "achter"):
            return
        if self.modus == "tekst":
            if self._tekst() is not None:
                self.h.t_tekst.setFocus()
                self.h.t_tekst.selectAll()
            return
        i = self.vak_op(self.naar_pagina(e.position()))
        if i is not None:
            self.gekozen = i
            self.gekozen_ander.emit()
            self.h.plaatje_invoegen()

    def wheelEvent(self, e):
        if self.modus == "verf":
            self.h.zet_dikte(self.h.gs.dikte + (1 if e.angleDelta().y() > 0 else -1))
            return
        if self.modus == "achter":
            sp = self.h.ach_laag()
            if sp is not None and sp.get("soort") == "plaat":
                f = 1.1 if e.angleDelta().y() > 0 else 1 / 1.1
                sp["zoom"] = round(min(6.0, max(0.2, sp.get("zoom", 1.0) * f)), 3)
                self.update()
                self.h.ach_zoom_bij()
                self.h.later_veranderd()
            return
        i = self.vak_op(self.naar_pagina(e.position()))
        if i is None or not self.pag["vakjes"][i].get("beeld"):
            return
        if i != self.gekozen:
            self.gekozen = i
            self.gekozen_ander.emit()
        b = self.pag["vakjes"][i]["beeld"]
        f = 1.1 if e.angleDelta().y() > 0 else 1 / 1.1
        b["zoom"] = round(min(6.0, max(0.2, b.get("zoom", 1.0) * f)), 3)
        self.update()
        self.h.zoom_bij()
        self.h.later_veranderd()

    def keyPressEvent(self, e):
        if self.modus == "verf" and e.key() in (Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight):
            self.h.zet_dikte(self.h.gs.dikte + (-1 if e.key() == Qt.Key.Key_BracketLeft else 1))
        elif e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self.modus == "tekst":
            self.h.tekst_weg()
        elif e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self.modus not in ("verf", "achter"):
            self.h.vak_weg()
        else:
            super().keyPressEvent(e)

    # -- plaatjes slepen vanuit de Verkenner
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        urls = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if not urls:
            return
        i = self.vak_op(self.naar_pagina(e.position()))
        if self.modus == "achter":
            if self.h.ach_doel == "vak":
                if i is None:
                    return
                self.gekozen = i
                self.gekozen_ander.emit()
            self.h.ach_plaat(urls[0])
            return
        if i is None:
            return
        self.gekozen = i
        self.gekozen_ander.emit()
        self.h.zet_plaatje(urls[0])


def _klik(w):
    """Uitlijnen op een raster van 10 (vakjes staan dan mooi recht)."""
    return round(w / 10.0) * 10.0


# ------------------------------------------------------------------ bladeren (lezen zoals een echt boek)
class Bladeren(QDialog):
    def __init__(self, hoofd):
        super().__init__(hoofd)
        self.h = hoofd
        self.setWindowTitle("%s - %s" % (APP, T("bladeren").strip("📖 ")))
        self.setStyleSheet("QDialog { background: #0d0b14; } QLabel { color: #b9b2d6; font-size: 16px; }"
                           "QPushButton { background: #221c33; color: #efeaff; border: 2px solid #4a3d66; border-radius: 12px;"
                           " font-size: 34px; padding: 10px 22px; } QPushButton:hover { border-color: #ffd166; }")
        self.i = hoofd.nu
        self.dubbel = False
        self.cache = {}
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(260)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(lambda _: self.update())
        self.richting = 0
        v = QVBoxLayout(self)
        v.addStretch(1)
        onder = QHBoxLayout()
        self.terug = QPushButton("◀")
        self.terug.clicked.connect(lambda: self.blader(-1))
        self.verder = QPushButton("▶")
        self.verder.clicked.connect(lambda: self.blader(1))
        self.teller = QLabel("")
        self.teller.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.k_dubbel = QPushButton(T("b_dubbel"))
        self.k_dubbel.setCheckable(True)
        self.k_dubbel.setStyleSheet("QPushButton { font-size: 22px; padding: 10px 16px; min-width: 260px; } "
                                    "QPushButton:checked { background: #7F77DD; color: #16131f; border-color: #ffd166; }")
        self.k_dubbel.toggled.connect(self._dubbel)
        self.k_sluit = QPushButton(T("b_sluit"))
        self.k_sluit.setStyleSheet("font-size: 22px; background: #7a3b4e; border-color: #c25a74;")
        self.k_sluit.clicked.connect(self.close)
        onder.addWidget(self.terug)
        onder.addWidget(self.k_dubbel)
        onder.addWidget(self.teller, 1)
        onder.addWidget(self.k_sluit)
        onder.addWidget(self.verder)
        self.kruis = QPushButton("✕", self)
        self.kruis.setToolTip(T("b_sluit"))
        self.kruis.setFixedSize(76, 76)
        self.kruis.setStyleSheet("font-size: 40px; padding: 0; background: #7a3b4e; border: 3px solid #ffd166; border-radius: 38px;")
        self.kruis.clicked.connect(self.close)
        v.addLayout(onder)
        hulp = QLabel(T("blader_hulp"))
        hulp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(hulp)
        self.showFullScreen() if not os.environ.get("QT_QPA_PLATFORM") == "offscreen" else self.resize(1400, 900)
        self._teller()

    def _beeld(self, i):
        if not (0 <= i < len(self.h.boek["paginas"])):
            return None
        hoog = max(200, self.height() - 150)
        sleutel = (i, hoog)
        if sleutel not in self.cache:
            self.cache[sleutel] = QPixmap.fromImage(self.h._render(self.h.boek["paginas"][i], int(hoog * PB / PH)))
        return self.cache[sleutel]

    def _spread(self, i):
        """Welke bladzijden staan er nu in beeld? Bij twee naast elkaar staat de voorkant alleen."""
        if not self.dubbel:
            return [i]
        if i == 0:
            return [0]
        links = i if i % 2 == 1 else i - 1
        return [x for x in (links, links + 1) if x < len(self.h.boek["paginas"])]

    def blader(self, d):
        n = len(self.h.boek["paginas"])
        if not self.dubbel:
            nieuw = self.i + d
        else:
            s0 = self._spread(self.i)[0]
            nieuw = (1 if s0 == 0 else s0 + 2) if d > 0 else (0 if s0 <= 1 else s0 - 2)
        nieuw = max(0, min(n - 1, nieuw))
        if nieuw == self.i:
            return
        self.richting = 1 if nieuw > self.i else -1
        self.i = nieuw
        self.anim.stop()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()
        self._teller()

    def _teller(self):
        n = len(self.h.boek["paginas"])
        zicht = self._spread(self.i)
        self.teller.setText(" - ".join(str(x + 1) for x in zicht) + "  /  %d" % n)
        self.terug.setEnabled(zicht[0] > 0)
        self.verder.setEnabled(zicht[-1] < n - 1)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0d0b14"))
        zicht = self._spread(self.i)
        beelden = [self._beeld(x) for x in zicht]
        beelden = [b for b in beelden if b is not None]
        if not beelden:
            return
        totaal = sum(b.width() for b in beelden) + 8 * (len(beelden) - 1)
        x = (self.width() - totaal) / 2
        verschuif = self.anim.currentValue() if self.anim.state() == QVariantAnimation.State.Running else 0.0
        x += (verschuif or 0.0) * self.richting * self.width() * 0.25
        p.setOpacity(1.0 - 0.6 * (verschuif or 0.0))
        for b in beelden:
            p.fillRect(int(x) + 10, 22, b.width(), b.height(), QColor(0, 0, 0, 140))
            p.drawPixmap(int(x), 12, b)
            x += b.width() + 8

    def resizeEvent(self, e):
        self.cache = {}
        if hasattr(self, "kruis"):
            self.kruis.move(self.width() - self.kruis.width() - 20, 20)
            self.kruis.raise_()
        super().resizeEvent(e)

    def _dubbel(self, aan):
        self.dubbel = aan
        self._teller()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key.Key_Right, Qt.Key.Key_PageDown, Qt.Key.Key_Down):
            self.blader(1)
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_PageUp, Qt.Key.Key_Up):
            self.blader(-1)
        elif k == Qt.Key.Key_Space:
            self.k_dubbel.setChecked(not self.k_dubbel.isChecked())
        elif k == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def wheelEvent(self, e):
        self.blader(1 if e.angleDelta().y() < 0 else -1)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() < self.height() - 120:
            self.blader(1 if e.position().x() > self.width() / 2 else -1)


# ------------------------------------------------------------------ het hoofdvenster
def stijl(f=1.0):
    q = lambda n: "%dpx" % round(n * f)
    return """
* { font-family: 'Segoe UI', Arial; font-size: %(n)s; color: #efeaff; }
QMainWindow, QDialog, QWidget#wortel { background: #16131f; }
QLabel#titel { font-size: %(t)s; font-weight: 800; color: #b59cff; }
QLabel#kop { font-size: %(k)s; font-weight: 700; color: #ffd166; margin-top: 8px; }
QLabel#sub { color: #b9b2d6; font-size: %(s)s; }
QPushButton { background: #221c33; border: 2px solid #4a3d66; border-radius: 10px; padding: 8px 14px; }
QPushButton:hover { border-color: #b59cff; }
QPushButton:checked { background: #7F77DD; color: #16131f; border-color: #ffd166; font-weight: 700; }
QPushButton:disabled { color: #6b6488; border-color: #2e2745; }
QPushButton#paars { background: #7F77DD; color: #16131f; font-weight: 700; }
QPushButton#paars:disabled { background: #2e2745; color: #6b6488; }
QListWidget { background: #1d1829; border: 2px solid #4a3d66; border-radius: 10px; padding: 6px; }
QListWidget::item { padding: 6px; border-radius: 8px; }
QListWidget::item:selected { background: #3a2f5a; border: 2px solid #ffd166; }
QSpinBox { background: #221c33; border: 2px solid #4a3d66; border-radius: 8px; padding: 6px; min-width: 70px; }
QDoubleSpinBox, QLineEdit, QComboBox { background: #221c33; border: 2px solid #4a3d66; border-radius: 8px; padding: 6px; min-width: 70px; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border-color: #ffd166; }
QComboBox QAbstractItemView { background: #221c33; selection-background-color: #7F77DD; }
QSlider::groove:horizontal { height: 10px; background: #2e2745; border-radius: 5px; }
QSlider::handle:horizontal { width: 26px; margin: -9px 0; background: #ffd166; border-radius: 13px; }
QScrollArea, QScrollArea > QWidget > QWidget { border: none; background: #16131f; }
QStatusBar { color: #b9b2d6; }
QTabWidget::pane { border: 2px solid #4a3d66; border-radius: 10px; top: -2px; background: #16131f; }
QTabBar::tab { background: #221c33; padding: 10px 6px; margin-right: 3px; border: 2px solid #4a3d66;
               border-bottom: none; border-top-left-radius: 10px; border-top-right-radius: 10px; font-weight: 700; }
QTabBar::tab:selected { background: #7F77DD; color: #16131f; }
QCheckBox { spacing: 10px; }
QCheckBox::indicator { width: 24px; height: 24px; }
QPushButton#staal { border: 3px solid #4a3d66; border-radius: 8px; min-width: 34px; min-height: 34px; padding: 0; }
QPushButton#staal:checked { border: 4px solid #ffd166; }
""" % dict(n=q(16), t=q(26), k=q(17), s=q(14))


class Hoofd(QMainWindow):
    def __init__(self):
        super().__init__()
        self.instel = self._lees()
        self.f = self.instel.get("groot", 1.0)
        self.setWindowTitle(APP)
        ico = _res("assets", "icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))
        bl.laad_letters(_res("assets", "fonts"))
        bl.BEELD = lambda bid: self.beelden.beeld(bid)
        self.beelden = Beelden()
        self.boek = nieuw_boek()
        for pg in self.boek["paginas"]:
            zorg_lagen(pg, self.beelden)
        self.nu = 0
        self.pad = None
        self.gs = tk.Gereedschap()
        self.laag_i = 0                         # gekozen laag op deze bladzijde
        self.ach_doel, self.ach_i = "vak", 0    # achtergrond: voor het gekozen vakje of de hele bladzijde
        self.terug, self.vooruit = [], []
        self.json_nu = self._staat()
        self.pix_teller = self.bewaard_pix = 0
        self.bewaard_staat = self._staat()
        self._bouw()
        self.resize(1500, 950)
        self.setStyleSheet(stijl(self.f))
        self._later = QTimer(self)
        self._later.setSingleShot(True)
        self._later.timeout.connect(self.na_wijziging)
        self.ververs_alles()

    # ---------------------------------------------------------- instellingen
    def _lees(self):
        try:
            with open(INSTEL, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _bewaar_instel(self):
        try:
            with open(INSTEL, "w", encoding="utf-8") as f:
                json.dump(self.instel, f, ensure_ascii=False, indent=1)
        except Exception as e:
            _log("instellingen: %s" % e)

    # ---------------------------------------------------------- opbouw
    def _bouw(self):
        wortel = QWidget()
        wortel.setObjectName("wortel")
        self.setCentralWidget(wortel)
        v = QVBoxLayout(wortel)
        v.setContentsMargins(14, 10, 14, 6)
        kop = QHBoxLayout()
        logo = QLabel()
        pm = QPixmap(_res("assets", "icon.png"))
        if not pm.isNull():
            logo.setPixmap(pm.scaledToHeight(52, Qt.TransformationMode.SmoothTransformation))
        kop.addWidget(logo)
        t = QLabel(APP)
        t.setObjectName("titel")
        kop.addWidget(t)
        kop.addSpacing(16)
        for tekst, fn in ((T("nieuw"), self.nieuw), (T("open"), self.openen), (T("opslaan"), self.opslaan),
                          (T("opslaan_als"), self.opslaan_als), (T("png"), self.als_png), (T("pdf"), self.als_pdf),
                          (T("bladeren"), self.bladeren), (T("drukker"), self.drukklaar), (T("planner"), self.planner)):
            b = QPushButton(tekst)
            b.clicked.connect(fn)
            kop.addWidget(b)
        kop.addSpacing(10)
        self.k_terug = QPushButton(T("ongedaan"))
        self.k_terug.clicked.connect(self.ongedaan)
        self.k_vooruit = QPushButton(T("opnieuw"))
        self.k_vooruit.clicked.connect(self.opnieuw)
        kop.addWidget(self.k_terug)
        kop.addWidget(self.k_vooruit)
        kop.addStretch(1)
        for tekst, d in ((T("a_klein"), -0.1), (T("a_groot"), 0.1)):
            b = QPushButton(tekst)
            b.clicked.connect(lambda _=False, d=d: self.letter(d))
            kop.addWidget(b)
        b = QPushButton(T("snelgids"))
        b.clicked.connect(self.snelgids)
        kop.addWidget(b)
        b = QPushButton(T("over"))
        b.clicked.connect(lambda: QMessageBox.information(self, APP, T("over_tekst") % VERSIE))
        kop.addWidget(b)
        v.addLayout(kop)

        midden = QHBoxLayout()
        midden.setSpacing(12)
        # links: de bladzijden
        links = QVBoxLayout()
        lk = QLabel(T("pagina"))
        lk.setObjectName("kop")
        links.addWidget(lk)
        self.lijst = QListWidget()
        self.lijst.setViewMode(QListView.ViewMode.ListMode)
        self.lijst.setIconSize(QSize(96, 136))
        self.lijst.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lijst.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lijst.model().rowsMoved.connect(lambda *a: QTimer.singleShot(0, self._pagina_versleept))
        self.lijst.setToolTip(T("sleep_hint"))
        self.lijst.setSpacing(6)
        self.lijst.setFixedWidth(210)
        self.lijst.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lijst.currentRowChanged.connect(self.kies_pagina)
        links.addWidget(self.lijst, 1)
        r1 = QHBoxLayout()
        for tekst, fn in ((T("p_bij"), self.pagina_bij), (T("p_weg"), self.pagina_weg)):
            b = QPushButton(tekst)
            b.clicked.connect(fn)
            r1.addWidget(b)
        links.addLayout(r1)
        r2 = QHBoxLayout()
        for tekst, d in ((T("p_op"), -1), (T("p_neer"), 1)):
            b = QPushButton(tekst)
            b.clicked.connect(lambda _=False, d=d: self.pagina_schuif(d))
            r2.addWidget(b)
        links.addLayout(r2)
        r4 = QHBoxLayout()
        for tekst, fn in ((T("kaft_voor"), lambda: self.kaft("voor")), (T("kaft_achter"), lambda: self.kaft("achter"))):
            b = QPushButton(tekst)
            b.setStyleSheet("padding: 8px 4px;")
            b.clicked.connect(fn)
            r4.addWidget(b)
        links.addLayout(r4)
        midden.addLayout(links)
        # midden: het vlak
        self.vlak = Vlak(self)
        self.vlak.veranderd.connect(self.na_wijziging)
        self.vlak.gekozen_ander.connect(self.knoppen_bij)
        midden.addWidget(self.vlak, 1)
        # rechts: de knoppen
        rechts_w = QWidget()
        rechts_w.setObjectName("wortel")
        rechts = QVBoxLayout(rechts_w)
        rechts.setContentsMargins(0, 0, 6, 0)
        k = QLabel(T("indeling"))
        k.setObjectName("kop")
        k.setWordWrap(True)
        rechts.addWidget(k)
        g = QGridLayout()
        for i, soort in enumerate((1, 2, 3, 4, 6, "strip")):
            b = QPushButton(str(soort) if soort != "strip" else T("strip"))
            b.setMinimumHeight(44)
            b.clicked.connect(lambda _=False, s=soort: self.zet_indeling(s))
            if soort == "strip":
                g.addWidget(b, 2, 0, 1, 3)
            else:
                g.addWidget(b, i // 3, i % 3)
        rechts.addLayout(g)
        rr = QHBoxLayout()
        rr.addWidget(QLabel(T("ruimte")))
        self.ruimte = QSpinBox()
        self.ruimte.setRange(0, 80)
        self.ruimte.setSingleStep(5)
        self.ruimte.setValue(20)
        rr.addWidget(self.ruimte)
        rechts.addLayout(rr)
        self.k_teken = QPushButton(T("tekenvak"))
        self.k_teken.setCheckable(True)
        self.k_teken.toggled.connect(self._teken_modus)
        rechts.addWidget(self.k_teken)
        k = QLabel(T("modus"))
        k.setObjectName("kop")
        rechts.addWidget(k)
        self.k_mvak = QPushButton(T("m_vak"))
        self.k_mplaat = QPushButton(T("m_plaat"))
        grp = QButtonGroup(self)
        for b, m in ((self.k_mvak, "vak"), (self.k_mplaat, "plaat")):
            b.setCheckable(True)
            grp.addButton(b)
            b.clicked.connect(lambda _=False, m=m: self.zet_modus(m))
            rechts.addWidget(b)
        self.k_mvak.setChecked(True)
        k = QLabel(T("vakje"))
        k.setObjectName("kop")
        rechts.addWidget(k)
        self.geen = QLabel(T("geen_vak"))
        self.geen.setObjectName("sub")
        self.geen.setWordWrap(True)
        rechts.addWidget(self.geen)
        self.k_plaat = QPushButton(T("plaat_in"))
        self.k_plaat.setObjectName("paars")
        self.k_plaat.clicked.connect(self.plaatje_invoegen)
        rechts.addWidget(self.k_plaat)
        r3 = QHBoxLayout()
        self.k_passend = QPushButton(T("passend"))
        self.k_passend.clicked.connect(self.plaatje_passend)
        self.k_plaatweg = QPushButton(T("plaat_weg"))
        self.k_plaatweg.clicked.connect(self.plaatje_weg)
        r3.addWidget(self.k_passend)
        r3.addWidget(self.k_plaatweg)
        rechts.addLayout(r3)
        rz = QHBoxLayout()
        rz.addWidget(QLabel(T("zoom")))
        self.zoom = QSlider(Qt.Orientation.Horizontal)
        self.zoom.setRange(20, 600)
        self.zoom.valueChanged.connect(self._zoom_schuif)
        self.zoom.sliderReleased.connect(self.na_wijziging)
        rz.addWidget(self.zoom, 1)
        rechts.addLayout(rz)
        rd = QHBoxLayout()
        rd.addWidget(QLabel(T("rand")))
        self.rand = QSpinBox()
        self.rand.setRange(0, 20)
        self.rand.valueChanged.connect(self._rand)
        rd.addWidget(self.rand)
        rechts.addLayout(rd)
        self.k_vakweg = QPushButton(T("vak_weg"))
        self.k_vakweg.clicked.connect(self.vak_weg)
        rechts.addWidget(self.k_vakweg)
        hint = QLabel(T("hint"))
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        rechts.addWidget(hint)
        rechts.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(rechts_w)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabs_r = QTabWidget()
        self.tabs_r.setFixedWidth(590)
        self.tabs_r.addTab(sc, T("tab_vak"))
        self.tabs_r.addTab(self._bouw_tekenen(), T("tab_teken"))
        self.tabs_r.addTab(self._bouw_tekst(), T("tab_tekst"))
        self.tabs_r.addTab(self._bouw_achter(), T("tab_ach"))
        self.tabs_r.addTab(self._bouw_figuren(), T("tab_fig"))
        self.tabs_r.currentChanged.connect(self._tab_wissel)
        midden.addWidget(self.tabs_r)
        v.addLayout(midden, 1)
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.ongedaan)
        QShortcut(QKeySequence.StandardKey.Redo, self, activated=self.opnieuw)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.opnieuw)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=self.opslaan)
        QShortcut(QKeySequence.StandardKey.Open, self, activated=self.openen)

    def _bouw_tekenen(self):
        w = QWidget()
        w.setObjectName("wortel")
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 8, 4)
        self.gereed = {}
        grp = QButtonGroup(self)
        for kop, lijst in ((T("gereedschap"), ("pen", "potlood", "penseel", "gum", "emmer", "pipet")),
                           (T("vormen"), ("lijn", "rechthoek", "cirkel", "pijl", "snelheid"))):
            k = QLabel(kop)
            k.setObjectName("kop")
            v.addWidget(k)
            g = QGridLayout()
            for i, soort in enumerate(lijst):
                b = QPushButton(T("g_" + soort))
                b.setCheckable(True)
                b.setMinimumHeight(42)
                grp.addButton(b)
                b.clicked.connect(lambda _=False, s=soort: self.kies_gereedschap(s))
                g.addWidget(b, i // 2, i % 2)
                self.gereed[soort] = b
            v.addLayout(g)
        self.gereed["pen"].setChecked(True)
        self.k_gevuld = QCheckBox(T("gevuld"))
        self.k_gevuld.toggled.connect(lambda a: setattr(self.gs, "gevuld", a))
        v.addWidget(self.k_gevuld)
        k = QLabel(T("kleur"))
        k.setObjectName("kop")
        v.addWidget(k)
        g = QGridLayout()
        g.setSpacing(6)
        self.stalen = []
        for i, kl in enumerate(("#111111", "#ffffff", "#7a7a7a", "#e23b3b", "#ff8c1a", "#ffd166", "#3cb54a",
                                "#2d7ff9", "#7F77DD", "#a0522d", "#f2c6a0", "#ff6fb5")):
            b = QPushButton("")
            b.setObjectName("staal")
            b.setCheckable(True)
            b.setStyleSheet("QPushButton#staal { background: %s; }" % kl)
            b.clicked.connect(lambda _=False, k=kl: self.zet_kleur(QColor(k)))
            g.addWidget(b, i // 6, i % 6)
            self.stalen.append((kl, b))
        v.addLayout(g)
        rk = QHBoxLayout()
        self.kleurvak = QPushButton("")
        self.kleurvak.setObjectName("staal")
        self.kleurvak.setFixedSize(54, 40)
        rk.addWidget(self.kleurvak)
        b = QPushButton(T("andere_kleur"))
        b.clicked.connect(self._kies_kleur)
        self.kleurvak.clicked.connect(self._kies_kleur)
        rk.addWidget(b, 1)
        v.addLayout(rk)
        rd = QHBoxLayout()
        rd.addWidget(QLabel(T("dikte")))
        self.dikte = QSlider(Qt.Orientation.Horizontal)
        self.dikte.setRange(1, 60)
        self.dikte.valueChanged.connect(lambda w: self.zet_dikte(w, schuif=False))
        rd.addWidget(self.dikte, 1)
        self.dikte_l = QLabel("")
        self.dikte_l.setMinimumWidth(34)
        rd.addWidget(self.dikte_l)
        v.addLayout(rd)
        self.k_binnen = QCheckBox(T("binnen"))
        self.k_binnen.setChecked(True)
        self.k_binnen.toggled.connect(lambda a: setattr(self.gs, "binnen", a))
        v.addWidget(self.k_binnen)
        k = QLabel(T("lagen"))
        k.setObjectName("kop")
        k.setWordWrap(True)
        v.addWidget(k)
        self.lagenlijst = QListWidget()
        self.lagenlijst.setMinimumHeight(130)
        self.lagenlijst.currentRowChanged.connect(self._kies_laag)
        self.lagenlijst.itemChanged.connect(self._laag_vinkje)
        self.lagenlijst.itemDoubleClicked.connect(self._laag_naam)
        v.addWidget(self.lagenlijst)
        rl = QHBoxLayout()
        for tekst, fn in ((T("l_bij"), self.laag_bij), (T("l_weg"), self.laag_weg)):
            b = QPushButton(tekst)
            b.clicked.connect(fn)
            rl.addWidget(b)
        for tekst, d in (("▲", 1), ("▼", -1)):
            b = QPushButton(tekst)
            b.clicked.connect(lambda _=False, d=d: self.laag_schuif(d))
            rl.addWidget(b)
        v.addLayout(rl)
        self.k_achter = QCheckBox(T("a_achter"))
        self.k_achter.toggled.connect(self._laag_achter)
        v.addWidget(self.k_achter)
        ro = QHBoxLayout()
        ro.addWidget(QLabel(T("dekking")))
        self.dekking = QSlider(Qt.Orientation.Horizontal)
        self.dekking.setRange(5, 100)
        self.dekking.valueChanged.connect(self._dekking)
        ro.addWidget(self.dekking, 1)
        v.addLayout(ro)
        hint = QLabel(T("teken_hint"))
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        v.addWidget(hint)
        v.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.zet_kleur(self.gs.kleur)
        self.dikte.setValue(int(self.gs.dikte))
        return sc

    def _bouw_tekst(self):
        w = QWidget()
        w.setObjectName("wortel")
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 8, 4)
        k = QLabel(T("t_nieuw"))
        k.setObjectName("kop")
        v.addWidget(k)
        g = QGridLayout()
        for i, soort in enumerate(bl.SOORTEN):
            b = QPushButton(T("t_" + soort))
            b.setMinimumHeight(44)
            b.clicked.connect(lambda _=False, s=soort: self.tekst_bij_zetten(s))
            g.addWidget(b, i // 2, i % 2)
        v.addLayout(g)
        k = QLabel(T("t_gekozen"))
        k.setObjectName("kop")
        v.addWidget(k)
        self.t_geen = QLabel(T("t_geen"))
        self.t_geen.setObjectName("sub")
        self.t_geen.setWordWrap(True)
        v.addWidget(self.t_geen)
        self.t_tekst = QPlainTextEdit()
        self.t_tekst.setFixedHeight(96)
        self.t_tekst.setStyleSheet("QPlainTextEdit { background: #ffffff; color: #111111; border: 3px solid #ffd166; "
                                   "border-radius: 8px; font-size: 20px; padding: 4px; }")
        self.t_tekst.textChanged.connect(self._t_tekst)
        v.addWidget(self.t_tekst)
        self.t_woorden_k = QLabel(T("t_woorden"))
        self.t_woorden_k.setObjectName("sub")
        v.addWidget(self.t_woorden_k)
        self.t_woorden = QWidget()
        gw = QGridLayout(self.t_woorden)
        gw.setContentsMargins(0, 0, 0, 0)
        woorden = ("BAM!", "POW!", "BOEM!", "ZAP!", "KRAK!", "WHAM!", "PLONS!", "ZOEF!") if NL else             ("BAM!", "POW!", "BOOM!", "ZAP!", "CRACK!", "WHAM!", "SPLASH!", "WHOOSH!")
        for i, wd in enumerate(woorden):
            b = QPushButton(wd)
            b.clicked.connect(lambda _=False, x=wd: self.t_tekst.setPlainText(x))
            b.setStyleSheet("padding: 6px 4px;")
            gw.addWidget(b, i // 3, i % 3)
        v.addWidget(self.t_woorden)
        rf = QHBoxLayout()
        rf.addWidget(QLabel(T("t_lettertype")))
        self.t_font = QFontComboBox()
        self.t_font.setMinimumHeight(40)
        self.t_font.setSizeAdjustPolicy(QFontComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.t_font.setMinimumContentsLength(10)
        self.t_font.setMaximumWidth(250)
        self.t_font.setStyleSheet("QFontComboBox { background: #221c33; border: 2px solid #4a3d66; border-radius: 8px; padding: 4px; }")
        self.t_font.currentFontChanged.connect(lambda f: self._t_zet("letter", f.family()))
        rf.addWidget(self.t_font, 1)
        v.addLayout(rf)
        rb = QHBoxLayout()
        self.t_vet = QPushButton(T("t_vet"))
        self.t_vet.setCheckable(True)
        self.t_vet.setStyleSheet("font-weight: 900;")
        self.t_vet.toggled.connect(lambda a: self._t_zet("vet", a))
        self.t_schuin = QPushButton(T("t_schuin"))
        self.t_schuin.setCheckable(True)
        self.t_schuin.setStyleSheet("font-style: italic;")
        self.t_schuin.toggled.connect(lambda a: self._t_zet("schuin", a))
        self.t_stripk = QPushButton(T("t_strip"))
        self.t_stripk.setToolTip("Terug naar de stripletter van DraveComic" if NL else "Back to DraveComic's comic font")
        self.t_stripk.clicked.connect(self._t_stripletter)
        rb.addWidget(self.t_vet)
        rb.addWidget(self.t_schuin)
        rb.addWidget(self.t_stripk)
        v.addLayout(rb)
        self.t_rij_grootte = QWidget()
        rg = QHBoxLayout(self.t_rij_grootte)
        rg.setContentsMargins(0, 0, 0, 0)
        rg.addWidget(QLabel(T("t_grootte")))
        self.t_grootte = QSpinBox()
        self.t_grootte.setRange(10, 120)
        self.t_grootte.valueChanged.connect(lambda x: self._t_zet("grootte", x))
        rg.addWidget(self.t_grootte)
        v.addWidget(self.t_rij_grootte)
        rk = QHBoxLayout()
        self.t_letter = QPushButton(T("t_letter"))
        self.t_letter.clicked.connect(lambda: self._t_kleur("kleur"))
        self.t_vulling = QPushButton(T("t_vulling"))
        self.t_vulling.clicked.connect(lambda: self._t_kleur("vulling"))
        rk.addWidget(self.t_letter)
        rk.addWidget(self.t_vulling)
        v.addLayout(rk)
        self.t_rij_draai = QWidget()
        rd = QHBoxLayout(self.t_rij_draai)
        rd.setContentsMargins(0, 0, 0, 0)
        rd.addWidget(QLabel(T("t_draai")))
        self.t_draai = QSlider(Qt.Orientation.Horizontal)
        self.t_draai.setRange(-45, 45)
        self.t_draai.valueChanged.connect(lambda x: self._t_zet("draai", x))
        rd.addWidget(self.t_draai, 1)
        v.addWidget(self.t_rij_draai)
        self.t_ster = QCheckBox(T("t_ster"))
        self.t_ster.toggled.connect(lambda a: self._t_zet("ster", a))
        v.addWidget(self.t_ster)
        self.t_staart = QCheckBox(T("t_staart"))
        self.t_staart.toggled.connect(self._t_staart)
        v.addWidget(self.t_staart)
        rv = QHBoxLayout()
        self.t_voor = QPushButton(T("t_voor"))
        self.t_voor.clicked.connect(lambda: self._t_volgorde(1))
        self.t_achter = QPushButton(T("t_achter"))
        self.t_achter.clicked.connect(lambda: self._t_volgorde(-1))
        rv.addWidget(self.t_voor)
        rv.addWidget(self.t_achter)
        v.addLayout(rv)
        self.t_wegk = QPushButton(T("t_weg"))
        self.t_wegk.clicked.connect(self.tekst_weg)
        v.addWidget(self.t_wegk)
        hint = QLabel(T("t_hint"))
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        v.addWidget(hint)
        v.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return sc

    # ---------------------------------------------------------- teksten
    def tekst_bij_zetten(self, soort):
        ts = self.vlak._teksten()
        n = len(ts)
        t = bl.nieuw(soort, 500 + (n % 4) * 30, 420 + (n % 4) * 40)
        ts.append(t)
        self.vlak.tgekozen = len(ts) - 1
        self.tekst_bij()
        self.vlak.update()
        self.na_wijziging()
        self.t_tekst.setFocus()
        self.t_tekst.selectAll()

    def tekst_bij(self):
        t = self.vlak._tekst() if hasattr(self, "vlak") else None
        heeft = t is not None
        self.t_geen.setVisible(not heeft)
        for x in (self.t_tekst, self.t_letter, self.t_vulling, self.t_voor, self.t_achter, self.t_wegk,
                  self.t_font, self.t_vet, self.t_schuin, self.t_stripk):
            x.setEnabled(heeft)
        if heeft and t["soort"] == "figuur":
            for x in (self.t_tekst, self.t_letter, self.t_vulling, self.t_font, self.t_vet, self.t_schuin, self.t_stripk):
                x.setEnabled(False)
        geluid = heeft and t["soort"] == "geluid"
        ballon = heeft and t["soort"] in ("praat", "denk", "schreeuw")
        self.t_woorden.setVisible(geluid)
        self.t_woorden_k.setVisible(geluid)
        self.t_rij_draai.setVisible(geluid)
        self.t_ster.setVisible(geluid)
        self.t_rij_grootte.setVisible(heeft and not geluid)
        self.t_staart.setVisible(ballon)
        for x, waarde in ((self.t_tekst, None), (self.t_grootte, "grootte"), (self.t_draai, "draai"),
                          (self.t_ster, "ster"), (self.t_staart, None)):
            x.blockSignals(True)
        self.t_tekst.setPlainText(t.get("tekst", "") if heeft else "")
        if heeft:
            self.t_grootte.setValue(int(t.get("grootte", 30) or 30))
            self.t_draai.setValue(int(t.get("draai", 0)))
            self.t_ster.setChecked(bool(t.get("ster", True)))
            self.t_staart.setChecked(bool(t.get("staart")))
            self.t_letter.setStyleSheet("border-bottom: 6px solid %s;" % t.get("kleur", "#111111"))
            self.t_vulling.setStyleSheet("border-bottom: 6px solid %s;" % t.get("vulling", "#ffffff"))
        for x in (self.t_font, self.t_vet, self.t_schuin):
            x.blockSignals(True)
        if heeft:
            fam, vet, schuin = bl.letter_van(t)
            self.t_font.setCurrentFont(QFont(fam))
            self.t_vet.setChecked(vet)
            self.t_schuin.setChecked(schuin)
        for x in (self.t_tekst, self.t_grootte, self.t_draai, self.t_ster, self.t_staart, self.t_font, self.t_vet,
                  self.t_schuin):
            x.blockSignals(False)
        if hasattr(self, "f_weg"):
            self.fig_bij()

    def _t_tekst(self):
        t = self.vlak._tekst()
        if t is not None:
            t["tekst"] = self.t_tekst.toPlainText()
            self.vlak.update()
            self.later_veranderd()

    def _t_zet(self, sleutel, waarde):
        t = self.vlak._tekst()
        if t is not None:
            t[sleutel] = waarde
            self.vlak.update()
            self.later_veranderd()

    def _t_stripletter(self):
        t = self.vlak._tekst()
        if t is not None:
            for k in ("letter", "vet", "schuin"):
                t.pop(k, None)
            self.tekst_bij()
            self.vlak.update()
            self.na_wijziging()

    def _t_kleur(self, sleutel):
        t = self.vlak._tekst()
        if t is None:
            return
        k = QColorDialog.getColor(QColor(t.get(sleutel, "#ffffff")), self, T("t_letter" if sleutel == "kleur" else "t_vulling"))
        if k.isValid():
            t[sleutel] = k.name()
            self.tekst_bij()
            self.vlak.update()
            self.na_wijziging()

    def _t_staart(self, aan):
        t = self.vlak._tekst()
        if t is None:
            return
        if aan and not t.get("staart"):
            t["staart"] = [t["x"] + t["w"] / 2 + 40, t["y"] + t["h"] + 120]
        elif not aan:
            t["staart"] = None
        self.vlak.update()
        self.na_wijziging()

    def _t_volgorde(self, d):
        ts, i = self.vlak._teksten(), self.vlak.tgekozen
        if i is None:
            return
        j = len(ts) - 1 if d > 0 else 0
        ts.insert(j, ts.pop(i))
        self.vlak.tgekozen = j
        self.vlak.update()
        self.na_wijziging()

    def tekst_weg(self):
        ts, i = self.vlak._teksten(), self.vlak.tgekozen
        if i is None or not (0 <= i < len(ts)):
            return
        del ts[i]
        self.vlak.tgekozen = None
        self.tekst_bij()
        self.vlak.update()
        self.na_wijziging()


    # ---------------------------------------------------------- 0.6.0: klaar voor de drukker
    def drukklaar(self):
        ps = self.boek["paginas"]
        binnen = [pg for pg in ps if pg.get("soort") not in ("voor", "achter")]
        voor = next((pg for pg in ps if pg.get("soort") == "voor"), None)
        achter = next((pg for pg in ps if pg.get("soort") == "achter"), None)
        if not binnen:
            QMessageBox.information(self, APP, T("druk_leeg"))
            return
        titel = self.boek.get("titel") or "strip"
        d = dk.DrukDialoog(self, NL, len(binnen), voor is not None, achter is not None, titel, self.instel)
        d.setStyleSheet(stijl(self.f))
        if d.exec() != QDialog.DialogCode.Accepted:
            return
        w = d.waarden()
        self.instel.update(druk_formaat=w["formaat"], druk_afloop=w["afloop"], druk_vel=w["vel"], druk_aanvul=w["aanvul"],
                           druk_tekens=w["tekens"], druk_rugkleur=w["rugkleur"], druk_rugtekst=bool(w["rugtekst"]))
        self._bewaar_instel()
        map_ = QFileDialog.getExistingDirectory(self, T("druk_map"), self.instel.get("laatste_map") or MIJN)
        if not map_:
            return
        teken = lambda p, pg, sch: teken_pagina(p, pg, self.beelden, sch)
        maker = "%s %s - Dravenlock" % (APP, VERSIE)
        p1 = os.path.join(map_, "%s - %s.pdf" % (titel, T("druk_binnen")))
        p2 = os.path.join(map_, "%s - %s.pdf" % (titel, T("druk_kaft")))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            n = dk.maak_binnenwerk(p1, binnen, teken, PB, PH, w["breed"], w["hoog"], w["afloop"], w["tekens"], w["aanvul"],
                                   titel, maker)
            kb, kh = dk.maak_kaft(p2, voor, achter, teken, PB, PH, w["breed"], w["hoog"], w["afloop"], w["rug"], w["tekens"],
                                  w["rugkleur"], w["rugtekst"], titel, maker)
        except Exception as e:
            _log("drukklaar: %s" % traceback.format_exc())
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, APP, T("druk_fout") % e)
            return
        QApplication.restoreOverrideCursor()
        if QMessageBox.question(self, APP, T("druk_klaar") % (n, w["rug"], kb, kh, p1, p2)) == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(map_))

    # ---------------------------------------------------------- 0.6.0: verhaal-planner
    def planner(self):
        d = pl.Planner(self, NL, self.boek.get("plan"))
        d.setStyleSheet(stijl(self.f))
        if d.exec() != QDialog.DialogCode.Accepted:
            return
        plan = d.resultaat()
        self.boek["plan"] = plan
        if not d.maken:
            self.na_wijziging()
            self.statusBar().showMessage(T("plan_bewaard"), 6000)
            return
        if QMessageBox.question(self, APP, T("plan_vraag") % len(plan)) != QMessageBox.StandardButton.Yes:
            self.na_wijziging()
            return
        nieuwe = [self._plan_blad(b) for b in plan]
        ps = self.boek["paginas"]
        plek = next((i for i, pg in enumerate(ps) if pg.get("soort") == "achter"), len(ps))
        ps[plek:plek] = nieuwe
        self.nu = plek
        self.vlak.gekozen = self.vlak.tgekozen = None
        self.ververs_alles()
        self.na_wijziging()
        self.statusBar().showMessage(T("plan_klaar") % len(nieuwe), 8000)

    def _plan_blad(self, b):
        pg = dict(vakjes=indeling(b["indeling"], self.ruimte.value()), teksten=[])
        zorg_lagen(pg, self.beelden)
        for v, plan in zip(pg["vakjes"], b["vakjes"]):
            if plan.get("wat"):
                v["plan"] = plan["wat"]
            y = v["y"] + 14
            regels = pl.regels_naar_teksten(plan.get("tekst", ""))
            regels = [r for r in regels if r[0] == "verteller"] + [r for r in regels if r[0] != "verteller"]
            for soort, tekst in regels:
                t = bl.nieuw(soort, v["x"] + v["w"] / 2, v["y"] + 80)
                w = min(v["w"] * (0.62 if soort == "praat" else 0.85), 420)
                h = min(110.0, max(70.0, v["h"] * 0.2))
                t.update(tekst=tekst, w=round(w), h=round(h))
                if soort == "praat":
                    t["x"] = round(v["x"] + (v["w"] - w) / 2)
                    t["y"] = round(y + h * 0.25)
                    t["staart"] = [t["x"] + w / 2 + 30, min(v["y"] + v["h"] - 20, t["y"] + h + 90)]
                    y = t["y"] + h * 1.3 + 10
                else:
                    t["x"] = round(v["x"] + 34)
                    t["y"] = round(y + 16)
                    y = t["y"] + h + 30
                if y > v["y"] + v["h"] - 40:
                    break
                pg["teksten"].append(t)
        return pg

    # ---------------------------------------------------------- 0.6.0: personage-kast
    def _bouw_figuren(self):
        w = QWidget()
        w.setObjectName("wortel")
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 8, 4)
        k = QLabel(T("f_kast"))
        k.setObjectName("kop")
        v.addWidget(k)
        u = QLabel(T("f_uitleg"))
        u.setObjectName("sub")
        u.setWordWrap(True)
        v.addWidget(u)
        self.kast = QListWidget()
        self.kast.setViewMode(QListView.ViewMode.IconMode)
        self.kast.setIconSize(QSize(110, 110))
        self.kast.setResizeMode(QListView.ResizeMode.Adjust)
        self.kast.setMovement(QListView.Movement.Static)
        self.kast.setSpacing(8)
        self.kast.setMinimumHeight(300)
        self.kast.itemDoubleClicked.connect(lambda _it: self.fig_plaats())
        v.addWidget(self.kast, 1)
        b = QPushButton(T("f_plaats"))
        b.setObjectName("paars")
        b.setMinimumHeight(48)
        b.clicked.connect(self.fig_plaats)
        v.addWidget(b)
        b = QPushButton(T("f_uit_tekening"))
        b.clicked.connect(self.fig_uit_tekening)
        v.addWidget(b)
        b = QPushButton(T("f_eigen"))
        b.clicked.connect(self.fig_eigen)
        v.addWidget(b)
        r = QHBoxLayout()
        b = QPushButton(T("f_naam"))
        b.clicked.connect(self.fig_hernoem)
        r.addWidget(b)
        b = QPushButton(T("f_uit_kast"))
        b.clicked.connect(self.fig_uit_kast)
        r.addWidget(b)
        v.addLayout(r)
        k = QLabel(T("f_gekozen"))
        k.setObjectName("kop")
        v.addWidget(k)
        self.f_geen = QLabel(T("f_geen"))
        self.f_geen.setObjectName("sub")
        self.f_geen.setWordWrap(True)
        v.addWidget(self.f_geen)
        r = QHBoxLayout()
        self.f_spiegel = QPushButton(T("f_spiegel"))
        self.f_spiegel.clicked.connect(self.fig_spiegel)
        r.addWidget(self.f_spiegel)
        self.f_voor = QPushButton(T("t_voor"))
        self.f_voor.clicked.connect(lambda: self._t_volgorde(1))
        r.addWidget(self.f_voor)
        self.f_achter = QPushButton(T("t_achter"))
        self.f_achter.clicked.connect(lambda: self._t_volgorde(-1))
        r.addWidget(self.f_achter)
        v.addLayout(r)
        self.f_weg = QPushButton(T("f_weg"))
        self.f_weg.clicked.connect(self.tekst_weg)
        v.addWidget(self.f_weg)
        hint = QLabel(T("f_hint"))
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        v.addWidget(hint)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.kast_bij()
        self.fig_bij()
        return sc

    def kast_bij(self, kies=None):
        self.kast.clear()
        for naam, pad in fg.lijst(DATA):
            it = QListWidgetItem(QIcon(QPixmap(pad)), naam)
            it.setData(Qt.ItemDataRole.UserRole, pad)
            self.kast.addItem(it)
            if kies and naam == kies:
                self.kast.setCurrentItem(it)
        if self.kast.currentItem() is None and self.kast.count():
            self.kast.setCurrentRow(0)

    def fig_bij(self):
        t = self.vlak._tekst() if hasattr(self, "vlak") else None
        fig = t is not None and t.get("soort") == "figuur"
        self.f_geen.setVisible(not fig)
        for x in (self.f_spiegel, self.f_voor, self.f_achter, self.f_weg):
            x.setEnabled(fig)

    def _kast_pad(self):
        it = self.kast.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def fig_plaats(self):
        pad = self._kast_pad()
        if not pad:
            QMessageBox.information(self, APP, T("f_kast_leeg"))
            return
        try:
            with open(pad, "rb") as f:
                data = f.read()
        except Exception as e:
            _log("figuur %s: %s" % (pad, e))
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        bid = self.beelden.voeg_bytes(data)
        if not bid:
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        im = self.beelden.beeld(bid)
        v = self._vak()
        doos = (v["x"], v["y"], v["w"], v["h"]) if v else (PB * 0.25, PH * 0.3, PB * 0.5, PH * 0.4)
        ts = self.vlak._teksten()
        ts.append(fg.nieuw_ding(bid, os.path.splitext(os.path.basename(pad))[0], im.width(), im.height(), doos))
        if self.tabs_r.currentIndex() not in (2, 4):
            self.tabs_r.setCurrentIndex(4)
        self.vlak.modus = "tekst"
        self.vlak.tgekozen = len(ts) - 1
        self.fig_bij()
        self.vlak.update()
        self.na_wijziging()

    def fig_uit_tekening(self):
        im, lid = self.huidige_laag()
        if im is None:
            QMessageBox.information(self, APP, T("laag_uit") if lid else T("f_geen_tekening"))
            return
        v = self._vak()
        if v:
            gebied = QRect(int(v["x"] * tk.LS), int(v["y"] * tk.LS), int(v["w"] * tk.LS), int(v["h"] * tk.LS))
        else:
            gebied = QRect(0, 0, tk.LB, tk.LH)
        gebied = gebied.intersected(QRect(0, 0, tk.LB, tk.LH))
        stuk, r = fg.bijgesneden(im.copy(gebied))
        if stuk is None:
            QMessageBox.information(self, APP, T("f_geen_tekening"))
            return
        naam, ok = QInputDialog.getText(self, T("f_kast"), T("f_naam_vraag"), text=T("f_standaard"))
        if not ok:
            return
        naam, _ = fg.bewaar(DATA, naam, stuk)
        self.kast_bij(kies=naam)
        if QMessageBox.question(self, APP, T("f_vervang") % naam) != QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage(T("f_bewaard") % naam, 6000)
            return
        # de tekening wordt een figuur: van de laag af, als verschuifbaar ding erop
        echt = r.translated(gebied.topLeft())
        voor = im.copy(echt)
        p = QPainter(im)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.fillRect(echt, Qt.GlobalColor.transparent)
        p.end()
        self.pixel_stap(lid, echt, voor, im.copy(echt))
        bid = self.beelden.voeg_bytes(fg.png_bytes(stuk))
        ts = self.vlak._teksten()
        ts.append(dict(soort="figuur", bid=bid, naam=naam, x=round(echt.x() / tk.LS), y=round(echt.y() / tk.LS),
                       w=round(echt.width() / tk.LS), h=round(echt.height() / tk.LS), spiegel=False, staart=None, tekst=""))
        self.tabs_r.setCurrentIndex(4)
        self.vlak.modus = "tekst"
        self.vlak.tgekozen = len(ts) - 1
        self.fig_bij()
        self.vlak.update()
        self.na_wijziging()
        self.statusBar().showMessage(T("f_bewaard") % naam, 6000)

    def fig_eigen(self):
        begin = self.instel.get("plaatjesmap") or os.path.expanduser("~")
        pad, _ = QFileDialog.getOpenFileName(self, T("kies_plaat"), begin, "%s (*.png *.webp *.jpg *.jpeg *.bmp)" % T("plaatjes"))
        if not pad:
            return
        im = QImage(pad)
        if im.isNull():
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        if im.width() > 1600 or im.height() > 1600:
            im = im.scaled(1600, 1600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        naam, ok = QInputDialog.getText(self, T("f_kast"), T("f_naam_vraag"), text=os.path.splitext(os.path.basename(pad))[0])
        if not ok:
            return
        naam, _ = fg.bewaar(DATA, naam, im)
        self.kast_bij(kies=naam)

    def fig_hernoem(self):
        pad = self._kast_pad()
        if not pad:
            return
        oud = os.path.splitext(os.path.basename(pad))[0]
        naam, ok = QInputDialog.getText(self, T("f_kast"), T("f_naam_vraag"), text=oud)
        if ok and naam.strip() and naam.strip() != oud:
            naam, _ = fg.hernoem(DATA, pad, naam)
            self.kast_bij(kies=naam)

    def fig_uit_kast(self):
        pad = self._kast_pad()
        if not pad:
            return
        naam = os.path.splitext(os.path.basename(pad))[0]
        if QMessageBox.question(self, APP, T("f_weg_vraag") % naam) == QMessageBox.StandardButton.Yes:
            try:
                os.remove(pad)
            except Exception as e:
                _log("kast weg: %s" % e)
            self.kast_bij()

    def fig_spiegel(self):
        t = self.vlak._tekst()
        if t is not None and t.get("soort") == "figuur":
            t["spiegel"] = not t.get("spiegel")
            self.vlak.update()
            self.na_wijziging()

    # ---------------------------------------------------------- achtergronden (stuk 5)
    def _bouw_achter(self):
        w = QWidget()
        w.setObjectName("wortel")
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 6, 8, 4)
        k = QLabel(T("a_voor"))
        k.setObjectName("kop")
        v.addWidget(k)
        rv = QHBoxLayout()
        self.a_k_vak, self.a_k_pag = QPushButton(T("a_vak")), QPushButton(T("a_pag"))
        grp = QButtonGroup(self)
        for b, d in ((self.a_k_vak, "vak"), (self.a_k_pag, "pagina")):
            b.setCheckable(True)
            b.setMinimumHeight(42)
            b.setStyleSheet("padding: 8px 6px;")
            grp.addButton(b)
            b.clicked.connect(lambda _=False, d=d: self.ach_doel_zet(d))
            rv.addWidget(b)
        self.a_k_vak.setChecked(True)
        v.addLayout(rv)
        self.a_geen = QLabel(T("geen_vak"))
        self.a_geen.setObjectName("sub")
        self.a_geen.setWordWrap(True)
        v.addWidget(self.a_geen)
        k = QLabel(T("a_lagen"))
        k.setObjectName("kop")
        k.setWordWrap(True)
        v.addWidget(k)
        self.a_lijst = QListWidget()
        self.a_lijst.setIconSize(QSize(60, 40))
        self.a_lijst.setMinimumHeight(150)
        self.a_lijst.currentRowChanged.connect(self._ach_kies)
        self.a_lijst.itemChanged.connect(self._ach_vinkje)
        v.addWidget(self.a_lijst)
        self.a_leeg = QLabel(T("a_leeg"))
        self.a_leeg.setObjectName("sub")
        self.a_leeg.setWordWrap(True)
        v.addWidget(self.a_leeg)
        rl = QHBoxLayout()
        for tekst, d in (("▲", 1), ("▼", -1)):
            b = QPushButton(tekst)
            b.clicked.connect(lambda _=False, d=d: self.ach_schuif(d))
            rl.addWidget(b)
        self.a_k_weg = QPushButton(T("a_weg"))
        self.a_k_weg.clicked.connect(self.ach_weg)
        rl.addWidget(self.a_k_weg, 1)
        v.addLayout(rl)
        k = QLabel(T("a_gekozen"))
        k.setObjectName("kop")
        v.addWidget(k)
        rk = QHBoxLayout()
        self.a_k1, self.a_k2 = QPushButton(""), QPushButton("")
        for b, s in ((self.a_k1, "k1"), (self.a_k2, "k2")):
            b.setMinimumHeight(40)
            b.clicked.connect(lambda _=False, s=s: self.ach_kleur(s))
            rk.addWidget(b)
        v.addLayout(rk)
        ra = QHBoxLayout()
        self.a_k_anders = QPushButton(T("a_anders"))
        self.a_k_anders.clicked.connect(self.ach_anders)
        self.a_k_spiegel = QPushButton(T("a_spiegel"))
        self.a_k_spiegel.setCheckable(True)
        self.a_k_spiegel.clicked.connect(self.ach_spiegel)
        ra.addWidget(self.a_k_anders)
        ra.addWidget(self.a_k_spiegel)
        v.addLayout(ra)
        ro = QHBoxLayout()
        ro.addWidget(QLabel(T("dekking")))
        self.a_dekking = QSlider(Qt.Orientation.Horizontal)
        self.a_dekking.setRange(5, 100)
        self.a_dekking.valueChanged.connect(self._ach_dekking)
        self.a_dekking.sliderReleased.connect(self.na_wijziging)
        ro.addWidget(self.a_dekking, 1)
        v.addLayout(ro)
        rz = QHBoxLayout()
        rz.addWidget(QLabel(T("zoom")))
        self.a_zoom = QSlider(Qt.Orientation.Horizontal)
        self.a_zoom.setRange(20, 600)
        self.a_zoom.valueChanged.connect(self._ach_zoom)
        self.a_zoom.sliderReleased.connect(self.na_wijziging)
        rz.addWidget(self.a_zoom, 1)
        self.a_k_passend = QPushButton(T("passend"))
        self.a_k_passend.clicked.connect(self.ach_passend)
        rz.addWidget(self.a_k_passend)
        v.addLayout(rz)
        self.a_k_alle = QPushButton(T("a_alle"))
        self.a_k_alle.clicked.connect(self.ach_alle)
        v.addWidget(self.a_k_alle)
        k = QLabel(T("a_toevoegen"))
        k.setObjectName("kop")
        v.addWidget(k)
        g = QGridLayout()
        g.setSpacing(6)
        self.a_nieuw_knoppen = []
        soorten = [s for s in ach.SOORTEN if s != "plaat"]
        for i, s in enumerate(soorten):
            b = QPushButton(ach.naam(s, NL))
            b.setIcon(QIcon(ach.voorbeeld(s)))
            b.setIconSize(QSize(52, 35))
            b.setStyleSheet("text-align: left; padding: 4px 6px;")
            b.setMinimumHeight(46)
            b.clicked.connect(lambda _=False, s=s: self.ach_bij(s))
            g.addWidget(b, i // 2, i % 2)
            self.a_nieuw_knoppen.append(b)
        n = len(soorten)
        self.a_k_plaat = QPushButton(T("a_plaat"))
        self.a_k_plaat.setObjectName("paars")
        self.a_k_plaat.setMinimumHeight(46)
        self.a_k_plaat.clicked.connect(self.ach_plaat_kies)
        g.addWidget(self.a_k_plaat, n // 2 + (n % 2), 0)
        self.a_k_teken = QPushButton(T("a_teken"))
        self.a_k_teken.setObjectName("paars")
        self.a_k_teken.setMinimumHeight(46)
        self.a_k_teken.clicked.connect(self.ach_teken)
        g.addWidget(self.a_k_teken, n // 2 + (n % 2), 1)
        v.addLayout(g)
        hint = QLabel(T("a_hint"))
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        v.addWidget(hint)
        v.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return sc

    def _ach_lagen(self, maak=False):
        """De achtergrond-stapel waar we nu aan werken (bladzijde of gekozen vakje), of None."""
        pg = self.boek["paginas"][self.nu]
        if self.ach_doel == "pagina":
            return pg.setdefault("achtergrond", []) if maak else pg.get("achtergrond", [])
        v = self._vak()
        if v is None:
            return None
        return v.setdefault("achtergrond", []) if maak else v.get("achtergrond", [])

    def ach_laag(self):
        ls = self._ach_lagen()
        if not ls:
            return None
        self.ach_i = max(0, min(self.ach_i, len(ls) - 1))
        return ls[self.ach_i]

    def ach_doel_zet(self, d):
        self.ach_doel = d
        self.a_k_vak.setChecked(d == "vak")
        self.a_k_pag.setChecked(d == "pagina")
        self.ach_i = len(self._ach_lagen() or []) - 1
        self.ach_ververs()
        self.vlak.update()

    def ach_ververs(self):
        if not hasattr(self, "a_lijst"):
            return
        ls = self._ach_lagen()
        geen_vak = ls is None
        self.a_geen.setVisible(geen_vak)
        ls = ls or []
        self.ach_i = max(0, min(self.ach_i, len(ls) - 1))
        self.a_lijst.blockSignals(True)
        self.a_lijst.clear()
        for i in range(len(ls) - 1, -1, -1):
            s = ls[i].get("soort")
            it = QListWidgetItem(ach.naam(s, NL))
            if s == "plaat":
                im = self.beelden.beeld(ls[i].get("id"))
                if im is not None and not im.isNull():
                    it.setIcon(QIcon(QPixmap.fromImage(im.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                                 Qt.TransformationMode.SmoothTransformation))))
            else:
                it.setIcon(QIcon(self._ach_icoon(s)))
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if ls[i].get("zicht", True) else Qt.CheckState.Unchecked)
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.a_lijst.addItem(it)
        if ls:
            self.a_lijst.setCurrentRow(len(ls) - 1 - self.ach_i)
        self.a_lijst.blockSignals(False)
        self.a_lijst.setEnabled(not geen_vak)
        self.a_leeg.setVisible(not geen_vak and not ls)
        sp = ls[self.ach_i] if ls else None
        s = sp.get("soort") if sp else None
        namen = ach.KLEUREN.get(s, ()) if sp else ()
        for j, (b, sl) in enumerate(((self.a_k1, "k1"), (self.a_k2, "k2"))):
            if j < len(namen):
                kl = QColor(sp.get(sl) or "#ffffff")
                tekst = "#111111" if kl.lightness() > 140 else "#ffffff"
                b.setText(namen[j][0 if NL else 1])
                b.setStyleSheet("QPushButton { background: %s; color: %s; border: 3px solid #4a3d66; font-weight: 700; }"
                                "QPushButton:hover { border-color: #ffd166; }" % (kl.name(), tekst))
                b.setVisible(True)
            else:
                b.setVisible(False)
        for b in (self.a_k_weg, self.a_dekking, self.a_k_spiegel):
            b.setEnabled(sp is not None)
        self.a_k_anders.setEnabled(sp is not None and s != "plaat" and s not in ("kleur", "verloop"))
        for b in (self.a_zoom, self.a_k_passend):
            b.setEnabled(s == "plaat")
        self.a_k_alle.setEnabled(self.ach_doel == "vak" and bool(ls))
        for b in self.a_nieuw_knoppen + [self.a_k_plaat]:
            b.setEnabled(not geen_vak)
        self.a_dekking.blockSignals(True)
        self.a_dekking.setValue(int(round(100 * sp.get("dekking", 1.0))) if sp else 100)
        self.a_dekking.blockSignals(False)
        self.a_zoom.blockSignals(True)
        self.a_zoom.setValue(int(round(100 * sp.get("zoom", 1.0))) if s == "plaat" else 100)
        self.a_zoom.blockSignals(False)
        self.a_k_spiegel.setChecked(bool(sp and sp.get("spiegel")))

    def _ach_icoon(self, soort):
        if not hasattr(self, "_ach_iconen"):
            self._ach_iconen = {}
        if soort not in self._ach_iconen:
            self._ach_iconen[soort] = ach.voorbeeld(soort, 90, 60)
        return self._ach_iconen[soort]

    def _ach_kies(self, rij):
        it = self.a_lijst.item(rij)
        if it is not None:
            self.ach_i = it.data(Qt.ItemDataRole.UserRole)
            self.ach_ververs()

    def _ach_vinkje(self, it):
        ls = self._ach_lagen()
        if ls:
            ls[it.data(Qt.ItemDataRole.UserRole)]["zicht"] = it.checkState() == Qt.CheckState.Checked
            self.vlak.update()
            self.na_wijziging()

    def ach_bij(self, soort, extra=None):
        ls = self._ach_lagen(maak=True)
        if ls is None:
            QMessageBox.information(self, APP, T("eerst_vak"))
            return
        sp = ach.nieuw(soort)
        if extra:
            sp.update(extra)
        plek = self.ach_i + 1 if ls else 0
        if soort in ach.VOL and not extra:
            plek = 0 if not ls or ls[0].get("soort") not in ach.VOL else self.ach_i + 1
        ls.insert(plek, sp)
        self.ach_i = plek
        self.ach_ververs()
        self.vlak.update()
        self.na_wijziging()

    def ach_plaat_kies(self):
        if self._ach_lagen() is None:
            QMessageBox.information(self, APP, T("eerst_vak"))
            return
        begin = self.instel.get("plaatjesmap") or os.path.expanduser("~")
        pad, _ = QFileDialog.getOpenFileName(self, T("kies_plaat"), begin,
                                             "%s (*.png *.jpg *.jpeg *.webp *.bmp *.gif)" % T("plaatjes"))
        if pad:
            self.instel["plaatjesmap"] = os.path.dirname(pad)
            self._bewaar_instel()
            self.ach_plaat(pad)

    def ach_plaat(self, pad):
        try:
            bid = self.beelden.voeg_toe(pad)
        except Exception as e:
            _log("achtergrond-plaatje %s: %s" % (pad, e))
            bid = None
        if not bid:
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        self.ach_bij("plaat", dict(id=bid))

    def ach_teken(self):
        """Een tekenlaag die achter de plaatjes ligt, en meteen naar het tekenen."""
        ls = self._lagen()
        ls.insert(0, dict(id=self.beelden.nieuwe_laag(), naam=T("a_tekening"), zicht=True, dekking=1.0, achter=True))
        self.laag_i = 0
        self.na_wijziging()
        self.k_binnen.setChecked(self.ach_doel == "vak")
        self.tabs_r.setCurrentIndex(1)
        self.lagen_bij()
        self.statusBar().showMessage(T("a_teken_klaar"), 10000)

    def ach_weg(self):
        ls = self._ach_lagen()
        if not ls:
            return
        del ls[self.ach_i]
        self.ach_i = max(0, self.ach_i - 1)
        self.ach_ververs()
        self.vlak.update()
        self.na_wijziging()

    def ach_schuif(self, d):
        ls = self._ach_lagen()
        if not ls:
            return
        j = self.ach_i + d
        if 0 <= j < len(ls):
            ls[self.ach_i], ls[j] = ls[j], ls[self.ach_i]
            self.ach_i = j
            self.ach_ververs()
            self.vlak.update()
            self.na_wijziging()

    def ach_kleur(self, sl):
        sp = self.ach_laag()
        if sp is None:
            return
        k = QColorDialog.getColor(QColor(sp.get(sl) or "#ffffff"), self, T("kleur"))
        if k.isValid():
            sp[sl] = k.name()
            self.ach_ververs()
            self.vlak.update()
            self.na_wijziging()

    def ach_anders(self):
        sp = self.ach_laag()
        if sp is not None:
            sp["zaad"] = (int(sp.get("zaad") or 1) * 7919 + 104729) % 99991 + 1
            self.vlak.update()
            self.na_wijziging()

    def ach_spiegel(self):
        sp = self.ach_laag()
        if sp is not None:
            sp["spiegel"] = not sp.get("spiegel")
            self.ach_ververs()
            self.vlak.update()
            self.na_wijziging()

    def _ach_dekking(self, w):
        sp = self.ach_laag()
        if sp is not None:
            sp["dekking"] = w / 100.0
            self.vlak.update()
            self.later_veranderd()

    def _ach_zoom(self, w):
        sp = self.ach_laag()
        if sp is not None and sp.get("soort") == "plaat":
            sp["zoom"] = w / 100.0
            self.vlak.update()
            self.later_veranderd()

    def ach_zoom_bij(self):
        sp = self.ach_laag()
        self.a_zoom.blockSignals(True)
        self.a_zoom.setValue(int(round(100 * sp.get("zoom", 1.0))) if sp and sp.get("soort") == "plaat" else 100)
        self.a_zoom.blockSignals(False)

    def ach_passend(self):
        sp = self.ach_laag()
        if sp is not None and sp.get("soort") == "plaat":
            sp.update(zoom=1.0, dx=0.0, dy=0.0)
            self.ach_ververs()
            self.vlak.update()
            self.na_wijziging()

    def ach_alle(self):
        v = self._vak()
        if v is None or not v.get("achtergrond"):
            return
        if QMessageBox.question(self, APP, T("a_alle_vraag")) != QMessageBox.StandardButton.Yes:
            return
        for ander in self.boek["paginas"][self.nu]["vakjes"]:
            if ander is not v:
                ander["achtergrond"] = copy.deepcopy(v["achtergrond"])
        self.vlak.update()
        self.na_wijziging()

    # ---------------------------------------------------------- tekenen
    def _tab_wissel(self, i):
        self.k_teken.setChecked(False)
        self.vlak.tgekozen = None
        if i == 1:
            self.vlak.modus = "verf"
            self.vlak.gekozen = None
            self.lagen_bij()
        elif i == 2:
            self.vlak.modus = "tekst"
            self.vlak.gekozen = None
            self.vlak.muis = None
            self.vlak.unsetCursor()
            self.tekst_bij()
        elif i == 4:
            self.vlak.modus = "tekst"
            self.vlak.gekozen = None
            self.vlak.muis = None
            self.vlak.unsetCursor()
            self.kast_bij()
            self.fig_bij()
        elif i == 3:
            self.vlak.modus = "achter"
            self.vlak.muis = None
            self.vlak.unsetCursor()
            self.ach_i = len(self._ach_lagen() or []) - 1
            self.ach_ververs()
        else:
            self.vlak.modus = "plaat" if self.k_mplaat.isChecked() else "vak"
            self.vlak.muis = None
            self.vlak.unsetCursor()
        self.knoppen_bij()
        self.vlak.setFocus()

    def kies_gereedschap(self, soort):
        self.gs.soort = soort
        self.gereed[soort].setChecked(True)
        self.vlak.update()

    def zet_kleur(self, k):
        self.gs.kleur = QColor(k)
        self.kleurvak.setStyleSheet("QPushButton#staal { background: %s; }" % self.gs.kleur.name())
        for kl, b in self.stalen:
            b.setChecked(QColor(kl) == self.gs.kleur)
        if self.gs.soort in ("gum", "pipet"):
            self.kies_gereedschap("pen")

    def _kies_kleur(self):
        k = QColorDialog.getColor(self.gs.kleur, self, T("kleur"))
        if k.isValid():
            self.zet_kleur(k)

    def zet_dikte(self, w, schuif=True):
        w = max(1, min(60, int(w)))
        self.gs.dikte = float(w)
        self.dikte_l.setText(str(w))
        if schuif:
            self.dikte.blockSignals(True)
            self.dikte.setValue(w)
            self.dikte.blockSignals(False)
        self.vlak.update()

    # -- lagen (in de lijst staat de bovenste laag bovenaan)
    def _lagen(self):
        return self.boek["paginas"][self.nu]["lagen"]

    def huidige_laag(self):
        ls = self._lagen()
        if not ls:
            return None, None
        self.laag_i = max(0, min(self.laag_i, len(ls) - 1))
        l = ls[self.laag_i]
        if not l.get("zicht", True):
            return None, l["id"]
        return self.beelden.lagen.get(l["id"]), l["id"]

    def lagen_bij(self):
        ls = self._lagen()
        self.laag_i = max(0, min(self.laag_i, len(ls) - 1))
        self.lagenlijst.blockSignals(True)
        self.lagenlijst.clear()
        for i in range(len(ls) - 1, -1, -1):
            it = QListWidgetItem(("🌄 " if ls[i].get("achter") else "") + ls[i].get("naam", T("laag") % (i + 1)))
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if ls[i].get("zicht", True) else Qt.CheckState.Unchecked)
            it.setData(Qt.ItemDataRole.UserRole, i)
            self.lagenlijst.addItem(it)
        self.lagenlijst.setCurrentRow(len(ls) - 1 - self.laag_i)
        self.lagenlijst.blockSignals(False)
        self.dekking.blockSignals(True)
        self.dekking.setValue(int(round(100 * ls[self.laag_i].get("dekking", 1.0))) if ls else 100)
        self.dekking.blockSignals(False)
        self.k_achter.blockSignals(True)
        self.k_achter.setChecked(bool(ls and ls[self.laag_i].get("achter")))
        self.k_achter.blockSignals(False)

    def _laag_achter(self, aan):
        ls = self._lagen()
        if ls:
            ls[self.laag_i]["achter"] = bool(aan)
            self.lagen_bij()
            self.vlak.update()
            self.na_wijziging()

    def _kies_laag(self, rij):
        it = self.lagenlijst.item(rij)
        if it is not None:
            self.laag_i = it.data(Qt.ItemDataRole.UserRole)
            self.lagen_bij()

    def _laag_vinkje(self, it):
        i = it.data(Qt.ItemDataRole.UserRole)
        self._lagen()[i]["zicht"] = it.checkState() == Qt.CheckState.Checked
        self.lagen_bij()
        self.vlak.update()
        self.na_wijziging()

    def _laag_naam(self, it):
        i = it.data(Qt.ItemDataRole.UserRole)
        l = self._lagen()[i]
        naam, ok = QInputDialog.getText(self, APP, T("laag_naam"), text=l.get("naam", ""))
        if ok and naam.strip():
            l["naam"] = naam.strip()[:30]
            self.lagen_bij()
            self.na_wijziging()

    def laag_bij(self):
        ls = self._lagen()
        ls.insert(self.laag_i + 1, dict(id=self.beelden.nieuwe_laag(), naam=T("laag") % (len(ls) + 1), zicht=True, dekking=1.0))
        self.laag_i += 1
        self.lagen_bij()
        self.na_wijziging()

    def laag_weg(self):
        ls = self._lagen()
        if len(ls) <= 1:
            return
        if QMessageBox.question(self, APP, '"%s" %s' % (ls[self.laag_i].get("naam", ""), "weghalen?" if NL else "remove?")) \
                != QMessageBox.StandardButton.Yes:
            return
        del ls[self.laag_i]           # het plaatje blijft in het geheugen, dan kan Ongedaan hem terugzetten
        self.laag_i = max(0, self.laag_i - 1)
        self.lagen_bij()
        self.vlak.update()
        self.na_wijziging()

    def laag_schuif(self, d):
        ls = self._lagen()
        j = self.laag_i + d
        if 0 <= j < len(ls):
            ls[self.laag_i], ls[j] = ls[j], ls[self.laag_i]
            self.laag_i = j
            self.lagen_bij()
            self.vlak.update()
            self.na_wijziging()

    def _dekking(self, w):
        ls = self._lagen()
        if ls:
            ls[self.laag_i]["dekking"] = w / 100.0
            self.vlak.update()
            self.later_veranderd()

    def samen_beeld(self):
        """De hele bladzijde zoals je hem ziet, op laag-resolutie (voor het emmertje en kleur pakken)."""
        im = QImage(tk.LB, tk.LH, QImage.Format.Format_ARGB32)
        im.fill(QColor("#ffffff"))
        p = QPainter(im)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        teken_pagina(p, self.boek["paginas"][self.nu], self.beelden, tk.LS)
        p.end()
        return im

    def pixel_stap(self, lid, rect, voor, na):
        if lid is None or rect.isEmpty():
            return
        self.terug.append(dict(t="pix", laag=lid, rect=rect, voor=voor, na=na))
        self.terug = self.terug[-60:]
        self.vooruit = []
        self.pix_teller += 1
        self.miniatuur(self.nu)
        self.knoppen_bij()
        self._titel()

    def _plak(self, lid, rect, beeld):
        im = self.beelden.lagen.get(lid)
        if im is None:
            return
        p = QPainter(im)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.drawImage(rect.topLeft(), beeld)
        p.end()

    # ---------------------------------------------------------- staat / ongedaan maken
    def _staat(self):
        return json.dumps(self.boek, sort_keys=True)

    def na_wijziging(self):
        nu = self._staat()
        if nu != self.json_nu:
            self.terug.append(dict(t="json", voor=self.json_nu, na=nu))
            self.terug = self.terug[-60:]
            self.vooruit = []
            self.json_nu = nu
        self.miniatuur(self.nu)
        self.knoppen_bij()
        self._titel()

    def later_veranderd(self):
        self._later.start(600)

    def ongedaan(self):
        if not self.terug:
            return
        st = self.terug.pop()
        self.vooruit.append(st)
        self._toepassen(st, "voor")

    def opnieuw(self):
        if not self.vooruit:
            return
        st = self.vooruit.pop()
        self.terug.append(st)
        self._toepassen(st, "na")

    def _toepassen(self, st, kant):
        if st["t"] == "pix":
            self._plak(st["laag"], st["rect"], st[kant])
            self.pix_teller += 1
            self.vlak.update()
            self.miniatuur(self.nu)
            self.knoppen_bij()
            self._titel()
            return
        self.boek = json.loads(st[kant])
        self.json_nu = st[kant]
        self.nu = min(self.nu, len(self.boek["paginas"]) - 1)
        self.vlak.gekozen = None
        if self.vlak._tekst() is None:
            self.vlak.tgekozen = None
        self.tekst_bij()
        self.ververs_alles()

    # ---------------------------------------------------------- weergave bijwerken
    def ververs_alles(self):
        for pg in self.boek["paginas"]:
            zorg_lagen(pg, self.beelden)
        self.lijst.blockSignals(True)
        self.lijst.clear()
        nr = 0
        for i, pg in enumerate(self.boek["paginas"]):
            if pg.get("soort") == "voor":
                naam = T("voorkant")
            elif pg.get("soort") == "achter":
                naam = T("achterkant")
            else:
                nr += 1
                naam = str(nr)
            it = QListWidgetItem(naam)
            it.setData(Qt.ItemDataRole.UserRole, i)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            self.lijst.addItem(it)
            self.miniatuur(i)
        self.lijst.setCurrentRow(self.nu)
        self.lijst.blockSignals(False)
        self.lagen_bij()
        self.knoppen_bij()
        self.vlak.update()
        self._titel()

    def _pagina_versleept(self):
        volg = [self.lijst.item(k).data(Qt.ItemDataRole.UserRole) for k in range(self.lijst.count())]
        if sorted(volg) != list(range(len(self.boek["paginas"]))) or volg == list(range(len(volg))):
            return
        oud = self.boek["paginas"]
        self.boek["paginas"] = [oud[i] for i in volg]
        self.nu = volg.index(self.nu) if self.nu in volg else 0
        self.ververs_alles()
        self.na_wijziging()

    def miniatuur(self, i):
        it = self.lijst.item(i)
        if it is None or i >= len(self.boek["paginas"]):
            return
        pm = QPixmap(96, 136)
        pm.fill(QColor("#16131f"))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        teken_pagina(p, self.boek["paginas"][i], self.beelden, 96 / PB)
        p.end()
        it.setIcon(QIcon(pm))

    def knoppen_bij(self):
        v = self._vak()
        heeft = v is not None
        for b in (self.k_plaat, self.k_vakweg, self.rand):
            b.setEnabled(heeft)
        plaat = heeft and bool(v.get("beeld"))
        for b in (self.k_passend, self.k_plaatweg, self.zoom):
            b.setEnabled(plaat)
        self.geen.setVisible(not heeft)
        self.rand.blockSignals(True)
        self.rand.setValue(int(v.get("rand", 6)) if heeft else 6)
        self.rand.blockSignals(False)
        self.zoom_bij()
        if self.vlak.modus == "achter":
            ls = self._ach_lagen() or []
            if self.ach_i >= len(ls) or getattr(self, "_ach_vak", None) != (self.nu, self.vlak.gekozen, self.ach_doel):
                self.ach_i = len(ls) - 1
            self._ach_vak = (self.nu, self.vlak.gekozen, self.ach_doel)
            self.ach_ververs()
        self.k_terug.setEnabled(bool(self.terug))
        self.k_vooruit.setEnabled(bool(self.vooruit))
        self.vlak.update()

    def zoom_bij(self):
        v = self._vak()
        self.zoom.blockSignals(True)
        self.zoom.setValue(int(round(100 * v["beeld"].get("zoom", 1.0))) if v and v.get("beeld") else 100)
        self.zoom.blockSignals(False)

    def _titel(self):
        naam = os.path.basename(self.pad) if self.pad else self.boek.get("titel", T("naamloos"))
        ster = " *" if self._gewijzigd() else ""
        self.setWindowTitle("%s%s  -  %s %s" % (naam, ster, APP, VERSIE))

    def _gewijzigd(self):
        return self._staat() != self.bewaard_staat or self.pix_teller != self.bewaard_pix

    def _vak(self):
        i = self.vlak.gekozen
        vs = self.boek["paginas"][self.nu]["vakjes"]
        return vs[i] if i is not None and 0 <= i < len(vs) else None

    # ---------------------------------------------------------- bladzijden
    def kies_pagina(self, i):
        if 0 <= i < len(self.boek["paginas"]):
            self.nu = i
            self.vlak.gekozen = None
            self.vlak.tgekozen = None
            self.tekst_bij()
            self.laag_i = len(self.boek["paginas"][i].get("lagen", [])) - 1
            self.lagen_bij()
            self.knoppen_bij()

    def pagina_bij(self):
        pg = dict(vakjes=indeling(4, self.ruimte.value()))
        zorg_lagen(pg, self.beelden)
        self.boek["paginas"].insert(self.nu + 1, pg)
        self.nu += 1
        self.vlak.gekozen = None
        self.ververs_alles()
        self.na_wijziging()

    def pagina_weg(self):
        if len(self.boek["paginas"]) <= 1:
            return
        if QMessageBox.question(self, APP, (T("blz") % (self.nu + 1)) + (" weghalen?" if NL else " remove?")) \
                != QMessageBox.StandardButton.Yes:
            return
        del self.boek["paginas"][self.nu]
        self.nu = max(0, self.nu - 1)
        self.vlak.gekozen = None
        self.ververs_alles()
        self.na_wijziging()

    def pagina_schuif(self, d):
        j = self.nu + d
        ps = self.boek["paginas"]
        if 0 <= j < len(ps):
            ps[self.nu], ps[j] = ps[j], ps[self.nu]
            self.nu = j
            self.ververs_alles()
            self.na_wijziging()

    # ---------------------------------------------------------- vakjes
    def zet_indeling(self, soort):
        oud = self.boek["paginas"][self.nu]["vakjes"]
        nieuw = indeling(soort, self.ruimte.value())
        # plaatjes die er al in zaten gaan mee naar de nieuwe vakjes (op volgorde)
        plaatjes = [v.get("beeld") for v in oud if v.get("beeld")]
        for v, b in zip(nieuw, plaatjes):
            v["beeld"] = b
        achter = [v.get("achtergrond") for v in oud if v.get("achtergrond")]
        for v, a in zip(nieuw, achter):
            v["achtergrond"] = a
        self.boek["paginas"][self.nu]["vakjes"] = nieuw
        self.vlak.gekozen = None
        self.vlak.update()
        self.na_wijziging()

    def _teken_modus(self, aan):
        self.vlak.modus = "nieuwvak" if aan else ("plaat" if self.k_mplaat.isChecked() else "vak")

    def zet_modus(self, m):
        self.k_teken.setChecked(False)
        self.vlak.modus = m

    def vak_weg(self):
        v = self._vak()
        if v is None:
            return
        self.boek["paginas"][self.nu]["vakjes"].remove(v)
        self.vlak.gekozen = None
        self.na_wijziging()

    def _rand(self, w):
        v = self._vak()
        if v is not None:
            v["rand"] = w
            self.vlak.update()
            self.later_veranderd()

    def _zoom_schuif(self, w):
        v = self._vak()
        if v and v.get("beeld"):
            v["beeld"]["zoom"] = w / 100.0
            self.vlak.update()
            self.later_veranderd()

    # ---------------------------------------------------------- plaatjes
    def plaatje_invoegen(self):
        if self._vak() is None:
            QMessageBox.information(self, APP, T("eerst_vak"))
            return
        begin = self.instel.get("plaatjesmap") or os.path.expanduser("~")
        pad, _ = QFileDialog.getOpenFileName(self, T("kies_plaat"), begin,
                                             "%s (*.png *.jpg *.jpeg *.webp *.bmp *.gif)" % T("plaatjes"))
        if pad:
            self.instel["plaatjesmap"] = os.path.dirname(pad)
            self._bewaar_instel()
            self.zet_plaatje(pad)

    def zet_plaatje(self, pad):
        v = self._vak()
        if v is None:
            return
        try:
            bid = self.beelden.voeg_toe(pad)
        except Exception as e:
            _log("plaatje %s: %s" % (pad, e))
            bid = None
        if not bid:
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        v["beeld"] = dict(id=bid, zoom=1.0, dx=0.0, dy=0.0)
        self.k_mplaat.setChecked(True)
        self.zet_modus("plaat")
        self.na_wijziging()

    def plaatje_passend(self):
        v = self._vak()
        if v and v.get("beeld"):
            v["beeld"].update(zoom=1.0, dx=0.0, dy=0.0)
            self.na_wijziging()

    def plaatje_weg(self):
        v = self._vak()
        if v and v.get("beeld"):
            v["beeld"] = None
            self.na_wijziging()

    # ---------------------------------------------------------- bestanden
    def _gebruikt(self):
        ids = {v["beeld"]["id"] for p in self.boek["paginas"] for v in p["vakjes"] if v.get("beeld")}
        for p in self.boek["paginas"]:
            ids |= ach.gebruikte_beelden(p.get("achtergrond"))
            for v in p["vakjes"]:
                ids |= ach.gebruikte_beelden(v.get("achtergrond"))
            ids |= {t["bid"] for t in p.get("teksten", []) if t.get("soort") == "figuur" and t.get("bid")}
        return ids

    def _schrijf(self, pad):
        tmp = pad + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("boek.json", json.dumps(self.boek, ensure_ascii=False, indent=1))
            for bid in self._gebruikt():
                if bid in self.beelden.data:
                    z.writestr("beelden/%s" % bid, self.beelden.data[bid])
            for lid in {l["id"] for p in self.boek["paginas"] for l in p.get("lagen", [])}:
                im = self.beelden.lagen.get(lid)
                if im is not None:
                    ba = QByteArray()
                    buf = QBuffer(ba)
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    im.save(buf, "PNG")
                    buf.close()
                    z.writestr("lagen/%s.png" % lid, bytes(ba))
        os.replace(tmp, pad)
        self.pad = pad
        self.bewaard_staat = self._staat()
        self.bewaard_pix = self.pix_teller
        self.instel["laatste_map"] = os.path.dirname(pad)
        self._bewaar_instel()
        self._titel()
        self.statusBar().showMessage(T("bewaard") % os.path.basename(pad), 8000)

    def opslaan(self):
        if self.pad:
            self._schrijf(self.pad)
        else:
            self.opslaan_als()

    def opslaan_als(self):
        os.makedirs(MIJN, exist_ok=True)
        begin = os.path.join(self.instel.get("laatste_map") or MIJN, (self.boek.get("titel") or "strip") + ".dcomic")
        pad, _ = QFileDialog.getSaveFileName(self, T("opslaan_als"), begin, "%s (*.dcomic)" % T("project"))
        if pad:
            if not pad.lower().endswith(".dcomic"):
                pad += ".dcomic"
            self.boek["titel"] = os.path.splitext(os.path.basename(pad))[0]
            self._schrijf(pad)

    def _mag_weg(self):
        if not self._gewijzigd():
            return True
        k = QMessageBox.question(self, APP, T("vraag_bewaren"), QMessageBox.StandardButton.Yes |
                                 QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if k == QMessageBox.StandardButton.Cancel:
            return False
        if k == QMessageBox.StandardButton.Yes:
            self.opslaan()
            return not self._gewijzigd()
        return True

    def nieuw(self):
        if not self._mag_weg():
            return
        self.boek, self.nu, self.pad = nieuw_boek(), 0, None
        self.beelden = Beelden()
        for pg in self.boek["paginas"]:
            zorg_lagen(pg, self.beelden)
        self.terug, self.vooruit = [], []
        self.bewaard_staat = self.json_nu = self._staat()
        self.bewaard_pix = self.pix_teller
        self.vlak.gekozen = None
        self.ververs_alles()

    def openen(self, pad=None):
        if not self._mag_weg():
            return
        if not pad:
            os.makedirs(MIJN, exist_ok=True)
            pad, _ = QFileDialog.getOpenFileName(self, T("open"), self.instel.get("laatste_map") or MIJN,
                                                 "%s (*.dcomic)" % T("project"))
            if not pad:
                return
        try:
            b = Beelden()
            with zipfile.ZipFile(pad) as z:
                boek = json.loads(z.read("boek.json").decode("utf-8"))
                for n in z.namelist():
                    if n.startswith("beelden/"):
                        b.data[n.split("/", 1)[1]] = z.read(n)
                    elif n.startswith("lagen/") and n.endswith(".png"):
                        im = QImage.fromData(z.read(n))
                        if not im.isNull():
                            im = im.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                            if im.width() != tk.LB or im.height() != tk.LH:
                                im = im.scaled(tk.LB, tk.LH)
                            b.lagen[n[6:-4]] = im
        except Exception as e:
            _log("openen %s: %s" % (pad, e))
            QMessageBox.warning(self, APP, T("fout_open"))
            return
        self.boek, self.beelden, self.nu, self.pad = boek, b, 0, pad
        for pg in self.boek["paginas"]:
            zorg_lagen(pg, self.beelden)
        self.terug, self.vooruit = [], []
        self.bewaard_staat = self.json_nu = self._staat()
        self.bewaard_pix = self.pix_teller
        self.instel["laatste_map"] = os.path.dirname(pad)
        self._bewaar_instel()
        self.vlak.gekozen = None
        self.ververs_alles()

    def als_png(self):
        if len(self.boek["paginas"]) > 1:
            m = QMessageBox(self)
            m.setWindowTitle(APP)
            m.setText(T("png_lang"))
            een = m.addButton(T("blz") % (self.nu + 1), QMessageBox.ButtonRole.AcceptRole)
            alle = m.addButton(T("alle_png"), QMessageBox.ButtonRole.AcceptRole)
            m.addButton(QMessageBox.StandardButton.Cancel)
            m.exec()
            if m.clickedButton() is alle:
                self.alle_als_png()
                return
            if m.clickedButton() is not een:
                return
        os.makedirs(MIJN, exist_ok=True)
        naam = "%s - %s.png" % (self.boek.get("titel") or "strip", T("blz") % (self.nu + 1))
        pad, _ = QFileDialog.getSaveFileName(self, T("png"), os.path.join(self.instel.get("laatste_map") or MIJN, naam),
                                             "PNG (*.png)")
        if not pad:
            return
        if not pad.lower().endswith(".png"):
            pad += ".png"
        s = 2.48                        # 1000 eenheden -> 2480 px breed (A4 op 300 dpi)
        im = QImage(int(PB * s), int(PH * s), QImage.Format.Format_RGB32)
        im.fill(QColor("#ffffff"))
        p = QPainter(im)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        teken_pagina(p, self.boek["paginas"][self.nu], self.beelden, s)
        p.end()
        im.save(pad)
        QMessageBox.information(self, APP, T("png_klaar") % pad)

    # ---------------------------------------------------------- overig
    # ---------------------------------------------------------- kaft
    def kaft(self, kant):
        ps = self.boek["paginas"]
        for i, pg in enumerate(ps):
            if pg.get("soort") == kant:
                self.nu = i
                self.ververs_alles()
                self.statusBar().showMessage(T("kaft_er") % T("voorkant" if kant == "voor" else "achterkant").lower(), 6000)
                return
        pg = dict(soort=kant, vakjes=[dict(x=0.0, y=0.0, w=PB, h=PH, rand=0, beeld=None)])
        zorg_lagen(pg, self.beelden)
        if kant == "voor":
            titel = bl.nieuw("geluid", PB / 2, 230)
            titel.update(tekst=self.boek.get("titel") or T("naamloos"), w=820, h=230, x=90, y=115, draai=-4, ster=False,
                         kleur="#ffd166")
            door = bl.nieuw("verteller", PB / 2, PH - 150)
            door.update(tekst=T("door"), w=520, h=90, x=240, y=PH - 210, grootte=34)
            pg["teksten"] = [titel, door]
            ps.insert(0, pg)
            self.nu = 0
        else:
            ach = bl.nieuw("verteller", PB / 2, PH - 120)
            ach.update(tekst=T("achter_tekst") + "\ndravenlock.nl", w=520, h=110, x=240, y=PH - 200, grootte=26)
            pg["teksten"] = [ach]
            ps.append(pg)
            self.nu = len(ps) - 1
        self.vlak.gekozen = self.vlak.tgekozen = None
        self.ververs_alles()
        self.na_wijziging()

    # ---------------------------------------------------------- het hele boek
    def _render(self, pg, breed):
        """Eén bladzijde als QImage van 'breed' pixels breed (zonder hulplijnen)."""
        s = breed / PB
        im = QImage(int(PB * s), int(PH * s), QImage.Format.Format_RGB32)
        im.fill(QColor("#ffffff"))
        p = QPainter(im)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        teken_pagina(p, pg, self.beelden, s)
        p.end()
        return im

    def als_pdf(self):
        os.makedirs(MIJN, exist_ok=True)
        naam = (self.boek.get("titel") or "strip") + ".pdf"
        pad, _ = QFileDialog.getSaveFileName(self, T("pdf"), os.path.join(self.instel.get("laatste_map") or MIJN, naam),
                                             "PDF (*.pdf)")
        if not pad:
            return
        if not pad.lower().endswith(".pdf"):
            pad += ".pdf"
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.maak_pdf(pad)
        finally:
            QApplication.restoreOverrideCursor()
        n = len(self.boek["paginas"])
        if QMessageBox.question(self, APP, T("pdf_klaar") % (n, pad)) == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(pad))

    def maak_pdf(self, pad):
        """Het hele boek als PDF op A4: lijnen, ballonnen en letters blijven scherp (vector)."""
        pdf = QPdfWriter(pad)
        pdf.setTitle(self.boek.get("titel") or APP)
        pdf.setCreator("%s %s - Dravenlock" % (APP, VERSIE))
        pdf.setResolution(300)
        pdf.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait, QMarginsF(0, 0, 0, 0)))
        p = QPainter(pdf)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, pg in enumerate(self.boek["paginas"]):
            if i:
                pdf.newPage()
            vp = p.viewport()
            teken_pagina(p, pg, self.beelden, min(vp.width() / PB, vp.height() / PH))
        p.end()

    def alle_als_png(self):
        map_ = QFileDialog.getExistingDirectory(self, T("kies_map"), self.instel.get("laatste_map") or MIJN)
        if not map_:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            titel = self.boek.get("titel") or "strip"
            for i, pg in enumerate(self.boek["paginas"]):
                self._render(pg, 2480).save(os.path.join(map_, "%s - %02d.png" % (titel, i + 1)))
        finally:
            QApplication.restoreOverrideCursor()
        QMessageBox.information(self, APP, T("png_alle_klaar") % (len(self.boek["paginas"]), map_))

    def bladeren(self):
        Bladeren(self).exec()

    def letter(self, d):
        self.f = round(min(1.6, max(0.8, self.f + d)), 2)
        self.instel["groot"] = self.f
        self._bewaar_instel()
        self.setStyleSheet(stijl(self.f))

    def snelgids(self):
        for n in ("DraveComic-Snelgids.pdf", "DraveComic-Snelgids.html"):
            p = _res(n)
            if os.path.exists(p):
                QDesktopServices.openUrl(QUrl.fromLocalFile(p))
                return
        QMessageBox.information(self, APP, "De snelgids komt bij de volgende versie." if NL else "The guide comes with the next version.")

    def closeEvent(self, e):
        if self._mag_weg():
            e.accept()
        else:
            e.ignore()


def main():
    def vang(t, w, tb):
        _log("".join(traceback.format_exception(t, w, tb)))
        sys.__excepthook__(t, w, tb)
    sys.excepthook = vang
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    w = Hoofd()
    w.show()
    try:
        import drave_doneer
        drave_doneer.voeg_toe(w, "nl" if NL else "en")
    except Exception:
        pass
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".dcomic") and os.path.exists(sys.argv[1]):
        w.openen(sys.argv[1])
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
