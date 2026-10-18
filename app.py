"""
Modul-3-Atlas – für Tarif- und Energiemanagement-Anbieter
Wie viel ist dynamischer Tarif + intelligente Steuerung + §14a je Netzgebiet für Kunden wert?
Start lokal:  streamlit run app.py
"""

import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import benchmark as bm
import modell as m
import tarif_check as daten

WHITEPAPER = "https://github.com/elmsha/modul3-check/blob/main/WHITEPAPER.md"
GITHUB = "https://github.com/elmsha/modul3-check"
WHITEPAPER_STE = "https://github.com/elmsha/modul3-check/blob/main/WHITEPAPER_STE.md"

st.set_page_config(page_title="Modul-3-Atlas", page_icon="⚡", layout="wide")

PINK, MINT, GELB, VIOLETT, TEXT, LEISE, KARTE, ST_GRAU = (
    "#FF4FA3", "#5CE1C6", "#FFD25A", "#8C7BFF", "#F4F1FF", "#B9B2D9", "#251A5C", "#3A2E78")
TEIL_FARBE = alt.Scale(domain=["Modul 1", "Steuerung", "Modul 3"], range=[VIOLETT, GELB, PINK])
STUFE_FARBE = alt.Scale(domain=["Hochtarif", "Standard", "Niedertarif"], range=[PINK, ST_GRAU, MINT])

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, label {{ font-family: 'Nunito', sans-serif !important; }}
.block-container {{ padding-top: 2rem; max-width: 1200px; }}
.hero {{ background: linear-gradient(135deg, #2B1C6E 0%, #17103A 70%); border-radius: 28px; padding: 2rem 2.2rem 1.6rem;
         margin-bottom: 1rem; border: 1px solid rgba(255,255,255,.06); }}
.hero h1 {{ font-size: 2.7rem; font-weight: 900; margin: 0 0 .4rem; letter-spacing: -.5px; color: {TEXT} !important; }}
.hero h1 span {{ color: {PINK} !important; }}
.hero p {{ font-size: 1.12rem; color: {LEISE}; max-width: 860px; margin: 0 0 .5rem; line-height: 1.5; }}
.hero a {{ color: {MINT}; }}
.badge {{ display:inline-block; background:{GELB}; color:#17103A; font-size:.72rem; font-weight:800;
          padding:.15rem .6rem; border-radius:999px; vertical-align: middle; margin-left:.5rem; }}
.karte {{ background: {KARTE}; border-radius: 22px; padding: 1.1rem 1.25rem; height: 100%;
          border: 1px solid rgba(255,255,255,.05); }}
.karte h4 {{ margin: 0 0 .35rem; font-size: 1.02rem; font-weight: 800; color: {TEXT}; }}
.karte p {{ margin: 0; font-size: .95rem; line-height: 1.5; color: {LEISE}; }}
.zahl {{ font-size: 2.4rem; font-weight: 900; line-height: 1.05; }}
.klein {{ font-size: .85rem; color: {LEISE}; }}
.pitch {{ background: linear-gradient(90deg, rgba(255,79,163,.18), rgba(140,123,255,.12)); border-radius: 18px;
          padding: 1rem 1.2rem; font-size: 1.12rem; font-weight: 700; color: {TEXT}; border-left: 5px solid {PINK}; }}
.hinweis {{ border-left: 4px solid {GELB}; padding: .6rem .95rem; background: rgba(255,210,90,.08);
            border-radius: 0 14px 14px 0; margin: .6rem 0; font-size: .93rem; color: {LEISE}; }}
.stTabs [data-baseweb="tab"] {{ font-weight: 800; font-size: 1rem; }}
h2, h3 {{ font-weight: 900 !important; }}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Daten
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Lade Markt- und Wetterdaten …")
def basis() -> pd.DataFrame:
    p = daten.lade_preise(daten.ZEITRAUM_START, daten.ZEITRAUM_ENDE)
    t = daten.lade_temperatur(pd.DataFrame(index=p.index))
    return pd.DataFrame({"boerse_eur_mwh": p, "temp_c": t})


@st.cache_data(show_spinner=False)
def netzdaten() -> dict:
    return bm.lade()


@st.cache_data(show_spinner="Rechne alle Netzgebiete und Kundentypen durch (einmalig ca. 15 Sekunden) …")
def auswertung() -> pd.DataFrame:
    return bm.anbieter_auswertung(basis(), netzdaten())


@st.cache_data(show_spinner="Rechne …")
def rechner(nb_json: str, annahmen_json: str) -> dict:
    return bm.wert_zerlegung(basis(), json.loads(nb_json), m.Annahmen(**json.loads(annahmen_json)))


@st.cache_data(show_spinner=False)
def fahrplan_csv(name: str, jahr: int) -> bytes:
    nb = {x["name"]: x for x in netzdaten()["netzbetreiber"]}[name]
    return bm.fahrplan(nb, jahr).to_csv(index=False, sep=";").encode("utf-8")


def eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", ".")


def segmente(nb: dict, saison_name: str, quartal: int) -> list[dict]:
    zeilen = [{"Netzbetreiber": nb["name"], "Saison": saison_name, "von": 0.0, "bis": 24.0, "Stufe": "Standard"}]
    if quartal in nb["quartale"]:
        for stufe, key in [("Hochtarif", "ht_fenster"), ("Niedertarif", "nt_fenster")]:
            for a, b in bm._fenster(nb[key]):
                zeilen.append({"Netzbetreiber": nb["name"], "Saison": saison_name, "von": a / 60, "bis": b / 60,
                               "Stufe": stufe})
    return zeilen


def streifen_chart(nbs: list[dict], reihenfolge: list[str]) -> alt.Chart:
    rows = []
    for nb in nbs:
        rows += segmente(nb, "Winter (Okt–Mär)", 1) + segmente(nb, "Sommer (Apr–Sep)", 3)
    d = pd.DataFrame(rows)
    return alt.Chart(d).mark_rect(cornerRadius=4, stroke="#17103A", strokeWidth=2).encode(
        x=alt.X("von:Q", title=None, scale=alt.Scale(domain=[0, 24]),
                axis=alt.Axis(values=list(range(0, 25, 3)), labelExpr="datum.value + ':00'")),
        x2="bis:Q",
        y=alt.Y("Netzbetreiber:N", sort=reihenfolge, title=None),
        color=alt.Color("Stufe:N", scale=STUFE_FARBE, legend=alt.Legend(orient="top", title=None)),
        column=alt.Column("Saison:N", title=None, sort=["Winter (Okt–Mär)", "Sommer (Apr–Sep)"],
                          header=alt.Header(labelFontSize=14, labelFontWeight="bold", labelColor=TEXT)),
        tooltip=["Netzbetreiber", "Saison", "Stufe"],
    ).properties(width=430, height=28 * len(nbs))


# -----------------------------------------------------------------------------
# Kopf
# -----------------------------------------------------------------------------
D = netzdaten()
NBS = {nb["name"]: nb for nb in D["netzbetreiber"]}

st.markdown(f"""
<div class="hero">
<h1>Wo lohnt sich <span>§14a</span> für deine Kunden? <span class="badge" style="color:#17103A !important">PROTOTYP</span></h1>
<p>Dynamischer Stromtarif, intelligente Steuerung und reduzierte Netzentgelte für Wärmepumpen und Wallboxen –
was das Paket einem Haushalt bringt, hängt stark vom Netzgebiet ab. Der Modul-3-Atlas rechnet es für
<b>{len(NBS)} Netzbetreiber</b> mit echten Börsenpreisen durch: für Produkt, Vertrieb und Steuerungslogik.</p>
<p class="klein">Preisblätter {D['jahr']} · Day-Ahead-Preise Okt 2025 – Sep 2026 · Wetter Oldenburg ·
<a href="{WHITEPAPER}" target="_blank">Whitepaper</a> ·
<a href="{WHITEPAPER_STE}" target="_blank">English (ASD-STE100)</a> · <a href="{GITHUB}" target="_blank">Code &amp; Daten</a></p>
</div>
""", unsafe_allow_html=True)

A = auswertung()

tab_wo, tab_rechner, tab_steuer, tab_daten = st.tabs(
    ["💸  Wo lohnt es sich?", "🧮  Kundenrechner", "🧭  Signale & Steuerung", "🔌  Daten & Fahrpläne"])

# =============================================================================
# TAB 1: WO LOHNT ES SICH?
# =============================================================================
with tab_wo:
    typ = st.radio("Kundentyp", list(bm.KUNDENTYPEN), index=3, horizontal=True,
                   help="Alle Kundentypen haben zusätzlich 3.000 kWh normalen Haushaltsstrom.")
    st.caption(bm.KUNDENTYP_TEXT[typ])
    t = A[A["Kundentyp"] == typ].sort_values("Gesamt", ascending=False)
    best, schlecht = t.iloc[0], t.iloc[-1]

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="karte"><div class="klein">Ersparnis pro Jahr, je nach Netzgebiet</div>
<div class="zahl" style="color:{PINK}">{eur(schlecht['Gesamt'])} – {eur(best['Gesamt'])}</div>
<p>Gleicher Kunde, gleiche Börse – der Unterschied kommt allein aus dem Netzentgelt.</p></div>""",
                    unsafe_allow_html=True)
    with k2:
        anteil = (t["Modul 3"] / t["Gesamt"]).median() * 100
        st.markdown(f"""<div class="karte"><div class="klein">Anteil von Modul 3 an der Ersparnis (Median)</div>
<div class="zahl" style="color:{MINT}">{anteil:.0f} %</div>
<p>Der Rest kommt aus Modul 1 (pauschal) und der Steuerung nach Börsenpreis.</p></div>""", unsafe_allow_html=True)
    with k3:
        neg = t[t["Modul 3"] < 10]["Netzbetreiber"].tolist()
        txt = (f"Bei <b>{', '.join(neg)}</b> bringt Modul 3 diesem Kundentyp kaum etwas oder kostet sogar – "
               "hier lieber nur Modul 1 empfehlen." if neg else
               "In allen erfassten Netzgebieten lohnt sich Modul 3 für diesen Kundentyp.")
        st.markdown(f'<div class="karte"><div class="klein">Vorsicht bei der Empfehlung</div>'
                    f'<div class="zahl" style="color:{GELB}">{len(neg)} von {len(t)}</div><p>{txt}</p></div>',
                    unsafe_allow_html=True)

    st.write("")
    st.markdown(f'<div class="pitch">„Mit dynamischem Tarif, intelligenter Steuerung und §14a spart ein Haushalt '
                f'({typ}) im Netz von {best["Netzbetreiber"]} rund {eur(best["Gesamt"])} pro Jahr.“</div>',
                unsafe_allow_html=True)
    st.write("")

    lang = t.melt(id_vars=["Netzbetreiber", "Gesamt"], value_vars=["Modul 1", "Steuerung", "Modul 3"],
                  var_name="Baustein", value_name="€")
    lang["rang"] = lang["Baustein"].map({"Modul 1": 0, "Steuerung": 1, "Modul 3": 2})
    t = t.assign(label_x=t[["Modul 1", "Steuerung", "Modul 3"]].clip(lower=0).sum(axis=1))
    reihenfolge = t["Netzbetreiber"].tolist()
    balken = alt.Chart(lang).mark_bar(cornerRadius=6, height=20).encode(
        y=alt.Y("Netzbetreiber:N", sort=reihenfolge, title=None),
        x=alt.X("sum(€):Q", title="Ersparnis pro Jahr (€, brutto)"),
        color=alt.Color("Baustein:N", scale=TEIL_FARBE, sort=["Modul 1", "Steuerung", "Modul 3"],
                        legend=alt.Legend(orient="top", title=None)),
        order=alt.Order("rang:Q", sort="ascending"),
        tooltip=["Netzbetreiber", "Baustein", alt.Tooltip("€:Q", format=".0f")])
    gesamt_txt = alt.Chart(t).mark_text(align="left", dx=6, fontWeight="bold", color=TEXT).encode(
        y=alt.Y("Netzbetreiber:N", sort=reihenfolge), x="label_x:Q", text=alt.Text("Gesamt:Q", format=".0f"))
    st.altair_chart((balken + gesamt_txt).properties(height=34 * len(t)), width="stretch")
    st.caption("Ersparnis gegenüber einem dynamischen Tarif ohne Steuerung und ohne §14a. "
               "**Modul 1** = pauschale Netzentgelt-Gutschrift · **Steuerung** = Verbrauch in günstige Börsenstunden "
               "verschieben · **Modul 3** = zeitvariables Netzentgelt, Steuerung kennt Börse und Netz.")

    with st.expander("Tabelle"):
        st.dataframe(t[["Netzbetreiber", "Region", "Gesamt", "Modul 1", "Steuerung", "Modul 3", "Designtyp", "Saison"]],
                     hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.0f €")
                                    for c in ["Gesamt", "Modul 1", "Steuerung", "Modul 3"]})

# =============================================================================
# TAB 2: KUNDENRECHNER
# =============================================================================
with tab_rechner:
    st.markdown("Für das Kundengespräch oder die Produktseite: Ersparnis für einen konkreten Haushalt.")
    c1, c2, c3 = st.columns(3)
    name = c1.selectbox("Netzbetreiber", list(NBS), index=list(NBS).index("EWE NETZ") if "EWE NETZ" in NBS else 0)
    haushalt = c2.number_input("Haushaltsstrom (kWh/Jahr)", 0, 10000, 3000, 250)
    c3.markdown(f"<div class='klein' style='margin-top:1.9rem'>{NBS[name]['region']} · "
                f"{bm.designtyp(NBS[name])}, {bm.saison(NBS[name]['quartale'])}</div>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        wp = st.toggle("Wärmepumpe", True)
        wp_kwh = st.slider("Wärmepumpe: Strom kWh/Jahr", 1000, 10000, 4000, 250, disabled=not wp)
        wp_flex = st.slider("Verschiebbarer Anteil der Tageswärme", 0, 60, 30, 5, format="%d %%", disabled=not wp,
                            help="Pufferspeicher, Fußbodenheizung, Gebäudemasse") / 100
    with w2:
        ea = st.toggle("E-Auto", True)
        ea_kwh = st.slider("E-Auto: Ladestrom kWh/Jahr", 500, 6000, 2500, 250, disabled=not ea)
        verf = st.radio("Wann steht das Auto an der Wallbox?", ["Abends und nachts (18–7 Uhr)", "Fast immer"],
                        horizontal=True, disabled=not ea)

    ann = dict(haushalt_kwh=haushalt, wp=wp, wp_kwh=wp_kwh, wp_flex=wp_flex, eauto=ea, eauto_kwh=ea_kwh,
               eauto_ankunft_h=18 if verf.startswith("Abends") else 8, eauto_abfahrt_h=7)
    if not wp and not ea:
        st.info("Ohne Wärmepumpe oder E-Auto gibt es keine steuerbare Verbrauchseinrichtung – §14a greift nicht.")
    else:
        w = rechner(json.dumps(NBS[name]), json.dumps(ann))
        e1, e2 = st.columns([1, 1.6])
        with e1:
            st.markdown(f"""<div class="karte"><div class="klein">Ersparnis pro Jahr</div>
<div class="zahl" style="color:{PINK}">{eur(w['Gesamt'])}</div>
<p>Stromkosten {eur(w['Kosten vorher'])} → <b style="color:{TEXT}">{eur(w['Kosten nachher'])}</b> pro Jahr</p>
<p class="klein" style="margin-top:.5rem">davon Modul 1: {eur(w['Modul 1'])} · Steuerung: {eur(w['Steuerung'])} ·
Modul 3: {eur(w['Modul 3'])}</p></div>""", unsafe_allow_html=True)
        with e2:
            schritte = [("Vorher", w["Kosten vorher"], "Basis"), ("Modul 1", -w["Modul 1"], "Modul 1"),
                        ("Steuerung", -w["Steuerung"], "Steuerung"), ("Modul 3", -w["Modul 3"], "Modul 3")]
            rows, stand = [], 0.0
            for lbl, wert, farbe in schritte:
                if lbl == "Vorher":
                    rows.append({"Schritt": lbl, "von": 0, "bis": wert, "Farbe": "Basis", "Wert": wert})
                    stand = wert
                else:
                    rows.append({"Schritt": lbl, "von": stand, "bis": stand + wert, "Farbe": farbe, "Wert": wert})
                    stand += wert
            rows.append({"Schritt": "Nachher", "von": 0, "bis": stand, "Farbe": "Nachher", "Wert": stand})
            wf = pd.DataFrame(rows)
            wf_chart = alt.Chart(wf).mark_bar(cornerRadius=6, size=46).encode(
                x=alt.X("Schritt:N", sort=list(wf["Schritt"]), title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("von:Q", title="Stromkosten € pro Jahr",
                        scale=alt.Scale(domain=[max(0, stand - 1.2 * w["Gesamt"]) // 100 * 100,
                                                (w["Kosten vorher"] + 50) // 100 * 100 + 100], clamp=True),
                        axis=alt.Axis(format="d")), y2="bis:Q",
                color=alt.Color("Farbe:N", legend=None, scale=alt.Scale(
                    domain=["Basis", "Modul 1", "Steuerung", "Modul 3", "Nachher"],
                    range=[ST_GRAU, VIOLETT, GELB, PINK, MINT])),
                tooltip=["Schritt", alt.Tooltip("Wert:Q", format=".0f", title="€")])
            txt = alt.Chart(wf[wf["Schritt"].isin(["Modul 1", "Steuerung", "Modul 3"])]).mark_text(
                dy=-10, color=TEXT, fontWeight="bold").encode(
                x=alt.X("Schritt:N", sort=list(wf["Schritt"])), y="von:Q", text=alt.Text("Wert:Q", format=".0f"))
            st.altair_chart((wf_chart + txt).properties(height=280), width="stretch")
            st.caption("Achse beginnt nicht bei null, damit die Einsparschritte sichtbar sind.")

        pitch = (f"Ein Haushalt im Netzgebiet von {name} mit "
                 f"{'Wärmepumpe (' + format(wp_kwh, ',').replace(',', '.') + ' kWh)' if wp else ''}"
                 f"{' und ' if wp and ea else ''}"
                 f"{'E-Auto (' + format(ea_kwh, ',').replace(',', '.') + ' kWh)' if ea else ''} spart mit dynamischem "
                 f"Stromtarif, intelligenter Steuerung und reduziertem Netzentgelt nach §14a EnWG rund "
                 f"{eur(w['Gesamt'])} pro Jahr.*\n\n*Modellrechnung auf Basis der Börsenpreise Okt 2025 – Sep 2026 und "
                 f"des Preisblatts {D['jahr']} von {name}; tatsächliche Ersparnis abhängig von Verbrauch und Tarif.")
        st.markdown("**Textbaustein für Angebot oder Produktseite**")
        st.code(pitch, language=None, wrap_lines=True)
        st.markdown('<div class="hinweis">Modellrechnung mit typisierten Lastprofilen. „Vorher“ = dynamischer Tarif '
                    'ohne Steuerung und ohne §14a. Grundgebühren, Smart-Meter- und Steuerbox-Kosten sind nicht '
                    'enthalten. Keine Tarifberatung.</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 3: SIGNALE & STEUERUNG
# =============================================================================
with tab_steuer:
    st.markdown("Für die Optimierungslogik im Energiemanagement: Börse und Netzentgelt sind zwei Signale – "
                "sie zeigen nicht immer in dieselbe Richtung.")
    s = A[A["Kundentyp"] == "Wärmepumpe + E-Auto"].sort_values("Netzbewusst", ascending=False)
    nacht = s[(s["Designtyp"] == "Nacht-NT") & (s["Saison"] == "ganzjährig")]

    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown(f"""<div class="karte"><div class="klein">Mehrwert netzbewusster Steuerung</div>
<div class="zahl" style="color:{PINK}">{eur(s['Netzbewusst'].min())} – {eur(s['Netzbewusst'].max())}</div>
<p>pro Haushalt und Jahr, wenn die Steuerung auf <b>Börse + Netzentgelt</b> optimiert statt nur auf den
Börsenpreis (Modul 3 gewählt).</p></div>""", unsafe_allow_html=True)
    with i2:
        v = nacht["Billig ohne NT Sommer %"].mean() if len(nacht) else np.nan
        st.markdown(f"""<div class="karte"><div class="klein">Sommer bei ganzjährigem Nacht-Niedertarif</div>
<div class="zahl" style="color:{GELB}">{v:.0f} %</div>
<p>der billigsten Börsen-Viertelstunden liegen <b>nicht</b> im Netz-Niedertarif. Mittags-PV schlägt dann den
Netzrabatt – die Steuerung muss abwägen, nicht einer Regel folgen.</p></div>""", unsafe_allow_html=True)
    with i3:
        top = s.sort_values("Konflikt %", ascending=False).iloc[0]
        st.markdown(f"""<div class="karte"><div class="klein">Häufigster direkter Widerspruch</div>
<div class="zahl" style="color:{MINT}">{top['Konflikt %']:.0f} %</div>
<p>der Viertelstunden bei <b>{top['Netzbetreiber']}</b>: Börse billig, aber Netz-Hochtarif – oder umgekehrt.</p></div>""",
                    unsafe_allow_html=True)

    st.subheader("Wann gelten Hoch- und Niedertarif?")
    reihenfolge = s.sort_values("Konflikt %")["Netzbetreiber"].tolist()
    st.altair_chart(streifen_chart(list(NBS.values()), reihenfolge), width="content")

    st.subheader("Kennzahlen für die Steuerung")
    st.dataframe(s[["Netzbetreiber", "Designtyp", "Saison", "Netzbewusst", "Konflikt %", "Billig ohne NT Sommer %"]],
                 hide_index=True, width="stretch",
                 column_config={
                     "Netzbewusst": st.column_config.NumberColumn("Mehrwert netzbewusst €/Jahr", format="%.0f €"),
                     "Konflikt %": st.column_config.ProgressColumn("Direkter Widerspruch", min_value=0, max_value=25,
                                                                   format="%.0f %%"),
                     "Billig ohne NT Sommer %": st.column_config.NumberColumn("Billige Börsenzeit ohne NT (Sommer)",
                                                                             format="%.0f %%")})
    st.markdown("""
**Steuerungsregel in einem Satz:** Optimiere auf den **Endpreis je Viertelstunde** (Börse + Netzentgelt-Stufe +
Umlagen), nicht auf ein einzelnes Signal – und nutze bei Wärmepumpen zusätzlich den temperaturabhängigen
Wirkungsgrad (Preis ÷ COP).
""")

# =============================================================================
# TAB 4: DATEN & FAHRPLÄNE
# =============================================================================
with tab_daten:
    st.subheader("Netzentgelt-Fahrpläne")
    st.markdown("Tarifstufe und Netzentgelt je Viertelstunde für ein ganzes Jahr – direkt verwendbar in "
                "Optimierung, Abrechnungsprüfung oder Simulation.")
    f1, f2, f3 = st.columns([1.4, .8, 1])
    fp_name = f1.selectbox("Netzbetreiber", list(NBS), key="fp")
    fp_jahr = f2.selectbox("Jahr", [D["jahr"]], key="fpj")
    f3.markdown("<div style='margin-top:1.75rem'></div>", unsafe_allow_html=True)
    f3.download_button("⬇ Fahrplan als CSV", fahrplan_csv(fp_name, fp_jahr),
                       f"netzentgelt_fahrplan_{fp_name.replace(' ', '_')}_{fp_jahr}.csv", "text/csv",
                       width="stretch")

    st.subheader("Erfasste Preisblätter")
    roh = pd.DataFrame([{
        "Netzbetreiber": nb["name"], "Region": nb["region"],
        "HT-Fenster": ", ".join(f"{a}–{b}" for a, b in nb["ht_fenster"]),
        "NT-Fenster": ", ".join(f"{a}–{b}" for a, b in nb["nt_fenster"]),
        "Quartale": ", ".join(f"Q{q}" for q in nb["quartale"]),
        "HT ct": nb["ht"], "ST ct": nb["st"], "NT ct": nb["nt"], "Modul 1 €": nb["modul1"],
        "Prüfung": nb["pruefung"], "Quelle": nb["quelle"]} for nb in D["netzbetreiber"]])
    st.dataframe(roh, hide_index=True, width="stretch",
                 column_config={"Quelle": st.column_config.LinkColumn("Quelle", display_text="öffnen")})
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("⬇ Alle als CSV", roh.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       "modul3_netzbetreiber.csv", "text/csv")
    d2.download_button("⬇ Alle als JSON", json.dumps(D, ensure_ascii=False, indent=2).encode("utf-8"),
                       "modul3_netzbetreiber.json", "application/json")
    if D.get("nicht_aufgenommen"):
        st.caption("Nicht aufgenommen: " + "; ".join(f"{x['name']} ({x['grund']})" for x in D["nicht_aufgenommen"]))

    st.subheader("So wird gerechnet")
    st.markdown(f"""
- **Haushalt:** 3.000 kWh Haushaltsstrom plus Wärmepumpe (Wärmebedarf aus Außentemperatur Oldenburg,
  temperaturabhängiger COP) und/oder E-Auto (11 kW). Flexible Lasten werden in die günstigsten Viertelstunden
  gelegt; die Day-Ahead-Preise sind zum Zeitpunkt der Entscheidung bekannt.
- **Vorher:** dynamischer Tarif, ohne Steuerung, ohne §14a. **Nachher:** dynamischer Tarif, Steuerung auf
  Börse + Netzentgelt, Modul 1 + 3.
- **Bausteine:** Modul 1 = pauschale Gutschrift · Steuerung = Verschiebung nach Börsenpreis ·
  Modul 3 = Zusatznutzen des zeitvariablen Netzentgelts · netzbewusst = Mehrwert, wenn die Steuerung das
  Netzentgelt kennt, statt nur die Börse.
- **Gleiche Börsenpreise** für alle Netzgebiete (eine Gebotszone) – Unterschiede kommen nur aus dem Netzentgelt.

**Grenzen:** Typisierte Lastprofile; Preisblätter teils aus Sekundärquellen (Spalte „Prüfung“); Netzentgelte 2026
auf Okt 2025 – Sep 2026 angewendet; Modul 3 für den ganzen Zähler angenommen; keine Grundgebühren, Messstellen- oder
Steuerbox-Kosten. Keine Tarif- oder Rechtsberatung.

Ausführlich: [Whitepaper]({WHITEPAPER}) · [English, ASD-STE100]({WHITEPAPER_STE}) · Daten: Energy-Charts (Fraunhofer ISE, CC BY 4.0), Open-Meteo (CC BY 4.0),
Preisblätter der Netzbetreiber.
""")

st.divider()
st.markdown(f"<div class='klein'>Modul-3-Atlas · Prototyp von Elmar Hackmann, Oldenburg · "
            f"<a href='{WHITEPAPER}' target='_blank' style='color:{MINT}'>Whitepaper</a> · "
            f"<a href='{WHITEPAPER_STE}' target='_blank' style='color:{MINT}'>English (ASD-STE100)</a> · "
            f"<a href='{GITHUB}' target='_blank' style='color:{MINT}'>GitHub</a> · "
            "Feedback und Korrekturen zu Preisblättern willkommen.</div>", unsafe_allow_html=True)
