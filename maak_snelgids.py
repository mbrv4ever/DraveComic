# Maakt DraveComic-Snelgids.pdf (grote letters). Copyright (C) 2026 Dravenlock (Roger & Claudio). GPL-3.0.
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import os
for n, f in (("D", "DejaVuSans.ttf"), ("DB", "DejaVuSans-Bold.ttf")):
    for m in ("/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/"):
        if os.path.exists(m + f):
            pdfmetrics.registerFont(TTFont(n, m + f)); break
P = HexColor("#3b2f6b")
t = ParagraphStyle("t", fontName="DB", fontSize=28, leading=34, textColor=P)
h = ParagraphStyle("h", fontName="DB", fontSize=19, leading=24, textColor=P, spaceBefore=14, spaceAfter=6, keepWithNext=1)
b = ParagraphStyle("b", fontName="D", fontSize=14, leading=21, spaceAfter=6)
li = ParagraphStyle("li", parent=b, leftIndent=18, bulletIndent=4)
E_ = []
H = lambda x: E_.append(Paragraph(x, h))
B = lambda x: E_.append(Paragraph(x, b))
L = lambda xs: [E_.append(Paragraph(x, li, bulletText="•")) for x in xs]
E_.append(Image("assets/icon.png", 3 * cm, 3 * cm, hAlign="LEFT"))
E_.append(Paragraph("DraveComic — snelgids", t))
B("Maak je eigen stripboek. Gratis (donationware) · GNU GPL v3.0 · Dravenlock (Roger &amp; Claudio)")
H("1. Bladzijden")
L(["Links staan al je bladzijden als kleine plaatjes. Klik erop om een bladzijde te kiezen.",
   "<b>+ Bladzijde</b> zet een nieuwe bladzijde achter de gekozen. <b>− Weg</b> haalt de gekozen weg.",
   "Met <b>▲</b> en <b>▼</b> schuif je een bladzijde naar voren of naar achteren. Je kunt een bladzijde ook gewoon <b>slepen</b> in de lijst.",
   "<b>📕 Voorkant</b> maakt een kaft vooraan: één groot vak voor je plaatje, de titel in stripletters en 'door ...'. Klik op de titel (tabblad Tekst) om hem te veranderen.",
   "<b>📗 Achterkant</b> zet een achterkant achteraan."])
H("2. Vakjes")
L(["Kies rechts een <b>indeling</b>: 1, 2, 3, 4 of 6 vakjes, of <b>Strip</b> (3 rijen). Plaatjes die er al in zaten, gaan mee.",
   "<b>Ruimte tussen de vakjes</b>: hoe breed de witte strook is (geldt voor de volgende indeling).",
   "<b>Zelf een vakje trekken</b>: zet de knop aan en sleep een rechthoek op de bladzijde.",
   "Klik op een vakje om het te kiezen (oranje stippellijn). Sleep het om het te verplaatsen.",
   "Sleep aan een oranje blokje om het vakje groter of kleiner te maken.",
   "<b>Rand (dikte)</b>: 0 = geen rand. <b>Vakje weghalen</b> of de toets <b>Delete</b>."])
H("3. Plaatjes")
L(["<b>Dubbelklik</b> op een vakje, of klik op <b>Plaatje invoegen</b>. Je kunt een plaatje ook vanuit de Verkenner op een vakje slepen.",
   "Het plaatje vult het vakje. Kies <b>Plaatje schuiven</b> en sleep om het goede stuk in beeld te krijgen.",
   "Draai aan het <b>muiswiel</b> of gebruik de <b>Zoom</b>-schuif om in of uit te zoomen.",
   "<b>Plaatje passend</b> zet zoom en plek terug. <b>Plaatje eruit</b> haalt het weg."])
H("4. Tekenen (tabblad Tekenen)")
L(["Klik rechts op het tabblad <b>Tekenen</b>. Nu tekent de muis op de bladzijde.",
   "<b>Pen</b>: een strakke lijn. <b>Potlood</b>: dun en een beetje doorzichtig. <b>Penseel</b>: inkt, wordt dunner als je snel beweegt.",
   "<b>Gum</b>: haalt weg wat je op deze laag tekende (het plaatje in het vakje blijft).",
   "<b>Emmertje</b>: klik in een vlak en het wordt gevuld met je kleur. <b>Kleur pakken</b>: klik ergens en je krijgt die kleur.",
   "<b>Vormen</b>: lijn, rechthoek, cirkel, pijl en snelheidsstrepen. Sleep van begin naar eind. Zet <b>Vorm gevuld</b> aan voor een volle vorm.",
   "Kies een <b>kleur</b> uit de 12 vakjes, of <b>Andere kleur…</b>. De <b>Dikte</b> regel je met de schuif, het muiswiel of de toetsen [ en ].",
   "<b>Binnen het vakje blijven</b>: wat je in een vakje begint, komt niet buiten dat vakje.",
   "<b>Tekentablet</b> (bijvoorbeeld Wacom): DraveComic voelt hoe hard je drukt. Zacht = dunne lijn, hard = dikke lijn (bij pen, potlood, penseel en gum). Draai je de pen om, dan is de achterkant de <b>gum</b>."])
