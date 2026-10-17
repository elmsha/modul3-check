# Tarif-Check: Dynamischer Tarif + §14a Modul 3 (EWE NETZ)

**Frage:** Was spart ein Haushalt mit E-Auto und/oder Wärmepumpe im Netzgebiet EWE NETZ, wenn er zum dynamischen Stromtarif zusätzlich das zeitvariable Netzentgelt (Modul 3) wählt? Und wie oft widersprechen sich Börsen- und Netzpreissignal?

## Starten

```bash
pip install -r requirements.txt
python tarif_check.py
```

Beim ersten Lauf werden 12 Monate Day-Ahead-Preise von Energy-Charts geladen sowie das Wetter für Oldenburg (ca. 1 Minute) und im Ordner `cache/` gespeichert. Danach läuft alles offline in wenigen Sekunden.

Das Ergebnis landet in `ergebnis/`: `bericht.html` zum Öffnen im Browser, dazu CSV-Tabellen und Grafiken.

## Die fünf Varianten

| | Tarif | Steuerung | Netzentgelt |
|---|---|---|---|
| A | Festpreis | keine | Modul 1 |
| B | Dynamisch | keine (Laden sofort, WP gleichmäßig) | Modul 1 |
| C | Dynamisch | nach Börsenpreis | Modul 1 |
| D | Dynamisch | nach Börsenpreis, abgerechnet mit Modul 3 | Modul 1+3 |
| E | Dynamisch | nach Börse + Netzentgelt | Modul 1+3 |

Die Kernzahl ist **C → E**: der Zusatznutzen von Modul 3, wenn die Steuerung beide Signale kennt. **C → D** zeigt, was passiert, wenn man Modul 3 wählt, die Wallbox aber weiter nur auf die Börse schaut.

## Annahmen (alle oben im Skript änderbar)

- **Netzentgelte:** Preisblatt EWE NETZ 2026, netto. Arbeitspreis 3,20 ct/kWh. Modul 3: HT 5,62 ct (16:30–20:30), ST 3,20 ct, NT 0,32 ct (23:00–05:00), ganzjährig. Modul 1: −91,23 €/a.
- **Unsicher:** Das Preisblatt nennt für Modul 3 zusätzlich eine Zeile mit 1,35 ct/kWh, deren Bedeutung aus dem Dokument nicht eindeutig hervorgeht. Ich habe angenommen, dass Modul 3 für den ganzen Zähler gilt, also auch für den Haushaltsstrom. Beides bei EWE NETZ verifizieren.
- **Übrige Bestandteile** (Stromsteuer, Umlagen, Konzessionsabgabe, Anbieter-Marge) sind grob gesetzt. Sie verändern die Ersparnis nicht, nur das Kostenniveau.
- **E-Auto:** 2.500 kWh/a, steht 18–7 Uhr an der Wallbox, 11 kW. Die Day-Ahead-Preise der Nacht sind um 18 Uhr bekannt, also keine unrealistische Voraussicht.
- **Wärmepumpe:** Der Wärmebedarf kommt aus der stündlichen Außentemperatur in Oldenburg ([Open-Meteo-Archiv](https://open-meteo.com/en/docs/historical-weather-api)): Heizgradstunden unter 15 °C plus 15 % Warmwasser. Der COP hängt von der Außentemperatur ab (Gütegrad 0,45 × Carnot, Vorlauf 35 °C). Kalibriert auf 4.000 kWh Strom im ungesteuerten Betrieb.
- **WP-Steuerung:** 30 % der Tageswärme lassen sich verschieben, und zwar in die Viertelstunden, in denen eine kWh *Wärme* am billigsten ist (Preis ÷ COP). Deshalb ändert sich der Jahresstromverbrauch je Variante leicht. Die 30 % bleiben die wichtigste Annahme; sie hängen von Pufferspeicher und Gebäude ab.
- Smart Meter (iMSys) wird vorausgesetzt. Ohne ihn gibt es weder dynamischen Tarif noch Modul 3.

## Ideen zum Weiterbauen (gute Vibe-Coding-Übungen)

1. Szenario-Schleife: `WP_FLEX_ANTEIL` von 0 bis 60 % durchlaufen und die Ersparnis als Kurve zeichnen.
2. Vorlauftemperatur auf 50 °C setzen (Altbau mit Heizkörpern) und vergleichen.
3. Ein zweites Netzgebiet zum Vergleich anlegen, etwa Westnetz oder Avacon.
4. Heimspeicher ergänzen, der Netz- und Börsensignal gleichzeitig ausnutzt.

**Datenquellen:** [Energy-Charts API](https://api.energy-charts.info/) (Fraunhofer ISE), Daten Bundesnetzagentur/SMARD, CC BY 4.0; Wetter: [Open-Meteo](https://open-meteo.com/), CC BY 4.0.
