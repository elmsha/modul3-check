"""
Tarif-Check: Dynamischer Stromtarif + zeitvariables Netzentgelt (§14a EnWG, Modul 3)
Netzgebiet: EWE NETZ (Preisblatt Netzentgelte Strom 2026)

Frage: Was spart ein Haushalt mit E-Auto und/oder Wärmepumpe, wenn er zusätzlich
zum dynamischen Tarif Modul 3 wählt – und wo widersprechen sich Börsen- und
Netzpreissignal?

Start:   pip install requests pandas matplotlib
         python tarif_check.py
Ergebnis: Ordner ./ergebnis mit Tabelle (CSV), Grafiken (PNG) und bericht.html
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

# =============================================================================
# 1) ANNAHMEN – hier drehen
# =============================================================================

ZEITRAUM_START = "2025-10-01"   # erste 12 Monate mit 15-Minuten-Day-Ahead
ZEITRAUM_ENDE  = "2026-09-30"
ZEITZONE = "Europe/Berlin"

# --- EWE NETZ Preisblatt 2026, Niederspannung, netto -------------------------
NETZ_AP_STANDARD_CT = 3.20      # ct/kWh, normaler Arbeitspreis (= Standardlaststufe)
NETZ_GP_EUR_A       = 102.00    # €/a Grundpreis
MODUL1_EUR_A        = -91.23    # €/a pauschale Reduzierung (Grundvoraussetzung für Modul 3)
MODUL3_STUFEN_CT = {            # zeitvariabel, nur zusammen mit Modul 1
    "HT": 5.62,                 # Hochlast 16:30–20:30
    "ST": 3.20,                 # Standard, übrige Zeit
    "NT": 0.32,                 # Niedriglast 23:00–05:00
}
MODUL3_FENSTER = {              # (Start, Ende) in lokaler Uhrzeit, Minuten seit 0:00
    "HT": [(16 * 60 + 30, 20 * 60 + 30)],
    "NT": [(23 * 60, 24 * 60), (0, 5 * 60)],
}

# --- Übrige Preisbestandteile (Annahmen, netto ct/kWh) -----------------------
# Konstante Bestandteile ändern die ERSPARNIS nicht, nur das absolute Niveau.
STROMSTEUER_CT      = 2.05
UMLAGEN_CT          = 2.95      # KWKG + Offshore + §19 StromNEV, grob – bitte prüfen
KONZESSION_CT       = 1.99      # Gemeinden 100–500 Tsd. Einwohner (Oldenburg)
LIEFERANT_AUFSCHLAG_CT = 2.00   # Marge dynamischer Anbieter (+ ggf. Monatsgebühr)
MWST = 0.19

# Vergleich: klassischer Festpreistarif, brutto inkl. aller Bestandteile
FESTPREIS_BRUTTO_CT = 30.0

# --- Lasten ------------------------------------------------------------------
HAUSHALT_KWH_A = 3000           # unflexibel, hängt bei Modul 3 mit am selben Zähler

EAUTO_KWH_A        = 2500       # ~15.000 km
EAUTO_LADELEISTUNG_KW = 11.0
EAUTO_ANKUNFT_H    = 18         # Auto steht ab 18 Uhr ...
EAUTO_ABFAHRT_H    = 7          # ... bis 7 Uhr am Folgetag an der Wallbox

WP_KWH_A           = 4000       # Strom der Wärmepumpe pro Jahr bei ungesteuertem Betrieb (Kalibrierung)
WP_MAX_KW          = 3.0        # elektrische Maximalleistung
WP_FLEX_ANTEIL     = 0.30       # Anteil der täglichen WÄRME, die sich im Tag verschieben lässt
                                # (Pufferspeicher, Estrich, Warmwasserspeicher)
HEIZGRENZE_C       = 15.0       # oberhalb dieser Außentemperatur wird nicht geheizt
WARMWASSER_ANTEIL  = 0.15       # Anteil der Jahreswärme für Warmwasser (temperaturunabhängig)
VORLAUF_C          = 35.0       # Vorlauftemperatur Heizung (Fußbodenheizung ~35, Heizkörper ~50)
GUETEGRAD          = 0.45       # realer COP / theoretischer Carnot-COP
STANDORT = {"name": "Oldenburg", "lat": 53.14, "lon": 8.21}

AUSGABE = Path("ergebnis")

# =============================================================================
# 2) DATEN: Day-Ahead-Preise von Energy-Charts (Fraunhofer ISE, CC BY 4.0)
# =============================================================================

API = "https://api.energy-charts.info/price"
CACHE = Path("cache")


def hole_json(url: str, params: dict, versuche: int = 6) -> dict:
    """GET mit Wiederholung: bei 429 (zu viele Anfragen) oder Serverfehler warten und neu versuchen."""
    for n in range(1, versuche + 1):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            warte = int(r.headers.get("Retry-After", 0) or 0) or 15 * n
            print(f"    Server bremst ({r.status_code}), warte {warte} s … (Versuch {n}/{versuche})")
            time.sleep(warte)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    raise RuntimeError(f"Keine Antwort von {url}")


def lade_preise(start: str, ende: str) -> pd.Series:
    """Day-Ahead DE-LU in €/MWh als 15-Minuten-Serie (lokale Zeit). Lädt monatsweise, cached."""
    CACHE.mkdir(exist_ok=True)
    teile = []
    for monat in pd.period_range(start, ende, freq="M"):
        datei = CACHE / f"preise_{monat}.json"
        if datei.exists():
            daten = json.loads(datei.read_text())
        else:
            von = max(pd.Timestamp(start), monat.start_time).strftime("%Y-%m-%d")
            bis = min(pd.Timestamp(ende), monat.end_time).strftime("%Y-%m-%d")
            print(f"  lade {monat} …")
            daten = hole_json(API, {"bzn": "DE-LU", "start": von, "end": bis})
            datei.write_text(json.dumps(daten))
            time.sleep(3)                       # höflich bleiben: API begrenzt Anfragen
        s = pd.Series(daten["price"],
                      index=pd.to_datetime(daten["unix_seconds"], unit="s", utc=True),
                      dtype="float64")
        teile.append(s)

    preise = pd.concat(teile)
    preise = preise[~preise.index.duplicated()].sort_index()
    # stündliche Abschnitte (falls vorhanden) auf 15 Minuten auffüllen
    preise = preise.resample("15min").ffill()
    preise = preise.tz_convert(ZEITZONE)
    return preise.loc[start:ende].rename("boerse_eur_mwh")


# =============================================================================
# 3) PREISKOMPONENTEN JE VIERTELSTUNDE
# =============================================================================

def modul3_stufe(index: pd.DatetimeIndex) -> pd.Series:
    minute = index.hour * 60 + index.minute
    stufe = pd.Series("ST", index=index)
    for name, fenster in MODUL3_FENSTER.items():
        for a, b in fenster:
            stufe[(minute >= a) & (minute < b)] = name
    return stufe


def baue_preisrahmen(boerse: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"boerse_ct": boerse / 10.0})   # €/MWh -> ct/kWh
    df["stufe"] = modul3_stufe(df.index)
    df["netz_m3_ct"] = df["stufe"].map(MODUL3_STUFEN_CT)
    df["netz_std_ct"] = NETZ_AP_STANDARD_CT
    df["datum"] = df.index.date
    df["monat"] = df.index.month
    df["minute"] = df.index.hour * 60 + df.index.minute
    return df


# =============================================================================
# 4) LASTPROFILE
# =============================================================================

def haushalt_profil(df: pd.DataFrame) -> pd.Series:
    """Einfaches Haushaltsprofil: Grundlast + Morgen- und Abendspitze."""
    h = df.index.hour + df.index.minute / 60
    form = (0.6
            + 0.6 * np.exp(-((h - 7.5) ** 2) / 2)
            + 1.2 * np.exp(-((h - 19.0) ** 2) / 4))
    form = pd.Series(form, index=df.index)
    return form / form.sum() * HAUSHALT_KWH_A


def lade_temperatur(df: pd.DataFrame) -> pd.Series:
    """Stündliche Außentemperatur (2 m) für den Standort aus dem Open-Meteo-Archiv, auf 15 min."""
    CACHE.mkdir(exist_ok=True)
    start, ende = df.index.min().date(), df.index.max().date()
    datei = CACHE / f"wetter_{STANDORT['name']}_{start}_{ende}.json"
    if datei.exists():
        daten = json.loads(datei.read_text())
    else:
        print(f"  lade Wetter {STANDORT['name']} …")
        daten = hole_json("https://archive-api.open-meteo.com/v1/archive", {
            "latitude": STANDORT["lat"], "longitude": STANDORT["lon"],
            "start_date": str(start), "end_date": str(ende),
            "hourly": "temperature_2m", "timezone": "GMT"})
        datei.write_text(json.dumps(daten))
    h = daten["hourly"]
    t = pd.Series(h["temperature_2m"], index=pd.to_datetime(h["time"], utc=True), dtype="float64")
    t = t.interpolate(limit_direction="both")          # einzelne Lücken schließen
    t = t.tz_convert(ZEITZONE).resample("15min").interpolate()
    return t.reindex(df.index, method="nearest").rename("temp_c")


def cop(temp_c: pd.Series) -> pd.Series:
    """Vereinfachter COP: Gütegrad x Carnot, mit 5 K Temperaturhub am Wärmetauscher."""
    carnot = (VORLAUF_C + 273.15) / (VORLAUF_C - temp_c + 5.0).clip(lower=5.0)
    return (GUETEGRAD * carnot).clip(1.5, 6.0)


def wp_waermebedarf(df: pd.DataFrame) -> pd.Series:
    """
    Wärmebedarf je Viertelstunde (kWh_th): Raumwärme über Heizgradstunden + konstantes Warmwasser.
    Skaliert so, dass der ungesteuerte Strombedarf genau WP_KWH_A ergibt.
    """
    raum = (HEIZGRENZE_C - df["temp_c"]).clip(lower=0)
    raum = raum / raum.sum() * (1 - WARMWASSER_ANTEIL)
    ww = pd.Series(WARMWASSER_ANTEIL / len(df), index=df.index)
    form = raum + ww                                 # Summe = 1
    strom_je_einheit = (form / df["cop"]).sum()
    return form * WP_KWH_A / strom_je_einheit


# =============================================================================
# 5) STEUERUNG: Energie in die billigsten Viertelstunden legen
# =============================================================================

def verteile_billigst(preis: np.ndarray, energie_kwh: float, max_kwh_je_slot: float) -> np.ndarray:
    """Füllt die günstigsten Slots bis zur Leistungsgrenze, bis die Energie erreicht ist."""
    last = np.zeros_like(preis)
    rest = energie_kwh
    for i in np.argsort(preis, kind="stable"):
        if rest <= 1e-9:
            break
        menge = min(max_kwh_je_slot, rest)
        last[i] = menge
        rest -= menge
    return last


def eauto_last(df: pd.DataFrame, signal: str | None) -> pd.Series:
    """
    signal=None      -> lädt sofort bei Ankunft (ungesteuert)
    signal='boerse'  -> billigste Slots nach Börsenpreis
    signal='summe'   -> billigste Slots nach Börse + Modul-3-Netzentgelt
    Day-Ahead-Preise für die Nacht sind um 18 Uhr bekannt -> keine unrealistische Voraussicht.
    """
    tage = sorted(set(df["datum"]))
    energie_tag = EAUTO_KWH_A / len(tage)
    max_slot = EAUTO_LADELEISTUNG_KW * 0.25
    last = pd.Series(0.0, index=df.index)

    for tag in tage:
        start = pd.Timestamp(tag, tz=ZEITZONE) + pd.Timedelta(hours=EAUTO_ANKUNFT_H)
        ende = pd.Timestamp(tag, tz=ZEITZONE) + pd.Timedelta(days=1, hours=EAUTO_ABFAHRT_H)
        fenster = df.loc[start:ende - pd.Timedelta(minutes=15)]
        if fenster.empty:
            continue
        if signal is None:
            preis = np.arange(len(fenster), dtype=float)          # früheste Slots zuerst
        elif signal == "boerse":
            preis = fenster["boerse_ct"].to_numpy()
        else:
            preis = (fenster["boerse_ct"] + fenster["netz_m3_ct"]).to_numpy()
        last.loc[fenster.index] += verteile_billigst(preis, energie_tag, max_slot)
    return last


def wp_last(df: pd.DataFrame, signal: str | None) -> pd.Series:
    """
    Ungesteuert: Wärme wird erzeugt, wenn sie gebraucht wird (Strom = Wärme / COP).
    Gesteuert: WP_FLEX_ANTEIL der Tageswärme wird in die Viertelstunden gelegt, in denen
    eine kWh WÄRME am billigsten ist, also Preis / COP. Warme Mittagsstunden profitieren doppelt:
    niedriger Börsenpreis (Solar) und höherer COP.
    """
    waerme = df["waerme_kwh"]
    if not signal:
        return waerme / df["cop"]
    preis = df["boerse_ct"] if signal == "boerse" else df["boerse_ct"] + df["netz_m3_ct"]
    last = pd.Series(0.0, index=df.index)
    for _, g in df.groupby("datum"):
        w = waerme.loc[g.index].to_numpy()
        c = g["cop"].to_numpy()
        fix_th = (1 - WP_FLEX_ANTEIL) * w
        fix_el = fix_th / c
        freiraum_th = np.maximum(WP_MAX_KW * 0.25 - fix_el, 0) * c
        flex_th = np.zeros_like(w)
        rest = WP_FLEX_ANTEIL * w.sum()
        for i in np.argsort(preis.loc[g.index].to_numpy() / c, kind="stable"):
            if rest <= 1e-9:
                break
            menge = min(freiraum_th[i], rest)
            flex_th[i] = menge
            rest -= menge
        last.loc[g.index] = (fix_th + flex_th) / c
    return last


# =============================================================================
# 6) KOSTEN
# =============================================================================

KONST_CT = STROMSTEUER_CT + UMLAGEN_CT + KONZESSION_CT + LIEFERANT_AUFSCHLAG_CT


def kosten_dynamisch(df: pd.DataFrame, last: pd.Series, modul3: bool) -> float:
    netz = df["netz_m3_ct"] if modul3 else df["netz_std_ct"]
    arbeit_ct = (df["boerse_ct"] + netz + KONST_CT) * last
    fix_eur = NETZ_GP_EUR_A + MODUL1_EUR_A          # Modul 1 in beiden Varianten
    return (arbeit_ct.sum() / 100 + fix_eur) * (1 + MWST)


def kosten_festpreis(last: pd.Series) -> float:
    return last.sum() * FESTPREIS_BRUTTO_CT / 100 + MODUL1_EUR_A * (1 + MWST)


@dataclass
class Fall:
    name: str
    eauto: bool
    wp: bool


FAELLE = [Fall("Nur E-Auto", True, False),
          Fall("Nur Wärmepumpe", False, True),
          Fall("E-Auto + Wärmepumpe", True, True)]


def rechne(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    haushalt = haushalt_profil(df)
    profile = {}
    zeilen = []
    for f in FAELLE:
        def gesamt(signal):
            l = haushalt.copy()
            if f.eauto:
                l += eauto_last(df, signal)
            if f.wp:
                l += wp_last(df, signal)
            return l

        ungesteuert = gesamt(None)
        nach_boerse = gesamt("boerse")
        nach_summe = gesamt("summe")
        profile[f.name] = {"ungesteuert": ungesteuert, "boerse": nach_boerse, "summe": nach_summe}

        varianten = {
            "A Festpreis (Modul 1)":                     (kosten_festpreis(ungesteuert), ungesteuert),
            "B Dynamisch, ungesteuert (Modul 1)":        (kosten_dynamisch(df, ungesteuert, False), ungesteuert),
            "C Dynamisch, Börse-gesteuert (Modul 1)":    (kosten_dynamisch(df, nach_boerse, False), nach_boerse),
            "D Dynamisch, Börse-gesteuert (Modul 1+3)":  (kosten_dynamisch(df, nach_boerse, True), nach_boerse),
            "E Dynamisch, Summen-gesteuert (Modul 1+3)": (kosten_dynamisch(df, nach_summe, True), nach_summe),
        }
        for v, (eur, last) in varianten.items():
            # kWh variiert bei der WP: Verschieben in warme Stunden hebt den COP
            zeilen.append({"Fall": f.name, "Variante": v, "Kosten €/a": round(eur, 0),
                           "kWh/a": round(last.sum())})
    tab = pd.DataFrame(zeilen)
    return tab, profile


# =============================================================================
# 7) SIGNALKONFLIKT
# =============================================================================

def konflikt_analyse(df: pd.DataFrame) -> pd.DataFrame:
    """Je Tag: Liegen die billigsten Börsen-Viertelstunden im NT-, ST- oder HT-Fenster?"""
    d = df.copy()
    d["rang"] = d.groupby("datum")["boerse_ct"].rank(pct=True)
    billig = d[d["rang"] <= 0.25]                    # billigstes Viertel des Tages
    teuer = d[d["rang"] >= 0.75]
    out = pd.DataFrame({
        "billigste 25 % Börse": billig["stufe"].value_counts(normalize=True),
        "teuerste 25 % Börse": teuer["stufe"].value_counts(normalize=True),
        "Anteil an der Zeit": d["stufe"].value_counts(normalize=True),
    }).reindex(["NT", "ST", "HT"]).fillna(0)
    return (out * 100).round(1)


# =============================================================================
# 8) GRAFIKEN + BERICHT
# =============================================================================

FARBEN = {"NT": "#2E7D6B", "ST": "#9AA5B1", "HT": "#C2553A"}


def grafik_heatmap(df: pd.DataFrame, pfad: Path):
    mittel = df.groupby(["monat", df.index.hour])["boerse_ct"].mean().unstack()
    reihenfolge = list(range(10, 13)) + list(range(1, 10))
    mittel = mittel.reindex([m for m in reihenfolge if m in mittel.index])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    im = ax.imshow(mittel.values, aspect="auto", cmap="RdYlGn_r")
    ax.set_yticks(range(len(mittel.index)))
    ax.set_yticklabels(["Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                        "Jul", "Aug", "Sep"][: len(mittel.index)] if len(mittel.index) == 12
                       else [str(m) for m in mittel.index])
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)])
    for a, b, farbe, label in [(-0.5, 4.5, FARBEN["NT"], "NT Netz"), (22.5, 23.5, FARBEN["NT"], None),
                               (16.0, 20.0, FARBEN["HT"], "HT Netz")]:
        ax.axvspan(a, b, ymin=1.0, ymax=1.04, color=farbe, clip_on=False, label=label)
    ax.set_title("Ø Börsenpreis nach Stunde und Monat (ct/kWh) – Balken oben: Modul-3-Fenster EWE NETZ",
                 fontsize=10, loc="left", pad=26)
    fig.colorbar(im, ax=ax, label="ct/kWh")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.22), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(pfad, dpi=150)
    plt.close(fig)


def grafik_kosten(tab: pd.DataFrame, pfad: Path):
    pivot = tab.pivot(index="Variante", columns="Fall", values="Kosten €/a")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    pivot.plot.barh(ax=ax, color=["#4C6A92", "#D99A3D", "#5B8C5A"])
    ax.invert_yaxis()
    ax.set_xlabel("€ pro Jahr, brutto")
    ax.set_ylabel("")
    ax.set_title("Jahreskosten je Variante", loc="left", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(pfad, dpi=150)
    plt.close(fig)


def grafik_beispielnacht(df: pd.DataFrame, pfad: Path):
    fall = {"boerse": eauto_last(df, "boerse"), "summe": eauto_last(df, "summe")}  # nur das Auto
    # Tag mit größtem Unterschied zwischen beiden Steuerungen
    diff = (fall["boerse"] - fall["summe"]).abs().groupby(df["datum"]).sum()
    tag = diff.idxmax()
    start = pd.Timestamp(tag, tz=ZEITZONE) + pd.Timedelta(hours=12)
    ende = start + pd.Timedelta(hours=21)
    ausschnitt = df.loc[start:ende]
    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    ax1.step(ausschnitt.index, ausschnitt["boerse_ct"], where="post", color="#333", lw=1.2, label="Börse")
    ax1.step(ausschnitt.index, ausschnitt["boerse_ct"] + ausschnitt["netz_m3_ct"], where="post",
             color="#C2553A", lw=1.2, ls="--", label="Börse + Netzentgelt Modul 3")
    ax1.set_ylabel("ct/kWh")
    ax2 = ax1.twinx()
    w = pd.Timedelta(minutes=13)
    ax2.bar(ausschnitt.index, fall["boerse"].loc[ausschnitt.index], width=w, align="edge",
            color="#4C6A92", alpha=0.45, label="Laden nach Börse")
    ax2.bar(ausschnitt.index, -fall["summe"].loc[ausschnitt.index], width=w, align="edge",
            color="#2E7D6B", alpha=0.45, label="Laden nach Summe (nach unten)")
    ax2.set_ylabel("kWh je Viertelstunde")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper left", frameon=False)
    ax1.set_title(f"Beispielnacht {tag}: wohin die Steuerung das Laden legt", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(pfad, dpi=150)
    plt.close(fig)


def schreibe_bericht(tab: pd.DataFrame, konflikt: pd.DataFrame, df: pd.DataFrame):
    zusammen = []
    for fall, g in tab.groupby("Fall", sort=False):
        k = dict(zip(g["Variante"].str[0], g["Kosten €/a"]))
        zusammen.append({
            "Fall": fall,
            "Dynamisch vs. Festpreis (gesteuert)": k["A"] - k["C"],
            "Steuerung allein (B→C)": k["B"] - k["C"],
            "Modul 3 ohne Anpassung (C→D)": k["C"] - k["D"],
            "Modul 3 mit Anpassung (C→E)": k["C"] - k["E"],
        })
    zus = pd.DataFrame(zusammen).set_index("Fall")
    zus.to_csv(AUSGABE / "ersparnis.csv", sep=";", decimal=",")
    tab.to_csv(AUSGABE / "kosten.csv", sep=";", decimal=",", index=False)
    konflikt.to_csv(AUSGABE / "signalkonflikt.csv", sep=";", decimal=",")

    html = f"""<!doctype html><html lang="de"><meta charset="utf-8">