H("5. Lagen")
L(["Een laag is een doorzichtig vel over de bladzijde. Teken bijvoorbeeld de lijnen op de ene laag en de kleuren op een andere.",
   "In de lijst staat de bovenste laag bovenaan. Klik op een laag om erop te tekenen. Het vinkje zet hem aan of uit.",
   "<b>+ Laag</b> en <b>− Laag</b>, <b>▲ ▼</b> om de volgorde te veranderen, <b>Doorzichtig</b> om een laag lichter te maken.",
   "Dubbelklik op een laag om hem een naam te geven."])
H("6. Tekst (tabblad Tekst)")
L(["Klik op het tabblad <b>Tekst</b>. Kies wat je wilt: <b>Praatballon</b>, <b>Denkwolk</b>, <b>Schreeuw</b>, <b>Vertelblokje</b> of <b>Geluidswoord</b>.",
   "Typ je tekst in het witte vak rechts. De ballon verandert meteen mee.",
   "Sleep een ballon om hem te verplaatsen. Sleep aan de oranje blokjes om hem groter of kleiner te maken.",
   "Sleep de <b>gele bol</b> om het staartje naar de prater te laten wijzen. Met <b>Staartje aan</b> zet je het staartje aan of uit.",
   "<b>Lettertype</b>: kies elke letter die op je pc staat. Met <b>B Vet</b> en <b>I Schuin</b> maak je de letters vet of schuin. <b>↺ Stripletter</b> zet de letter van DraveComic terug.",
   "<b>Lettergrootte</b>, <b>Letterkleur</b> en <b>Vulkleur</b> regel je rechts. Past de tekst niet, dan worden de letters vanzelf kleiner.",
   "Bij een <b>geluidswoord</b>: kies snel BAM!, POW!, BOEM! en meer, <b>draai</b> het woord en zet de <b>ster</b> erachter aan of uit.",
   "<b>Naar voren</b> / <b>Naar achteren</b> als dingen over elkaar liggen. <b>Tekst weghalen</b> of de toets Delete."])
H("7. Achtergrond (tabblad Achtergrond)")
L(["Kies bovenaan of de achtergrond voor het <b>gekozen vakje</b> is (klik eerst op een vakje) of voor de <b>hele bladzijde</b>.",
   "Een achtergrond bestaat uit <b>lagen, laag op laag</b>. Begin met een volle laag: <b>Lucht</b>, <b>Zonsondergang</b>, <b>Nacht</b>, <b>Kamer</b>, <b>Effen kleur</b> of <b>Kleurverloop</b>.",
   "Zet er daarna lagen bovenop die doorzichtig zijn: <b>Bergen</b>, <b>Heuvels</b>, <b>Stad</b>, <b>Bos</b>, <b>Zee</b>, en voor de sfeer <b>Regen</b>, <b>Sneeuw</b> of <b>Stippen</b>.",
   "Voor actie: <b>Actielijnen</b> (naar het midden), <b>Vaartstrepen</b> (snelheid) en <b>Knal</b> (een explosie).",
   "<b>Eigen plaatje</b>: een foto of tekening van jezelf als laag. Sleep in het vakje om hem te schuiven, draai aan het muiswiel om te zoomen. Je kunt een plaatje ook uit de Verkenner op het vakje slepen.",
   "<b>Zelf tekenen</b>: maakt een tekenlaag die <b>achter de plaatjes</b> ligt en gaat meteen naar Tekenen. Bij elke tekenlaag kun je dat met het vinkje <b>Achter de plaatjes</b> aan of uit zetten.",
   "In de lijst staat de bovenste laag bovenaan. Het vinkje zet een laag aan of uit, <b>▲ ▼</b> verandert de volgorde, <b>Laag weg</b> haalt hem weg.",
   "Bij de gekozen laag: de <b>kleuren</b> (bijvoorbeeld Bomen en Stammen, Huizen en Ramen), <b>🎲 Anders</b> (andere bomen, huizen of sterren), <b>Spiegelen</b> en <b>Doorzichtig</b>.",
   "<b>Ook in alle vakjes</b> zet de achtergrond van dit vakje in alle vakjes van de bladzijde.",
   "Heeft een vakje geen eigen achtergrond, dan zie je die van de bladzijde erdoorheen. Een PNG-plaatje met doorzichtige delen in een vakje laat de achtergrond ook zien."])
H("8. Figuren: de personage-kast (tabblad Figuren)")
L(["Teken je held <b>één keer</b> in een vakje (tabblad Tekenen). Klik dan op dat vakje en op <b>Bewaar uit tekening</b>. Geef hem een naam.",
   "DraveComic vraagt of de tekening meteen een <b>figuur</b> mag worden. Dan kun je hem verschuiven en groter of kleiner maken.",
   "Heb je al een plaatje (het liefst een PNG met doorzichtige achtergrond)? Klik op <b>Eigen plaatje in de kast</b>.",
   "Klik op een vakje, kies een figuur in de kast en klik op <b>Op de bladzijde zetten</b> (of dubbelklik op de figuur). Hij komt onderaan in het vakje.",
   "Sleep een figuur om hem te verplaatsen, sleep aan de oranje blokjes om hem groter of kleiner te maken. <b>Spiegelen</b> laat hem de andere kant op kijken.",
   "De kast staat in de map DraveComic-data\\Personages naast de app. Zo gebruik je je figuren in al je strips."])
