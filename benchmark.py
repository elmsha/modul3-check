"""
Modul-3-Benchmark: Regel-Check, Markt-Fit und Kundennutzen je Netzbetreiber.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import modell as m

HIER = Path(__file__).resolve().parent
DATEI = HIER / "netzbetreiber.json"
SOMMER, WINTER = [2, 3], [1, 4]


# -----------------------------------------------------------------------------
# Daten
# -----------------------------------------------------------------------------

def lade(pfad: Path = DATEI) -> dict:
    return json.loads(Path(pfad).read_text(encoding="utf-8"))


def _min(t: str) -> int:
    h, mi = t.split(":")
    return int(h) * 60 + int(mi)


def _fenster(liste) -> list[tuple[int, int]]:
    return [(_min(a), _min(b)) for a, b in liste]


def zu_netz(nb: dict) -> dict:
    """Netzbetreiber-Eintrag -> Format, das modell.py versteht."""
    return {
        "ap": nb["st"], "gp": 0.0, "modul1": nb.get("modul1", 0.0),
        "stufen": {"HT": nb["ht"], "ST": nb["st"], "NT": nb["nt"]},
        "fenster": {"HT": _fenster(nb["ht_fenster"]), "NT": _fenster(nb["nt_fenster"])},
        "quartale": nb["quartale"],
        "quelle": nb.get("quelle", ""), "hinweis": nb.get("anmerkung", ""),
    }


def stunden(fenster: list[tuple[int, int]]) -> float:
    return sum(b - a for a, b in fenster) / 60


# -----------------------------------------------------------------------------
# Regel-Check (BDEW-Anwendungshilfe Modul 3, V1.2)
# -----------------------------------------------------------------------------

def _ueberlappung(f1, f2) -> bool:
    return any(a1 < b2 and a2 < b1 for a1, b1 in f1 for a2, b2 in f2)


def regel_check(nb: dict, toleranz_pp: float = 0.5) -> list[dict]:
    """Prüft die formalen Vorgaben. Toleranz für Rundung bei umgerechneten Bruttowerten."""
    nt_q = nb["nt"] / nb["st"] * 100
    ht_q = nb["ht"] / nb["st"] * 100
    ht_f, nt_f = _fenster(nb["ht_fenster"]), _fenster(nb["nt_fenster"])
    return [
        {"regel": "NT zwischen 10 % und 40 % des ST", "ok": 10 - toleranz_pp <= nt_q <= 40 + toleranz_pp,
         "wert": f"{nt_q:.0f} %"},
        {"regel": "HT höchstens 200 % des ST", "ok": ht_q <= 200 + toleranz_pp, "wert": f"{ht_q:.0f} %"},
        {"regel": "HT mindestens 2 Stunden pro Tag", "ok": stunden(ht_f) >= 2, "wert": f"{stunden(ht_f):g} h"},
        {"regel": "HT/NT in mindestens 2 Quartalen", "ok": len(set(nb["quartale"])) >= 2,
         "wert": ", ".join(f"Q{q}" for q in sorted(nb["quartale"]))},
        {"regel": "HT- und NT-Fenster überschneiden sich nicht", "ok": not _ueberlappung(ht_f, nt_f),
         "wert": "ok" if not _ueberlappung(ht_f, nt_f) else "Überschneidung"},
    ]


def regel_ok(nb: dict) -> bool:
    return all(r["ok"] for r in regel_check(nb))


# -----------------------------------------------------------------------------
# Markt-Fit
# -----------------------------------------------------------------------------

def _tagesmatrix(df: pd.DataFrame, spalte: str) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """Tage x 96 Viertelstunden; Tage mit Zeitumstellung (92/100 Werte) werden ausgelassen."""
    tage = df.index.normalize()
    zaehler = pd.Series(1, index=df.index).groupby(tage).size()
    volle = zaehler[zaehler == 96].index
    teil = df[tage.isin(volle)]
    return teil[spalte].to_numpy().reshape(-1, 96), volle


def markt_fit(preise: pd.DataFrame, netz: dict, quartale: list[int] | None = None) -> dict:
    """
    preise: DataFrame mit 'boerse_ct' (15-min, lokale Zeit).
    Lift = Anteil der billigsten (teuersten) 25 % Börsen-Viertelstunden im NT (HT) ÷ Zeitanteil NT (HT).
    Korrelation = mittlere Korrelation zwischen Netz- und Börsenpreis innerhalb eines Tages.
    Gerechnet nur über Tage, an denen HT/NT gelten (optional weiter eingeschränkt auf 'quartale').
    """
    df = preise[["boerse_ct"]].copy()
    df["stufe"] = m.stufen(df.index, netz)
    df["netz"] = df["stufe"].map(netz["stufen"]).astype(float)
    aktiv_q = [q for q in netz["quartale"] if quartale is None or q in quartale]
    df = df[np.isin(df.index.quarter, aktiv_q)]
    if df.empty:
        return {"tage": 0}
    B, tage = _tagesmatrix(df, "boerse_ct")
    N, _ = _tagesmatrix(df, "netz")
    S, _ = _tagesmatrix(df.assign(s=df["stufe"].map({"NT": 0, "ST": 1, "HT": 2})), "s")
    if len(B) == 0:
        return {"tage": 0}

    rang = B.argsort(axis=1).argsort(axis=1) / 95.0
    billig, teuer = rang <= 0.25, rang >= 0.75
    anteil_nt, anteil_ht = (S == 0).mean(), (S == 2).mean()
    lift_nt = ((S == 0) & billig).sum() / billig.sum() / anteil_nt if anteil_nt else np.nan
    lift_ht = ((S == 2) & teuer).sum() / teuer.sum() / anteil_ht if anteil_ht else np.nan

    bz = B - B.mean(axis=1, keepdims=True)
    nz = N - N.mean(axis=1, keepdims=True)
    nenner = np.sqrt((bz ** 2).sum(axis=1) * (nz ** 2).sum(axis=1))
    korr = np.where(nenner > 0, (bz * nz).sum(axis=1) / np.where(nenner > 0, nenner, 1), np.nan)

    # Wie teuer ist die Börse im Schnitt in NT- bzw. HT-Zeiten (relativ zum Tagesmittel)?
    tagesmittel = B.mean(axis=1, keepdims=True)
    delta = B - tagesmittel
    boerse_im_nt = delta[S == 0].mean() if (S == 0).any() else np.nan
    boerse_im_ht = delta[S == 2].mean() if (S == 2).any() else np.nan

    return {"tage": len(B), "lift_nt": float(lift_nt), "lift_ht": float(lift_ht),
            "korrelation": float(np.nanmean(korr)),
            "boerse_im_nt_ct": float(boerse_im_nt), "boerse_im_ht_ct": float(boerse_im_ht)}


# -----------------------------------------------------------------------------
# Kundennutzen
# -----------------------------------------------------------------------------

def kundennutzen(basis: pd.DataFrame, name: str, netz: dict, annahmen: m.Annahmen | None = None) -> dict:
    """
    basis: DataFrame mit 'boerse_eur_mwh' und 'temp_c'. Rechnet den Musterhaushalt.
    Ergebnis: Zusatznutzen Modul 3 (C→E) und (C→D) in €/Jahr brutto.
    """
    m.NETZGEBIETE[name] = netz
    df = m.preisrahmen(basis["boerse_eur_mwh"], basis["temp_c"], name)
    a = annahmen or m.Annahmen()
    from dataclasses import replace
    a = replace(a, netz=name)
    r = m.rechne(df, a)
    k = dict(zip(r["Variante"], r["€/Jahr"]))
    return {"c_e": k["C"] - k["E"], "c_d": k["C"] - k["D"], "b_c": k["B"] - k["C"]}


PROFILE = {
    "Pendler": m.Annahmen(),                                           # E-Auto 18–7 Uhr an der Wallbox
    "Zuhause": m.Annahmen(eauto_ankunft_h=8, eauto_abfahrt_h=7),        # E-Auto fast immer verfügbar
}
PROFIL_TEXT = {
    "Pendler": "E-Auto werktags 18–7 Uhr an der Wallbox + Wärmepumpe",
    "Zuhause": "E-Auto tagsüber verfügbar (Homeoffice, Zweitwagen) + Wärmepumpe",
}


def designtyp(nb: dict) -> str:
    f = _fenster(nb["nt_fenster"])
    mittag = any(a < 15 * 60 and b > 10 * 60 for a, b in f)
    nacht = any(a < 6 * 60 or b > 22 * 60 for a, b in f)
    if mittag and nacht:
        return "Hybrid (Nacht + Mittag)"
    return "Mittags-NT" if mittag else "Nacht-NT"


def saison(quartale: list[int]) -> str:
    q = sorted(set(quartale))
    if len(q) == 4:
        return "ganzjährig"
    if q == SOMMER:
        return "nur Sommer (Q2/Q3)"
    if q == WINTER:
        return "nur Winter (Q1/Q4)"
    return ", ".join(f"Q{x}" for x in q)


def kennzahlen(basis: pd.DataFrame, nb: dict, mit_kunden: bool = True) -> dict:
    preise = pd.DataFrame({"boerse_ct": basis["boerse_eur_mwh"] / 10.0})
    netz = zu_netz(nb)
    fit = markt_fit(preise, netz)
    fit_s = markt_fit(preise, netz, SOMMER)
    fit_w = markt_fit(preise, netz, WINTER)
    z = {
        "Netzbetreiber": nb["name"], "Region": nb.get("region", ""),
        "Designtyp": designtyp(nb), "Saison": saison(nb["quartale"]),
        "ST ct": nb["st"], "HT ct": nb["ht"], "NT ct": nb["nt"],
        "NT % ST": nb["nt"] / nb["st"] * 100, "HT % ST": nb["ht"] / nb["st"] * 100,
        "Spreizung ct": nb["ht"] - nb["nt"],
        "HT h/Tag": stunden(_fenster(nb["ht_fenster"])), "NT h/Tag": stunden(_fenster(nb["nt_fenster"])),
        "Regeln ok": regel_ok(nb),
        "Markt-Fit": fit.get("korrelation", np.nan),
        "Markt-Fit Sommer": fit_s.get("korrelation", np.nan),
        "Markt-Fit Winter": fit_w.get("korrelation", np.nan),
        "Lift HT": fit.get("lift_ht", np.nan), "Lift NT": fit.get("lift_nt", np.nan),
        "Lift NT Sommer": fit_s.get("lift_nt", np.nan), "Lift NT Winter": fit_w.get("lift_nt", np.nan),
        "Prüfung": nb.get("pruefung", ""), "Quelle": nb.get("quelle", ""), "Anmerkung": nb.get("anmerkung", ""),
    }
    if mit_kunden:
        for prof, a in PROFILE.items():
            z[f"Nutzen {prof} €"] = kundennutzen(basis, nb["name"], netz, a)["c_e"]
    return z


# -----------------------------------------------------------------------------
# Gesamtauswertung
# -----------------------------------------------------------------------------

def auswerten(basis: pd.DataFrame, daten: dict, mit_kunden: bool = True) -> pd.DataFrame:
    return pd.DataFrame([kennzahlen(basis, nb, mit_kunden) for nb in daten["netzbetreiber"]])


# =============================================================================
# Anbieter-Sicht: Was ist das "Smart-Paket" je Netzgebiet für Kunden wert?
# =============================================================================

KUNDENTYPEN = {
    "Wärmepumpe": m.Annahmen(eauto=False),
    "E-Auto (Pendler)": m.Annahmen(wp=False),
    "E-Auto (tagsüber zu Hause)": m.Annahmen(wp=False, eauto_ankunft_h=8, eauto_abfahrt_h=7),
    "Wärmepumpe + E-Auto": m.Annahmen(),
}
KUNDENTYP_TEXT = {
    "Wärmepumpe": "4.000 kWh/Jahr, 30 % der Tageswärme verschiebbar",
    "E-Auto (Pendler)": "2.500 kWh/Jahr, werktags 18–7 Uhr an der Wallbox",
    "E-Auto (tagsüber zu Hause)": "2.500 kWh/Jahr, fast immer an der Wallbox (Homeoffice, Zweitwagen)",
    "Wärmepumpe + E-Auto": "Wärmepumpe und Pendler-E-Auto zusammen",
}


def wert_zerlegung(basis: pd.DataFrame, nb: dict, annahmen: m.Annahmen) -> dict:
    """
    Zerlegt die Ersparnis gegenüber 'dynamischer Tarif, ungesteuert, ohne §14a' (€/Jahr brutto):
      Modul 1   = pauschale Gutschrift
      Steuerung = B → C  (Verbrauch nach Börsenpreis verschieben)
      Modul 3   = C → E  (zeitvariables Netzentgelt + Steuerung kennt beide Signale)
    Außerdem: Mehrwert netzbewusster Steuerung = D → E.
    """
    from dataclasses import replace
    netz = zu_netz(nb)
    m.NETZGEBIETE[nb["name"]] = netz
    df = m.preisrahmen(basis["boerse_eur_mwh"], basis["temp_c"], nb["name"])
    a = replace(annahmen, netz=nb["name"])
    r = m.rechne(df, a)
    k = dict(zip(r["Variante"], r["€/Jahr"]))
    mwst = 1 + a.mwst
    modul1 = -nb.get("modul1", 0.0) * mwst
    return {
        "Modul 1": modul1, "Steuerung": k["B"] - k["C"], "Modul 3": k["C"] - k["E"],
        "Gesamt": modul1 + (k["B"] - k["C"]) + (k["C"] - k["E"]),
        "Netzbewusst": k["D"] - k["E"],
        "Kosten vorher": k["B"] + modul1, "Kosten nachher": k["E"],
        "kWh": float(r.loc[r["Variante"] == "E", "kWh/Jahr"].iloc[0]),
    }


def konflikt_quote(preise: pd.DataFrame, netz: dict) -> dict:
    """Anteil der Viertelstunden, in denen Börse und Netz gegensätzlich signalisieren."""
    df = preise[["boerse_ct"]].copy()
    df["stufe"] = m.stufen(df.index, netz)
    rang = df.groupby(df.index.normalize())["boerse_ct"].rank(pct=True)
    billig_ht = (rang <= 0.25) & (df["stufe"] == "HT")
    teuer_nt = (rang >= 0.75) & (df["stufe"] == "NT")
    billig_kein_nt = (rang <= 0.25) & (df["stufe"] != "NT")
    sommer = np.isin(df.index.quarter, SOMMER)
    return {
        "Konflikt %": float((billig_ht | teuer_nt).mean() * 100),
        "Billig ohne NT %": float(billig_kein_nt[rang <= 0.25].mean() * 100) if (rang <= 0.25).any() else np.nan,
        "Billig ohne NT Sommer %": float(billig_kein_nt[(rang <= 0.25) & sommer].mean() * 100),
    }


def anbieter_auswertung(basis: pd.DataFrame, daten: dict) -> pd.DataFrame:
    preise = pd.DataFrame({"boerse_ct": basis["boerse_eur_mwh"] / 10.0})
    zeilen = []
    for nb in daten["netzbetreiber"]:
        netz = zu_netz(nb)
        kq = konflikt_quote(preise, netz)
        for typ, a in KUNDENTYPEN.items():
            w = wert_zerlegung(basis, nb, a)
            zeilen.append({"Netzbetreiber": nb["name"], "Region": nb.get("region", ""), "Kundentyp": typ,
                           "Designtyp": designtyp(nb), "Saison": saison(nb["quartale"]), **w, **kq})
    return pd.DataFrame(zeilen)


def fahrplan(nb: dict, jahr: int) -> pd.DataFrame:
    """Netzentgelt-Fahrplan: Tarifstufe und Preis je Viertelstunde eines Jahres (lokale Zeit)."""
    idx = pd.date_range(f"{jahr}-01-01", f"{jahr + 1}-01-01", freq="15min", tz=m.ZEITZONE, inclusive="left")
    netz = zu_netz(nb)
    stufe = m.stufen(idx, netz)
    return pd.DataFrame({"zeit_lokal": idx.strftime("%Y-%m-%d %H:%M"),
                         "zeit_utc": idx.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "stufe": stufe,
                         "netzentgelt_ct_kwh_netto": pd.Series(stufe).map(netz["stufen"]).to_numpy()})
