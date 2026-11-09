# -*- coding: utf-8 -*-
# DraveComic - Copyright (C) 2026 Dravenlock (Roger & Claudio). Vrije software onder de GNU GPL v3.0.
"""planner.py - de verhaal-planner (0.6.0).

Eerst het verhaal kort per bladzijde opschrijven: per vakje 'wat zie je?' en 'wie zegt wat?'.
Daarna zet DraveComic de bladzijden klaar: de vakjes, de praatballonnen met de tekst,
en in elk leeg vakje staat (alleen op het scherm) wat erin moet komen.
Het plan wordt in de strip bewaard (boek["plan"]), dus je kunt het later verder schrijven.
"""
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

INDELINGEN = [1, 2, 3, 4, 6, "strip"]
AANTAL = {1: 1, 2: 2, 3: 3, 4: 4, 6: 6, "strip": 7}
VERTELLER = ("verteller", "verteler", "vertel", "narrator", "caption")


def leeg_blad(soort=4):
    return dict(indeling=soort, vakjes=[dict(wat="", tekst="") for _ in range(AANTAL[soort])])


def regels_naar_teksten(tekst):
    """'Kira: Woef!' -> praatballon 'Woef!'; 'Verteller: Die nacht...' -> vertelblokje. Geeft [(soort, tekst)]."""
    uit = []
    for deel in re.split(r"\s*(?:\n|\|)\s*", tekst or ""):
        deel = deel.strip()
        if not deel:
            continue
        m = re.match(r"^([^:]{1,25}):\s*(.+)$", deel)
        if m:
            wie, wat = m.group(1).strip().lower(), m.group(2).strip()
            uit.append(("verteller" if wie in VERTELLER else "praat", wat))
        else:
            uit.append(("praat", deel))
    return uit