H("9. Verhaal-planner (knop Planner)")
L(["Schrijf eerst je verhaal, kort per bladzijde. Kies per bladzijde de <b>indeling</b> (1, 2, 3, 4, 6 vakjes of Strip).",
   "Per vakje: <b>Wat zie je?</b> (bijvoorbeeld: Kira rent door het bos) en <b>Wie zegt wat?</b>",
   "Schrijf <b>Kira: Woef!</b> voor een praatballon en <b>Verteller: Die nacht...</b> voor een vertelblokje. Meer zinnen in één vakje? Zet er een <b>|</b> tussen.",
   "Klik op <b>Maak de bladzijden</b>: de bladzijden komen erbij, met de vakjes en de ballonnen. In elk leeg vakje staat klein wat erin moet komen (alleen op het scherm, niet in de PDF).",
   "Het plan wordt in je strip bewaard. Met <b>Bewaren en sluiten</b> schrijf je later verder."])
H("10. Klaar voor de drukker (knop Drukker)")
L(["Wil je je strip echt laten drukken, bij een drukker of print-on-demand? Dan maakt DraveComic twee PDF's: het <b>binnenwerk</b> en de <b>kaft</b>.",
   "Kies het <b>formaat</b> (A4, B5 of A5). De <b>afloop</b> is het randje dat na het drukken wordt afgesneden (meestal 3 mm).",
   "De <b>rug</b> rekent DraveComic zelf uit: aantal bladzijden en de dikte van één vel papier (gewoon papier is ongeveer 0,1 mm). Je drukker weet het precies.",
   "Drukkers willen vaak een <b>veelvoud van 4</b> bladzijden: zet <b>Aanvullen met lege bladzijden</b> aan.",
   "De kaft is achterkant + rug + voorkant op één vel. Maak dus eerst een <b>📕 Voorkant</b> en een <b>📗 Achterkant</b>. Je kunt de titel op de rug zetten en de kleur van de rug kiezen.",
   "<b>Snijtekens</b>: de meeste print-on-demand wil ze niet, een gewone drukker soms wel. Lees altijd even de <i>aanleverspecificaties</i> van je drukker."])
H("11. Opslaan")
L(["<b>📕 PDF</b> zet het hele boek in één PDF op A4: om te printen of te delen. Lijnen, ballonnen en letters blijven scherp.",
   "<b>📖 Bladeren</b> laat je boek groot op het scherm zien. Blader met ◀ ▶, de pijltjestoetsen, het muiswiel of een klik links/rechts. Met <b>Twee naast elkaar</b> (of <b>Spatie</b>) zie je twee bladzijden naast elkaar, net als een echt boek. Sluiten doe je met het grote <b>✕</b> rechtsboven, de knop <b>Sluiten</b> of <b>Esc</b>.",
   "<b>Opslaan</b> bewaart je hele strip in één bestand (.dcomic), met de plaatjes erin. Standaard in de map DraveComic-data\\Mijn strips naast de app.",
   "<b>Openen</b> opent een strip weer. <b>📷 Plaatje</b> bewaart de gekozen bladzijde, of alle bladzijden, als PNG (2480 × 3507, A4 op 300 dpi)."])
H("12. Toetsen")
tb = Table([["Ctrl + Z", "Ongedaan maken"], ["Ctrl + Y", "Opnieuw"], ["Ctrl + S", "Opslaan"], ["Ctrl + O", "Openen"],
            ["Delete", "Gekozen vakje weghalen"], ["Muiswiel", "Zoomen in een plaatje (bij Tekenen: dikte; bij Achtergrond: je eigen plaatje)"], ["[  en  ]", "Lijn dunner / dikker"], ["A− / A+", "Tekst in de app kleiner / groter"], ["Bladeren: ◀ ▶ / Spatie / Esc", "Bladeren / twee naast elkaar / sluiten"]],
           colWidths=[4.5 * cm, 11 * cm])
tb.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "D", 14), ("FONT", (0, 0), (0, -1), "DB", 14),
                        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#b9b2d6")), ("BACKGROUND", (0, 0), (0, -1), HexColor("#efeafd")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
E_.append(tb)
E_.append(Spacer(1, 12))
B("Vragen of ideeën? service@dravenlock.nl · dravenlock.nl")
B("Letters: Comic Neue en Bangers, vrij te gebruiken onder de SIL Open Font License (zie de map assets\\fonts).")
SimpleDocTemplate("DraveComic-Snelgids.pdf", pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                  bottomMargin=1.8 * cm, title="DraveComic snelgids", author="Dravenlock (Roger & Claudio)").build(E_)
print("snelgids klaar")
