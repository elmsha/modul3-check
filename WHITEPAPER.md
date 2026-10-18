# Modul-3-Atlas – Whitepaper

**Was dynamischer Tarif, intelligente Steuerung und §14a-Netzentgelte je Netzgebiet für Haushalte wert sind – ein Vergleich von zwölf Verteilnetzbetreibern für Tarif- und Energiemanagement-Anbieter**

*Elmar Hackmann, Oldenburg · Oktober 2026 · Prototyp · App: [zwei-signale.streamlit.app](https://zwei-signale.streamlit.app) · Code & Daten: [github.com/elmsha/modul3-check](https://github.com/elmsha/modul3-check)*

---

## Kurzfassung

Seit April 2025 bieten Verteilnetzbetreiber für Wärmepumpen und Wallboxen ein zeitvariables Netzentgelt an (§14a EnWG, Modul 3). Jeder Netzbetreiber legt selbst fest, wann Hochtarif (HT) und Niedertarif (NT) gelten. Eine zentrale, vergleichende Übersicht dieser Designs gibt es bisher nicht.

Der Modul-3-Atlas vergleicht die Preisblätter 2026 von zwölf Netzbetreibern und bewertet sie in drei Dimensionen: **Regelkonformität** nach BDEW-Anwendungshilfe, **Markt-Fit** gegenüber dem Day-Ahead-Börsenpreis (Oktober 2025 – September 2026) und **Kundennutzen** für zwei typische Haushalte.

**Für Anbieter von dynamischen Tarifen und Energiemanagement-Systemen (HEMS)** heißt das konkret:

- **Das Netzgebiet bestimmt das Werteversprechen.** Ein Haushalt mit Wärmepumpe und E-Auto spart mit dynamischem Tarif, Steuerung und §14a (Modul 1 + 3) gegenüber einem ungesteuerten dynamischen Tarif zwischen **314 € (Bayernwerk) und 762 € (Westnetz)** pro Jahr – bei identischen Börsenpreisen.
- **Modul 3 ist nicht überall eine gute Empfehlung.** In drei der zwölf Netzgebiete (Bayernwerk, LEW, Netze BW) bringt Modul 3 einem Pendler-Haushalt kaum etwas oder kostet sogar; dort ist Modul 1 allein die bessere Empfehlung.
- **Netzbewusste Steuerung ist ein messbarer Produktvorteil.** Wer auf Börsenpreis *und* Netzentgelt optimiert statt nur auf den Börsenpreis, holt je nach Netzgebiet 15–130 € pro Haushalt und Jahr zusätzlich heraus.

Die Befunde im Einzelnen:

1. **Zwei Design-Philosophien.** Acht der zwölf Netzbetreiber legen den Niedertarif in die Nacht, vier ganz oder teilweise auf den Mittag. Vier wenden HT und NT nur saisonal an. Beim Hochtarif sind sich fast alle einig: später Nachmittag bis Abend.
2. **Das Hochtarif-Signal passt, das Niedertarif-Signal oft nicht.** Hochtarif-Fenster treffen die teuersten Börsenzeiten meist zwei- bis dreimal so oft wie per Zufall (Median 2,4). Ganzjährige Nacht-Niedertarife treffen im Sommer dagegen fast keine der billigsten Börsenzeiten (Lift ≈ 0,1). Der günstigste Strom fällt dann mittags an, wenn Photovoltaik einspeist.
3. **Markt-Fit und Kundennutzen stehen in einem Zielkonflikt.** Mittags-Niedertarife passen am besten zum Markt, bringen aber Pendler-Haushalten, deren E-Auto mittags nicht zu Hause ist, kaum etwas. Nacht-Niedertarife sind für diese Haushalte attraktiv, passen aber im Sommer nicht zum Markt.
4. **Hybride Designs lösen den Konflikt teilweise auf.** Ein Niedertarif nachts *und* mittags (unter den erfassten nur bei N-ERGIE Netz) erreicht einen mittleren Markt-Fit und ist für beide Haushaltstypen attraktiv. Beispielrechnung für EWE NETZ: Ein zusätzliches NT-Fenster 11–15 Uhr hebt den Markt-Fit von 0,27 auf 0,46 und den Kundennutzen von 101 auf 140 € (Pendler) bzw. von 66 auf 156 € (Haushalt mit tagsüber verfügbarem E-Auto) – regelkonform.

**Einordnung:** Netzbetreiber legen Modul-3-Fenster nach ihrer lokalen Netzlast fest, nicht nach dem Strommarkt. Der Markt-Fit ist daher kein Maßstab für richtig oder falsch, sondern eine zusätzliche Perspektive: Er zeigt, ob das Netzsignal Flexibilität in Stunden lenkt, in denen Strom ohnehin im Überfluss vorhanden ist. In PV-starken ländlichen Netzen kann ein Mittags-Niedertarif zudem auch netzseitig sinnvoll sein, weil er Verbrauch in Stunden hoher Einspeisung legt. Das muss jeder Netzbetreiber mit seinen Lastdaten prüfen.

---

## 1. Hintergrund

### 1.1 §14a EnWG und die drei Module

Wärmepumpen und Wallboxen bringen viel zusätzliche Last ins Niederspannungsnetz. §14a EnWG und die Festlegungen der Bundesnetzagentur (BK6-22-300, BK8-22/010-A) erlauben Netzbetreibern seit 2024, solche „steuerbaren Verbrauchseinrichtungen“ bei drohender Überlastung auf eine Mindestleistung zu drosseln. Im Gegenzug sinkt das Netzentgelt:

| Modul | Inhalt |
|---|---|
| **Modul 1** | pauschale Reduzierung pro Jahr (Standard) |
| **Modul 2** | prozentuale Reduzierung des Arbeitspreises, separater Zähler |
| **Modul 3** | zusätzlich zu Modul 1: zeitvariables Netzentgelt mit Hochtarif (HT), Standardtarif (ST) und Niedertarif (NT), seit 1. April 2025 |

### 1.2 Vorgaben für Modul 3

Nach der [BDEW-Anwendungshilfe Modul 3 (V1.2, Juli 2026)](https://www.bdew.de/media/documents/2026-07-17_BDEW-Anwendungshilfe_Modul-3_V1.2.pdf) gilt unter anderem:

- Fenster und Preise gelten für ein Kalenderjahr und das ganze Netzgebiet; die Anwendung kann auf einzelne Quartale beschränkt werden, mindestens aber zwei.
- Fenster und Preisstufen sind in allen Quartalen mit HT/NT gleich.
- Der Standardtarif entspricht dem normalen Arbeitspreis für Haushalte (SLP).
- NT liegt zwischen 10 % und 40 % des ST, HT höchstens bei 200 % des ST.
- Das HT-Fenster umfasst mindestens zwei Stunden pro Tag.
- Grundlage sind energiewirtschaftliche Ansätze wie gemessene Hoch- und Niedriglastzeiten im eigenen Netz.
- Veröffentlichung im vorläufigen Preisblatt bis spätestens 15. Oktober für das Folgejahr.

Die Bundesnetzagentur hat im Mai 2026 Vollstreckungsverfahren gegen zwei Netzbetreiber eingeleitet, die Modul 3 nicht oder unzureichend umsetzen; weitere sollen folgen ([Pressemitteilung](https://bundesnetzagentur.de/SharedDocs/Pressemitteilungen/DE/2026/20260528_14a.html)).

### 1.3 Warum der Strommarkt eine Rolle spielt

Am Day-Ahead-Markt wird seit Oktober 2025 jede Viertelstunde einzeln gehandelt. Wind und Sonne haben Grenzkosten nahe null; liefern sie viel, sinkt der Preis (Merit Order). Mit dem PV-Ausbau liegt das Preistal von Frühjahr bis Herbst mittags, im Winter eher nachts.

Haushalte mit dynamischem Stromtarif (seit 2025 von allen Lieferanten anzubieten, §41a EnWG) sehen beide Signale gleichzeitig: Börsenpreis und Netzentgelt. Eine Wallbox oder Wärmepumpe kann ihren Verbrauch aber nur einmal verschieben. Zeigen beide Signale in unterschiedliche Richtungen, schwächt das die Wirkung beider.

### 1.4 Datenlage

Es gibt keine zentrale Datenbank der Modul-3-Fenster. Netzbetreiber veröffentlichen Preisblätter einzeln, meist als PDF. Die dena beschreibt den Datenaustausch rund um zeitvariable Netzentgelte als Engpass und schlägt einen Datenraum vor ([dena 2026](https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2026/Datenraum_als_Enabler_variabler_Netzentgelte.pdf)). Verbraucherportale wie [14a-atlas.de](https://www.14a-atlas.de/) und [energiemarie.de](https://energiemarie.de/) bereiten die Daten für Haushalte auf. Ein Vergleich aus Sicht der Netzbetreiber – mit Marktabgleich und Designvarianten – fehlt bisher.

---

## 2. Methodik

### 2.1 Daten

| Daten | Quelle | Zeitraum |
|---|---|---|
| Modul-3-Fenster, Preise, Quartale | Preisblätter 2026 der Netzbetreiber; teils über Sekundärquellen (siehe Tabelle 3) | 2026 |
| Day-Ahead-Preise DE-LU, 15 Minuten | [Energy-Charts](https://api.energy-charts.info/) (Fraunhofer ISE; Daten Bundesnetzagentur/SMARD, CC BY 4.0) | Okt 2025 – Sep 2026 |
| Außentemperatur Oldenburg, stündlich | [Open-Meteo](https://open-meteo.com/) (CC BY 4.0) | Okt 2025 – Sep 2026 |

Für alle Netzgebiete werden dieselben Börsenpreise verwendet (eine Gebotszone). Die Netzentgelte 2026 werden auf den gesamten Analysezeitraum angewendet.

### 2.2 Kennzahlen

**Regel-Check.** NT 10–40 % von ST, HT ≤ 200 % von ST, HT ≥ 2 h/Tag, mindestens zwei Quartale, keine Überschneidung von HT und NT. Toleranz 0,5 Prozentpunkte für Rundungseffekte bei aus Bruttowerten umgerechneten Preisen.

**Markt-Fit.** Für jeden Tag, an dem HT/NT gelten, wird die Pearson-Korrelation zwischen Netzentgelt und Börsenpreis über die 96 Viertelstunden berechnet und über alle Tage gemittelt. +1 bedeutet: Das Netzentgelt ist genau dann hoch (niedrig), wann der Börsenpreis hoch (niedrig) ist. 0 bedeutet: kein Zusammenhang. Getrennt ausgewiesen für Sommer (Q2/Q3) und Winter (Q1/Q4).

**Lift HT / Lift NT.** Anteil der teuersten (billigsten) 25 % Börsen-Viertelstunden eines Tages, die im HT- (NT-)Fenster liegen, geteilt durch den Zeitanteil des Fensters. 1,0 entspricht dem Zufall.

**Kundennutzen.** Simulation eines Haushalts mit 3.000 kWh Haushaltsstrom, E-Auto (2.500 kWh/Jahr, 11 kW) und Wärmepumpe (4.000 kWh/Jahr, Wärmebedarf aus der Außentemperatur, temperaturabhängiger COP, 30 % der Tageswärme verschiebbar). Verglichen werden zwei Varianten mit dynamischem Stromtarif:

- **C:** Modul 1, Steuerung nach Börsenpreis
- **E:** Modul 1 + 3, Steuerung nach Börsenpreis + Netzentgelt

Der Kundennutzen ist die Differenz C − E in €/Jahr brutto. Zwei Profile:

- **Pendler:** E-Auto werktags 18–7 Uhr an der Wallbox
- **Zuhause:** E-Auto tagsüber verfügbar (Homeoffice, Zweitwagen)

Die Day-Ahead-Preise sind zum Zeitpunkt der Ladeentscheidung bekannt; es wird keine unrealistische Voraussicht unterstellt.

### 2.3 Wert-Zerlegung, Kundenrechner und Fahrpläne

Für die Anbieter-Sicht wird die Ersparnis gegenüber einem dynamischen Tarif ohne Steuerung und ohne §14a in drei Bausteine zerlegt: **Modul 1** (pauschale Gutschrift, brutto), **Steuerung** (Variante B → C) und **Modul 3** (C → E). Der **Mehrwert netzbewusster Steuerung** ist D → E: Modul 3 ist gewählt, die Steuerung kennt aber entweder nur den Börsenpreis (D) oder Börse und Netzentgelt (E). Die App rechnet dies für vier Kundentypen und erlaubt im Kundenrechner eigene Haushaltsparameter. Zusätzlich lassen sich je Netzbetreiber **Netzentgelt-Fahrpläne** (Tarifstufe und Preis je Viertelstunde eines Jahres) als CSV exportieren.

## 3. Ergebnisse

### 3.1 Übersicht

| Netzbetreiber | Design | Geltung | Markt-Fit | Sommer | Winter | Lift HT | Lift NT | Nutzen Pendler | Nutzen Zuhause |
|---|---|---|---|---|---|---|---|---|---|
| Bayernwerk Netz | Mittags-NT | Q2/Q3 | 0,67 | 0,67 | – | 2,5 | 3,4 | −17 € | 58 € |
| LEW Verteilnetz | Mittags-NT | ganzjährig | 0,52 | 0,62 | 0,42 | 2,5 | 2,3 | 1 € | 104 € |
| Avacon Netz | Nacht-NT | Q1/Q4 | 0,50 | – | 0,50 | 2,8 | 2,0 | 161 € | 144 € |
| Netze BW | Mittags-NT | ganzjährig | 0,49 | 0,61 | 0,37 | 2,4 | 2,3 | 5 € | 128 € |
| E.DIS Netz | Nacht-NT | Q1/Q4 | 0,47 | – | 0,47 | 2,2 | 2,1 | 125 € | 109 € |
| N-ERGIE Netz | Hybrid | ganzjährig | 0,43 | 0,32 | 0,54 | 2,7 | 1,4 | 147 € | 165 € |
| Schleswig-Holstein Netz | Nacht-NT | Q1/Q4 | 0,38 | – | 0,38 | 1,5 | 1,8 | 174 € | 155 € |
| Stromnetz Berlin | Nacht-NT | ganzjährig | 0,28 | −0,01 | 0,57 | 2,6 | 0,9 | 201 € | 139 € |
| EWE NETZ | Nacht-NT | ganzjährig | 0,27 | −0,01 | 0,55 | 2,4 | 1,0 | 101 € | 66 € |
| wesernetz Bremen | Nacht-NT | ganzjährig | 0,23 | −0,03 | 0,48 | 2,3 | 1,2 | 113 € | 74 € |
| Westnetz | Nacht-NT | ganzjährig | 0,17 | −0,17 | 0,52 | 1,8 | 1,0 | 383 € | 273 € |
| SWM Infrastruktur | Nacht-NT | ganzjährig | 0,09 | −0,22 | 0,41 | 1,1 | 1,1 | 170 € | 108 € |

Alle zwölf Designs bestehen den Regel-Check. Auffällig: Fast alle setzen den Niedertarif genau an eine der beiden Grenzen – sieben auf 10 %, vier auf 40 % des Standardtarifs (einzelne Werte rundungsbedingt minimal darüber oder darunter, innerhalb der Toleranz). Nur Stromnetz Berlin liegt dazwischen (35 %).

### 3.2 Interpretation

- **Im Winter passen alle Designs ordentlich** (Markt-Fit 0,37–0,57). Abendspitze und nächtliches Preistal decken sich mit den typischen Fenstern.
- **Im Sommer trennt sich das Feld.** Ganzjährige Nacht-Niedertarife haben im Sommer einen Markt-Fit um null oder darunter. Saisonale Designs umgehen das Problem, indem sie Modul 3 im Sommer aussetzen (Avacon, E.DIS, SH Netz) oder nur im Sommer mit Mittagsfenster anwenden (Bayernwerk).
- **Die Höhe des Kundennutzens hängt stark am Preisniveau.** Westnetz erreicht den höchsten Nutzen vor allem wegen des hohen Standardtarifs (9,53 ct) und der großen Spreizung, nicht wegen des Fensterdesigns.
- **Ein Mittags-Niedertarif kann für Pendler sogar nachteilig sein.** Bei Bayernwerk zahlt der Pendler-Haushalt mit Modul 3 etwas mehr: Das E-Auto kann den Mittags-NT nicht nutzen, und der unflexible Haushaltsstrom fällt teilweise in den Abend-HT. Für die Annahmequote von Modul 3 ist das relevant.

### 3.3 Designvariante EWE NETZ

| Variante | Markt-Fit | Sommer | Winter | Nutzen Pendler | Nutzen Zuhause |
|---|---|---|---|---|---|
| Original (NT 23–5 Uhr) | 0,27 | −0,01 | 0,55 | 101 € | 66 € |
| + NT 12–14 Uhr | 0,38 | 0,18 | 0,58 | 125 € | 139 € |
| + NT 11–15 Uhr | 0,46 | 0,33 | 0,59 | 140 € | 156 € |
| nur NT 11–15 Uhr | 0,50 | 0,56 | 0,45 | 4 € | 82 € |

Die hybride Variante verbessert Markt-Fit und Kundennutzen gleichzeitig. Offen ist die netzseitige Wirkung: Ob zusätzliche Mittagslast im EWE-Netz entlastet (hohe PV-Einspeisung) oder belastet, lässt sich nur mit Netzlastdaten beurteilen. Höherer Kundennutzen bedeutet zudem geringere Netzentgelterlöse aus diesen Kunden, die über die Kalkulation der übrigen Entgelte ausgeglichen werden müssten.

### 3.4 Anbieter-Sicht: Wert des Smart-Pakets je Netzgebiet

Ersparnis pro Jahr (brutto) gegenüber einem dynamischen Tarif ohne Steuerung und ohne §14a, zerlegt in Modul 1 (pauschale Gutschrift), Steuerung nach Börsenpreis und Modul 3. Kundentyp: Wärmepumpe + Pendler-E-Auto.

| Netzbetreiber | Modul 1 | Steuerung | Modul 3 | **Gesamt** | Mehrwert netzbewusste Steuerung |
|---|---|---|---|---|---|
| Westnetz | 165 € | 213 € | 383 € | **762 €** | 130 € |
| Stromnetz Berlin | 147 € | 212 € | 201 € | **559 €** | 68 € |
| Schleswig-Holstein Netz | 137 € | 211 € | 174 € | **522 €** | 42 € |
| SWM Infrastruktur | 138 € | 211 € | 170 € | **518 €** | 41 € |
| Avacon Netz | 134 € | 211 € | 161 € | **505 €** | 37 € |
| N-ERGIE Netz | 133 € | 211 € | 147 € | **491 €** | 59 € |
| E.DIS Netz | 129 € | 210 € | 125 € | **464 €** | 34 € |
| wesernetz Bremen | 129 € | 210 € | 113 € | **452 €** | 55 € |
| EWE NETZ | 109 € | 208 € | 101 € | **418 €** | 38 € |
| Netze BW | 148 € | 212 € | 5 € | **365 €** | 35 € |
| LEW Verteilnetz | 117 € | 209 € | 1 € | **326 €** | 27 € |
| Bayernwerk Netz | 122 € | 210 € | −17 € | **314 €** | 15 € |

Gesamtersparnis nach Kundentyp:

| Netzbetreiber | Wärmepumpe | E-Auto (Pendler) | E-Auto (tagsüber zu Hause) | WP + E-Auto |
|---|---|---|---|---|
| Westnetz | 398 € | 533 € | 579 € | 762 € |
| Stromnetz Berlin | 306 € | 390 € | 484 € | 559 € |
| Schleswig-Holstein Netz | 310 € | 356 € | 493 € | 522 € |
| SWM Infrastruktur | 291 € | 379 € | 473 € | 518 € |
| Avacon Netz | 298 € | 346 € | 485 € | 505 € |
| N-ERGIE Netz | 276 € | 335 € | 509 € | 491 € |
| E.DIS Netz | 264 € | 325 € | 465 € | 464 € |
| wesernetz Bremen | 247 € | 333 € | 450 € | 452 € |
| EWE NETZ | 221 € | 298 € | 420 € | 418 € |
| Netze BW | 248 € | 242 € | 521 € | 365 € |
| LEW Verteilnetz | 210 € | 210 € | 469 € | 326 € |
| Bayernwerk Netz | 198 € | 223 € | 454 € | 314 € |

Lesart für Anbieter: Die Steuerung nach Börsenpreis ist überall ähnlich viel wert, weil alle Gebiete in derselben Gebotszone liegen. Die Unterschiede entstehen über Modul 1 und vor allem Modul 3. In Gebieten mit Mittags-Niedertarif hängt der Wert stark davon ab, ob das E-Auto tagsüber verfügbar ist – Kundensegmentierung (Pendler vs. Homeoffice/Zweitwagen) ist dort entscheidend für das Versprechen.

**Für die Steuerungslogik:** Ganzjährige Nacht-Niedertarife decken im Sommer 98–100 % der billigsten Börsen-Viertelstunden *nicht* ab; bei SWM Infrastruktur widersprechen sich Börse und Netz wegen des langen Hochtarif-Fensters (8:30–20:45 Uhr) in 18 % aller Viertelstunden direkt. Eine Optimierung auf den Endpreis je Viertelstunde (Börse + Netzentgelt-Stufe + Umlagen) statt auf ein Einzelsignal ist deshalb Pflicht.

---

## 4. Grenzen

- **Datenqualität.** Fünf Preisblätter wurden gegen das Original geprüft, sieben stammen aus Sekundärquellen (Bruttowerte, durch 1,19 geteilt). Bei Bayernwerk wich eine Sekundärquelle bei den Quartalen vom Original ab; die Prüfstufe ist je Netzbetreiber ausgewiesen.
- **Markt-Fit ist nicht der gesetzliche Maßstab.** Die Netzlast, nach der Netzbetreiber planen, ist öffentlich nicht verfügbar und nicht Teil der Analyse.
- **Typisierte Lastprofile** statt Messdaten; Flexibilität der Wärmepumpe gesetzt; Wetter nur für Oldenburg.
- **Netzentgelte 2026** auf den Zeitraum Okt 2025 – Sep 2026 angewendet.
- Modul 3 wird für den gesamten Zähler angenommen.
- Hamburger Energienetze und MITNETZ sind nicht enthalten: Eine Sekundärquelle gibt an, dass dort Modul 3 noch nicht angeboten wird; das ist nicht verifiziert.
- Keine Rechts-, Tarif- oder Anlageberatung.

## 5. Ausblick

- **Preisblätter 2027** (vorläufig seit 15.10.2026) erfassen und die Veränderung gegenüber 2026 auswerten.
- Abdeckung auf 30–50 Netzbetreiber erweitern, Prüfung gegen Originalpreisblätter vervollständigen.
- Netzseitige Perspektive ergänzen: PV-Dichte und Einspeiseprofile je Netzgebiet als Indikator, ob Mittagsfenster netzdienlich sind.
- Gespräche mit Tarif- und HEMS-Anbietern: Welche Netzgebiete priorisieren sie, wie kommunizieren sie Ersparnisse, und welche Daten fehlen ihnen in der Steuerung?
- Fahrpläne als API bereitstellen und um 2027 sowie weitere Netzbetreiber erweitern.

---

## Quellen

- [BDEW-Anwendungshilfe Modul 3, V1.2 (17.07.2026)](https://www.bdew.de/media/documents/2026-07-17_BDEW-Anwendungshilfe_Modul-3_V1.2.pdf)
- [Bundesnetzagentur: Pressemitteilung zu §14a, 28.05.2026](https://bundesnetzagentur.de/SharedDocs/Pressemitteilungen/DE/2026/20260528_14a.html)
- [dena: Datenraum als Enabler variabler Netzentgelte (2026)](https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2026/Datenraum_als_Enabler_variabler_Netzentgelte.pdf)
- [ZfK: Zeitvariable Netzentgelte – Modul 3 in den Preisblättern 2026](https://www.zfk.de/politik/regulierung/zeitvariable-netzentgelte-modul-3-netzbetreiber)
- Preisblätter der Netzbetreiber und Sekundärquellen: siehe `netzbetreiber.json` bzw. Reiter „Daten & Methodik“ der App
- [Energy-Charts API](https://api.energy-charts.info/), Fraunhofer ISE; Daten Bundesnetzagentur/SMARD, CC BY 4.0
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), CC BY 4.0