class Planner(QDialog):
    def __init__(self, ouder, nl, plan):
        super().__init__(ouder)
        self.nl = nl
        L = lambda a, b: a if nl else b
        self.L = L
        self.plan = [dict(indeling=b.get("indeling", 4), vakjes=[dict(v) for v in b.get("vakjes", [])]) for b in (plan or [])]
        if not self.plan:
            self.plan = [leeg_blad(4)]
        self.maken = False
        self.setWindowTitle(L("Verhaal-planner", "Story planner"))
        self.resize(1180, 820)
        v = QVBoxLayout(self)
        k = QLabel(L("📝  Verhaal-planner", "📝  Story planner"))
        k.setObjectName("kop")
        v.addWidget(k)
        u = QLabel(L("Schrijf per bladzijde kort op wat er in elk vakje gebeurt, en wie wat zegt. "
                     "Schrijf het zo: <b>Kira: Woef!</b> wordt een praatballon, <b>Verteller: Die nacht...</b> wordt een vertelblokje. "
                     "Meer zinnen in één vakje? Zet er een <b>|</b> tussen.",
                     "For each page, write briefly what happens in each panel and who says what. "
                     "Write it like this: <b>Kira: Woof!</b> becomes a speech balloon, <b>Narrator: That night...</b> a caption. "
                     "More lines in one panel? Put a <b>|</b> between them."))
        u.setWordWrap(True)
        u.setObjectName("sub")
        v.addWidget(u)
        midden = QHBoxLayout()
        links = QVBoxLayout()
        self.lijst = QListWidget()
        self.lijst.setFixedWidth(200)
        self.lijst.currentRowChanged.connect(self._kies)
        links.addWidget(self.lijst, 1)
        r = QHBoxLayout()
        b = QPushButton(L("+ Bladzijde", "+ Page"))
        b.clicked.connect(self._bij)
        r.addWidget(b)
        b = QPushButton(L("− Weg", "− Remove"))
        b.clicked.connect(self._weg)
        r.addWidget(b)
        links.addLayout(r)
        midden.addLayout(links)
        rechts = QVBoxLayout()
        ri = QHBoxLayout()
        ri.addWidget(QLabel(L("Indeling van deze bladzijde:", "Layout of this page:")))
        self.indeling = QComboBox()
        for s in INDELINGEN:
            self.indeling.addItem((L("%s vakjes", "%s panels") % s) if s != "strip" else L("Strip (3 rijen, 7 vakjes)", "Strip (3 rows, 7 panels)"))
        self.indeling.currentIndexChanged.connect(self._indeling)
        ri.addWidget(self.indeling)
        ri.addStretch(1)
        rechts.addLayout(ri)
        self.sc = QScrollArea()
        self.sc.setWidgetResizable(True)
        rechts.addWidget(self.sc, 1)
        midden.addLayout(rechts, 1)
        v.addLayout(midden, 1)
        kn = QHBoxLayout()
        self.info = QLabel()
        self.info.setObjectName("sub")
        kn.addWidget(self.info, 1)
        b = QPushButton(L("💾  Bewaren en sluiten", "💾  Save and close"))
        b.clicked.connect(self._bewaar_sluit)
        kn.addWidget(b)
        b = QPushButton(L("📄  Maak de bladzijden", "📄  Make the pages"))
        b.setObjectName("paars")
        b.clicked.connect(self._maak)
        kn.addWidget(b)
        v.addLayout(kn)
        self.velden = []
        self.nu = 0
        self._lijst_bij()

    # -- lijst
    def _lijst_bij(self):
        self.lijst.blockSignals(True)
        self.lijst.clear()
        for i in range(len(self.plan)):
            self.lijst.addItem(self.L("Bladzijde %d", "Page %d") % (i + 1))
        self.lijst.blockSignals(False)
        self.nu = max(0, min(self.nu, len(self.plan) - 1))
        self.lijst.setCurrentRow(self.nu)
        self._toon()

    def _kies(self, i):
        self._lees()
        self.nu = max(0, i)
        self._toon()

    def _bij(self):
        self._lees()
        self.plan.insert(self.nu + 1, leeg_blad(self.plan[self.nu]["indeling"] if self.plan else 4))
        self.nu += 1
        self._lijst_bij()

    def _weg(self):
        if len(self.plan) <= 1:
            self.plan = [leeg_blad(4)]
        else:
            del self.plan[self.nu]
        self._lijst_bij()

    # -- een bladzijde
    def _toon(self):
        b = self.plan[self.nu]
        self.indeling.blockSignals(True)
        self.indeling.setCurrentIndex(INDELINGEN.index(b["indeling"]) if b["indeling"] in INDELINGEN else 3)
        self.indeling.blockSignals(False)
        n = AANTAL[b["indeling"]]
        while len(b["vakjes"]) < n:
            b["vakjes"].append(dict(wat="", tekst=""))
        w = QWidget()
        w.setObjectName("wortel")
        g = QGridLayout(w)
        g.setColumnStretch(1, 1)
        self.velden = []
        for i in range(n):
            vk = b["vakjes"][i]
            kop = QLabel(self.L("Vakje %d", "Panel %d") % (i + 1))
            kop.setObjectName("kop")
            g.addWidget(kop, i * 3, 0, 1, 2)
            g.addWidget(QLabel(self.L("Wat zie je?", "What do you see?")), i * 3 + 1, 0)
            wat = QLineEdit(vk.get("wat", ""))
            wat.setPlaceholderText(self.L("bijv. Kira rent door het bos", "e.g. Kira runs through the woods"))
            g.addWidget(wat, i * 3 + 1, 1)
            g.addWidget(QLabel(self.L("Wie zegt wat?", "Who says what?")), i * 3 + 2, 0)
            tk = QLineEdit(vk.get("tekst", ""))
            tk.setPlaceholderText(self.L("bijv. Kira: Woef! | Verteller: Ze was weg.", "e.g. Kira: Woof! | Narrator: She was gone."))
            g.addWidget(tk, i * 3 + 2, 1)
            self.velden.append((wat, tk))
        g.setRowStretch(n * 3, 1)
        for e in w.findChildren(QLineEdit):
            e.setMinimumHeight(40)
        self.sc.setWidget(w)
        self.info.setText(self.L("%d bladzijde(n) in het plan", "%d page(s) in the plan") % len(self.plan))

    def _lees(self):
        if not self.velden or not (0 <= self.nu < len(self.plan)):
            return
        b = self.plan[self.nu]
        for i, (wat, tk) in enumerate(self.velden):
            if i < len(b["vakjes"]):
                b["vakjes"][i] = dict(wat=wat.text().strip(), tekst=tk.text().strip())

    def _indeling(self, i):
        self._lees()
        self.plan[self.nu]["indeling"] = INDELINGEN[i]
        self._toon()

    def resultaat(self):
        self._lees()
        # vakjes die er niet meer bij horen (kleinere indeling) laten we vallen
        for b in self.plan:
            b["vakjes"] = b["vakjes"][:AANTAL[b["indeling"]]]
        return self.plan

    def _bewaar_sluit(self):
        self.maken = False
        self.accept()

    def _maak(self):
        self.maken = True
        self.accept()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return            # Enter in een vakje sluit de planner niet
        super().keyPressEvent(e)
