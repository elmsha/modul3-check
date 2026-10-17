"""
Rechenkern für die Web-App: dynamischer Tarif + §14a Modul 3.
Alle Annahmen kommen als Parameter rein (keine globalen Variablen),
damit mehrere Nutzer der App sich nicht gegenseitig stören.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Netzgebiete (Preisblätter 2026, Niederspannung, netto)
# Zeitfenster als (Start, Ende) in Minuten seit Mitternacht, lokale Zeit.
# "quartale": in welchen Quartalen HT/NT gelten; sonst gilt überall ST.
# -----------------------------------------------------------------------------
NETZGEBIETE = {
    "EWE NETZ": {
        "ap": 3.20, "gp": 102.00, "modul1": -91.23,
        "stufen": {"HT": 5.62, "ST": 3.20, "NT": 0.32},
        "fenster": {"HT": [(990, 1230)], "NT": [(1380, 1440), (0, 300)]},
        "quartale": [1, 2, 3, 4],
        "quelle": "https://www.ewe-netz.de/-/media/ewe-netz/downloads/2026_02_24_ewe_netz_nne_strom_2026.pdf",
        "hinweis": "Zusätzliche Modul-3-Zeile mit 1,35 ct/kWh im Preisblatt unklar; ganzjährige Geltung angenommen.",
    },
    "Avacon Netz": {
        "ap": 6.04, "gp": 80.30, "modul1": -112.53,
        "stufen": {"HT": 8.41, "ST": 6.04, "NT": 0.60},
        "fenster": {"HT": [(990, 1260)], "NT": [(1380, 1440), (0, 300)]},
        "quartale": [1, 4],
        "quelle": "https://www.avacon-netz.de/content/dam/revu-global/avacon-netz/documents/netzentgelte-strom/2026/Preisbl%C3%A4tter_AVANG_Strom_01.01.2026.pdf",
        "hinweis": "Vorläufiges Preisblatt. HT/NT nur im 1. und 4. Quartal, sonst Standardtarif.",
    },
}

ZEITZONE = "Europe/Berlin"


@dataclass(frozen=True)
class Annahmen:
    netz: str = "EWE NETZ"
    haushalt_kwh: float = 3000
    eauto: bool = True
    eauto_kwh: float = 2500
    eauto_kw: float = 11.0
    eauto_ankunft_h: int = 18
    eauto_abfahrt_h: int = 7
    eauto_wochenende_tags: bool = False   # am Wochenende ab 8 Uhr an der Wallbox
    wp: bool = True
    wp_kwh: float = 4000
    wp_max_kw: float = 3.0
    wp_flex: float = 0.30
    heizgrenze_c: float = 15.0
    warmwasser_anteil: float = 0.15
    vorlauf_c: float = 35.0
    guetegrad: float = 0.45
    konst_ct: float = 8.99                # Stromsteuer, Umlagen, Konzession, Marge (netto)
    mwst: float = 0.19
    festpreis_brutto_ct: float = 30.0


# -----------------------------------------------------------------------------
# Preisrahmen
# -----------------------------------------------------------------------------

def stufen(index: pd.DatetimeIndex, netz: dict) -> np.ndarray:
    minute = index.hour * 60 + index.minute
    aktiv = np.isin(index.quarter, netz["quartale"])
    s = np.full(len(index), "ST", dtype=object)
    for name, fenster in netz["fenster"].items():
        for a, b in fenster:
            s[aktiv & (minute >= a) & (minute < b)] = name
    return s


def preisrahmen(boerse_eur_mwh: pd.Series, temp_c: pd.Series, netz_name: str) -> pd.DataFrame:
    netz = NETZGEBIETE[netz_name]
    df = pd.DataFrame({"boerse_ct": boerse_eur_mwh / 10.0, "temp_c": temp_c})
    df["stufe"] = stufen(df.index, netz)
    df["netz_m3_ct"] = df["stufe"].map(netz["stufen"]).astype(float)
    df["netz_std_ct"] = netz["ap"]
    df["datum"] = df.index.date
    return df


# -----------------------------------------------------------------------------
# Lasten
# -----------------------------------------------------------------------------

def _tagesgruppen(df: pd.DataFrame) -> list[np.ndarray]:
    codes = pd.factorize(df["datum"])[0]
    grenzen = np.flatnonzero(np.diff(codes)) + 1
    return np.split(np.arange(len(df)), grenzen)


def haushalt(df: pd.DataFrame, a: Annahmen) -> np.ndarray:
    h = df.index.hour + df.index.minute / 60
    form = 0.6 + 0.6 * np.exp(-((h - 7.5) ** 2) / 2) + 1.2 * np.exp(-((h - 19.0) ** 2) / 4)
    form = np.asarray(form, dtype=float)
    return form / form.sum() * a.haushalt_kwh


def _billigst(preis: np.ndarray, energie: float, kappe: np.ndarray) -> np.ndarray:
    out = np.zeros_like(preis, dtype=float)
    rest = energie
    for i in np.argsort(preis, kind="stable"):
        if rest <= 1e-9:
            break
        m = min(kappe[i], rest)
        out[i] = m
        rest -= m
    return out


def eauto(df: pd.DataFrame, a: Annahmen, signal: str | None) -> np.ndarray:
    idx = df.index
    tage = pd.DatetimeIndex(pd.unique(idx.normalize()))
    energie_tag = a.eauto_kwh / len(tage)
    slot_kwh = a.eauto_kw * 0.25
    boerse = df["boerse_ct"].to_numpy()
    summe = boerse + df["netz_m3_ct"].to_numpy()
    last = np.zeros(len(df))
    for tag in tage:
        ankunft = 8 if (a.eauto_wochenende_tags and tag.dayofweek >= 5) else a.eauto_ankunft_h
        von = idx.searchsorted(tag + pd.Timedelta(hours=ankunft))
        bis = idx.searchsorted(tag + pd.Timedelta(days=1, hours=a.eauto_abfahrt_h))
        if bis <= von:
            continue
        n = bis - von
        if signal is None:
            p = np.arange(n, dtype=float)
        elif signal == "boerse":
            p = boerse[von:bis]
        else:
            p = summe[von:bis]
        last[von:bis] += _billigst(p, energie_tag, np.full(n, slot_kwh))
    return last


def cop(df: pd.DataFrame, a: Annahmen) -> np.ndarray:
    hub = np.clip(a.vorlauf_c - df["temp_c"].to_numpy() + 5.0, 5.0, None)
    return np.clip(a.guetegrad * (a.vorlauf_c + 273.15) / hub, 1.5, 6.0)


def waerme(df: pd.DataFrame, a: Annahmen, c: np.ndarray) -> np.ndarray:
    raum = np.clip(a.heizgrenze_c - df["temp_c"].to_numpy(), 0, None)
    raum = raum / raum.sum() * (1 - a.warmwasser_anteil)
    form = raum + a.warmwasser_anteil / len(df)
    return form * a.wp_kwh / (form / c).sum()


def waermepumpe(df: pd.DataFrame, a: Annahmen, signal: str | None) -> np.ndarray:
    c = cop(df, a)
    w = waerme(df, a, c)
    if not signal:
        return w / c
    preis = df["boerse_ct"].to_numpy()
    if signal == "summe":
        preis = preis + df["netz_m3_ct"].to_numpy()
    last = np.zeros(len(df))
    for g in _tagesgruppen(df):
        fix_th = (1 - a.wp_flex) * w[g]
        kappe_th = np.clip(a.wp_max_kw * 0.25 - fix_th / c[g], 0, None) * c[g]
        flex_th = _billigst(preis[g] / c[g], a.wp_flex * w[g].sum(), kappe_th)
        last[g] = (fix_th + flex_th) / c[g]
    return last


# -----------------------------------------------------------------------------
# Kosten und Auswertung
# -----------------------------------------------------------------------------

def _kosten_dyn(df, last, a: Annahmen, modul3: bool) -> float:
    netz = NETZGEBIETE[a.netz]
    ap = df["netz_m3_ct"].to_numpy() if modul3 else df["netz_std_ct"].to_numpy()
    arbeit = ((df["boerse_ct"].to_numpy() + ap + a.konst_ct) * last).sum() / 100
    return (arbeit + netz["gp"] + netz["modul1"]) * (1 + a.mwst)


def _kosten_fest(last, a: Annahmen) -> float:
    return last.sum() * a.festpreis_brutto_ct / 100 + NETZGEBIETE[a.netz]["modul1"] * (1 + a.mwst)


def rechne(df: pd.DataFrame, a: Annahmen) -> pd.DataFrame:
    def gesamt(signal):
        l = haushalt(df, a)
        if a.eauto:
            l = l + eauto(df, a, signal)
        if a.wp:
            l = l + waermepumpe(df, a, signal)
        return l

    u, b, s = gesamt(None), gesamt("boerse"), gesamt("summe")
    zeilen = [
        ("A", "Festpreis", "keine", "Modul 1", _kosten_fest(u, a), u.sum()),
        ("B", "Dynamisch", "keine", "Modul 1", _kosten_dyn(df, u, a, False), u.sum()),
        ("C", "Dynamisch", "nach Börse", "Modul 1", _kosten_dyn(df, b, a, False), b.sum()),
        ("D", "Dynamisch", "nach Börse", "Modul 1+3", _kosten_dyn(df, b, a, True), b.sum()),
        ("E", "Dynamisch", "nach Börse + Netz", "Modul 1+3", _kosten_dyn(df, s, a, True), s.sum()),
    ]
    return pd.DataFrame(zeilen, columns=["Variante", "Tarif", "Steuerung", "Netzentgelt", "€/Jahr", "kWh/Jahr"])


def signalkonflikt(df: pd.DataFrame) -> pd.DataFrame:
    rang = df.groupby("datum")["boerse_ct"].rank(pct=True)
    out = pd.DataFrame({
        "billigste 25 % Börse": df.loc[rang <= 0.25, "stufe"].value_counts(normalize=True),
        "teuerste 25 % Börse": df.loc[rang >= 0.75, "stufe"].value_counts(normalize=True),
        "Zeitanteil": df["stufe"].value_counts(normalize=True),
    }).reindex(["NT", "ST", "HT"]).fillna(0)
    return out * 100