<title>Tarif-Check EWE NETZ</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#222}}
table{{border-collapse:collapse;margin:1rem 0}}td,th{{border-bottom:1px solid #ddd;padding:.3rem .7rem;text-align:right}}
th:first-child,td:first-child{{text-align:left}}img{{max-width:100%}}small{{color:#666}}</style>
<h1>Dynamischer Tarif + Modul 3 im Netzgebiet EWE NETZ</h1>
<p>Zeitraum {df.index.min():%d.%m.%Y} – {df.index.max():%d.%m.%Y}, Day-Ahead DE-LU (15 min).
Ø Börsenpreis {df['boerse_ct'].mean():.1f} ct/kWh.</p>
<h2>Ersparnis in €/Jahr (brutto, positiv = günstiger)</h2>{zus.to_html(float_format='%.0f')}
<h2>Jahreskosten</h2><img src="kosten.png">
<h2>Signalkonflikt: Wo liegen die billigsten Börsen-Viertelstunden?</h2>
<p>Anteil in %, nach Modul-3-Stufe.</p>{konflikt.to_html()}
<img src="heatmap.png"><img src="beispielnacht.png">
<h2>Annahmen</h2><small>EWE NETZ 2026 netto: AP {NETZ_AP_STANDARD_CT} ct, Modul 3 HT {MODUL3_STUFEN_CT['HT']} /
ST {MODUL3_STUFEN_CT['ST']} / NT {MODUL3_STUFEN_CT['NT']} ct, Modul 1 {MODUL1_EUR_A} €/a.
Weitere Bestandteile {KONST_CT:.2f} ct netto, MwSt {MWST:.0%}. Haushalt {HAUSHALT_KWH_A} kWh,
E-Auto {EAUTO_KWH_A} kWh ({EAUTO_ANKUNFT_H}–{EAUTO_ABFAHRT_H} Uhr, {EAUTO_LADELEISTUNG_KW} kW),
WP {WP_KWH_A} kWh Strom (ungesteuert), Last aus stündlicher Außentemperatur {STANDORT['name']} (Open-Meteo), Heizgrenze {HEIZGRENZE_C:.0f} °C, Vorlauf {VORLAUF_C:.0f} °C, Jahres-COP {df['waerme_kwh'].sum() / WP_KWH_A:.2f}, {WP_FLEX_ANTEIL:.0%} der Tageswärme verschiebbar. Preise: Energy-Charts / SMARD, CC BY 4.0.</small>
</html>"""
    (AUSGABE / "bericht.html").write_text(html, encoding="utf-8")
    return zus


def main():
    AUSGABE.mkdir(exist_ok=True)
    print("1/4 Börsenpreise laden")
    df = baue_preisrahmen(lade_preise(ZEITRAUM_START, ZEITRAUM_ENDE))
    print(f"    {len(df):,} Viertelstunden, Ø {df['boerse_ct'].mean():.2f} ct/kWh")
    df["temp_c"] = lade_temperatur(df)
    df["cop"] = cop(df["temp_c"])
    df["waerme_kwh"] = wp_waermebedarf(df)
    print(f"    Wetter {STANDORT['name']}: Ø {df['temp_c'].mean():.1f} °C, "
          f"Jahres-COP {df['waerme_kwh'].sum() / WP_KWH_A:.2f}")
    print("2/4 Szenarien rechnen")
    tab, profile = rechne(df)
    print("3/4 Signalkonflikt")
    konflikt = konflikt_analyse(df)
    print("4/4 Grafiken + Bericht")
    grafik_heatmap(df, AUSGABE / "heatmap.png")
    grafik_kosten(tab, AUSGABE / "kosten.png")
    grafik_beispielnacht(df, AUSGABE / "beispielnacht.png")
    zus = schreibe_bericht(tab, konflikt, df)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 10)
    print("\nErsparnis €/a:\n", zus.round(0))
    print("\nSignalkonflikt (%):\n", konflikt)
    print(f"\nFertig: {AUSGABE.resolve() / 'bericht.html'}")


if __name__ == "__main__":
    main()
