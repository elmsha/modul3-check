# Modul-3-Atlas

Für Anbieter von dynamischen Stromtarifen und Energiemanagement-Systemen: Was sind dynamischer Tarif, intelligente Steuerung und §14a-Netzentgelte (Modul 1 + 3) je Netzgebiet für einen Haushalt wert – und wie muss die Steuerung mit zwei Preissignalen umgehen?

**App:** [zwei-signale.streamlit.app](https://zwei-signale.streamlit.app) · **Hintergrund:** [WHITEPAPER.md](WHITEPAPER.md)

## Was die App zeigt

| Reiter | Inhalt |
|---|---|
| Wo lohnt es sich? | Ersparnis je Netzgebiet und Kundentyp, zerlegt in Modul 1, Steuerung und Modul 3 |
| Kundenrechner | Ersparnis für einen konkreten Haushalt inkl. Textbaustein für Angebot oder Produktseite |
| Signale & Steuerung | Zeitfenster aller Netzbetreiber, Widersprüche zwischen Börse und Netz, Mehrwert netzbewusster Steuerung |
| Daten & Fahrpläne | Netzentgelt-Fahrplan je Viertelstunde als CSV, Rohdaten mit Quellen und Prüfstatus |

## Dateien

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `.streamlit/config.toml` | Farbschema (dunkles Theme) |
| `benchmark.py` | Wert-Zerlegung, Markt-Fit, Regel-Check, Fahrpläne |
| `modell.py` | Haushaltssimulation (E-Auto, Wärmepumpe, Steuerung, Kosten) |
| `tarif_check.py` | Laden der Börsen- und Wetterdaten (mit Cache) |
| `netzbetreiber.json` | **Datenbasis:** Modul-3-Fenster, Preise, Quartale, Quellen |
| `preise_*.json`, `wetter_*.json` | zwischengespeicherte Markt- und Wetterdaten |

## Lokal starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Netzbetreiber ergänzen oder korrigieren

Einen Eintrag in `netzbetreiber.json` hinzufügen (Preise netto in ct/kWh, Fenster als `["HH:MM", "HH:MM"]`, Fenster über Mitternacht in zwei Teile aufteilen, `quartale` = Quartale mit HT/NT). Die App rechnet alles Weitere automatisch. Hinweise und Korrekturen sind willkommen.

## Datenquellen

Day-Ahead-Preise: [Energy-Charts](https://api.energy-charts.info/) (Fraunhofer ISE; Daten Bundesnetzagentur/SMARD, CC BY 4.0) · Wetter: [Open-Meteo](https://open-meteo.com/) (CC BY 4.0) · Netzentgelte: Preisblätter der Netzbetreiber, teils über Sekundärquellen (Prüfstatus je Eintrag in `netzbetreiber.json`).
