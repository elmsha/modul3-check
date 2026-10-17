"""
Web-App: Dynamischer Tarif + zeitvariables Netzentgelt (§14a Modul 3)
Start lokal:  streamlit run app.py
"""

import altair as alt
import pandas as pd
import streamlit as st

import modell as m
import tarif_check as daten   # nutzt nur die Ladefunktionen (mit Cache-Ordner)

st.set_page_config(page_title="Modul-3-Check", page_icon="⚡", layout="wide")


# -----------------------------------------------------------------------------
# Daten (einmal laden, dann gecacht)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Lade Börsenpreise und Wetter …")
def lade_basis():
    preise = daten.lade_preise(daten.ZEITRAUM_START, daten.ZEITRAUM_ENDE)
    temp = daten.lade_temperatur(pd.DataFrame(index=preise.index))
    return preise, temp


@st.cache_data(show_spinner=False)
def rahmen(netz_name: str) -> pd.DataFrame:
    preise, temp = lade_basis()
    return m.preisrahmen(preise, temp, netz_name)


@st.cache_data(show_spinner="Rechne Szenarien …")
def ergebnis(a: m.Annahmen) -> pd.DataFrame:
    return m.rechne(rahmen(a.netz), a)


# -----------------------------------------------------------------------------
# Eingaben
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Annahmen")
    netz = st.selectbox("Netzgebiet", list(m.NETZGEBIETE))
    haushalt = st.number_input("Haushaltsstrom (kWh/Jahr)", 0, 10000, 3000, 250)

    st.subheader("E-Auto")
    eauto = st.toggle("E-Auto vorhanden", True)
    eauto_kwh = st.slider("Ladestrom (kWh/Jahr)", 500, 6000, 2500, 250, disabled=not eauto)
    ankunft, abfahrt = st.select_slider(
        "An der Wallbox (Werktag)", options=list(range(12, 24)) + list(range(0, 12)),
        value=(18, 7), format_func=lambda h: f"{h}:00", disabled=not eauto)
    wochenende = st.toggle("Am Wochenende ab 8 Uhr zu Hause", False, disabled=not eauto,
                           help="Damit kann das Auto auch den billigen Solarmittag nutzen.")

    st.subheader("Wärmepumpe")
    wp = st.toggle("Wärmepumpe vorhanden", True)
    wp_kwh = st.slider("WP-Strom ungesteuert (kWh/Jahr)", 1000, 10000, 4000, 250, disabled=not wp)
    wp_flex = st.slider("Verschiebbarer Anteil der Tageswärme", 0, 60, 30, 5, format="%d %%", disabled=not wp,
                        help="Hängt an Pufferspeicher, Fußbodenheizung und Gebäudemasse.") / 100
    vorlauf = st.select_slider("Vorlauftemperatur", [35, 45, 55], 35, format_func=lambda t: f"{t} °C",
                               disabled=not wp, help="35 °C Fußbodenheizung, 55 °C Altbau mit Heizkörpern")

    with st.expander("Weitere Annahmen"):
        festpreis = st.number_input("Festpreistarif brutto (ct/kWh)", 20.0, 50.0, 30.0, 0.5)
        konst = st.number_input("Steuern, Umlagen, Marge netto (ct/kWh)", 0.0, 20.0, 8.99, 0.1)

a = m.Annahmen(netz=netz, haushalt_kwh=haushalt, eauto=eauto, eauto_kwh=eauto_kwh,
               eauto_ankunft_h=ankunft, eauto_abfahrt_h=abfahrt, eauto_wochenende_tags=wochenende,
               wp=wp, wp_kwh=wp_kwh, wp_flex=wp_flex, vorlauf_c=vorlauf,
               festpreis_brutto_ct=festpreis, konst_ct=konst)

df = rahmen(netz)
info = m.NETZGEBIETE[netz]

# -----------------------------------------------------------------------------
# 1. Kernaussage: Signalkonflikt
# -----------------------------------------------------------------------------
st.title("Zwei Preissignale, ein Widerspruch")
st.markdown(
    "Mit dynamischem Tarif und **§14a Modul 3** bekommen Haushalte mit Wärmepumpe oder Wallbox zwei "
    "Preissignale: den Börsenpreis und ein zeitvariables Netzentgelt. "
    f"Wie gut passen sie zusammen – im Netzgebiet **{netz}**, mit echten Daten von "
    f"{df.index.min():%m/%Y} bis {df.index.max():%m/%Y}?")

k = m.signalkonflikt(df)
res = ergebnis(a)
kosten = dict(zip(res["Variante"], res["€/Jahr"]))

c1, c2, c3 = st.columns(3)
c1.metric("Teuerste Börsen-Viertelstunden im Netz-**Hochtarif**", f"{k.loc['HT', 'teuerste 25 % Börse']:.0f} %",
          f"Zufall wären {k.loc['HT', 'Zeitanteil']:.0f} %", delta_color="off")
c2.metric("Billigste Börsen-Viertelstunden im Netz-**Niedertarif**", f"{k.loc['NT', 'billigste 25 % Börse']:.0f} %",
          f"Zufall wären {k.loc['NT', 'Zeitanteil']:.0f} %", delta_color="off")
c3.metric("Zusatznutzen Modul 3 (C → E)", f"{kosten['C'] - kosten['E']:,.0f} € / Jahr".replace(",", "."),
          "bei Steuerung nach Börse + Netz", delta_color="off")

ht_trifft = k.loc["HT", "teuerste 25 % Börse"] / max(k.loc["HT", "Zeitanteil"], 0.1)
nt_trifft = k.loc["NT", "billigste 25 % Börse"] / max(k.loc["NT", "Zeitanteil"], 0.1)
st.info(
    f"**Lesart:** Das Hochtarif-Fenster liegt {ht_trifft:.1f}-mal so oft auf teuren Börsenzeiten wie per Zufall – "
    f"das Netz bestraft die richtige Zeit. Das Niedertarif-Fenster trifft die billigen Börsenzeiten "
    f"{nt_trifft:.1f}-mal so oft wie per Zufall. Die billigsten Stunden liegen von Frühjahr bis Herbst am "
    "Solarmittag – dort gibt das Netz keinen Rabatt.")

# Heatmaps: Markt vs. Netz
df_h = df.assign(monat=df.index.strftime("%Y-%m"), stunde=df.index.hour)
markt = df_h.groupby(["monat", "stunde"], as_index=False)["boerse_ct"].mean()
netzst = df_h.groupby(["monat", "stunde"], as_index=False)["netz_m3_ct"].mean()

basis = dict(x=alt.X("stunde:O", title="Uhrzeit", axis=alt.Axis(labelExpr="datum.value + ':00'", labelAngle=0)),
             y=alt.Y("monat:O", title=None))
hm_markt = alt.Chart(markt).mark_rect().encode(
    **basis, color=alt.Color("boerse_ct:Q", title="ct/kWh", scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
    tooltip=["monat", "stunde", alt.Tooltip("boerse_ct:Q", format=".1f", title="Börse ct/kWh")],
).properties(title="Markt: Ø Börsenpreis", height=320)
hm_netz = alt.Chart(netzst).mark_rect().encode(
    **basis, color=alt.Color("netz_m3_ct:Q", title="ct/kWh", scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
    tooltip=["monat", "stunde", alt.Tooltip("netz_m3_ct:Q", format=".2f", title="Netz ct/kWh")],
).properties(title=f"Netz: Modul-3-Entgelt {netz}", height=320)

h1, h2 = st.columns(2)
h1.altair_chart(hm_markt, width="stretch")
h2.altair_chart(hm_netz, width="stretch")
st.caption("Grün = billig, rot = teuer. Links signalisiert die Börse, rechts das Netz. "
           "Wo links grün und rechts nicht grün ist, widersprechen sich die Signale.")

# -----------------------------------------------------------------------------
# 2. Was es für den Haushalt bedeutet
# -----------------------------------------------------------------------------
st.header("Was das für die Stromrechnung bedeutet")

z1, z2, z3 = st.columns(3)
z1.metric("Steuerung nach Börse (B → C)", f"{kosten['B'] - kosten['C']:,.0f} € / Jahr".replace(",", "."))
z2.metric("Modul 3 ohne Anpassung (C → D)", f"{kosten['C'] - kosten['D']:,.0f} € / Jahr".replace(",", "."))
z3.metric("Modul 3 mit Anpassung (C → E)", f"{kosten['C'] - kosten['E']:,.0f} € / Jahr".replace(",", "."))

balken = alt.Chart(res.assign(Name=res["Variante"] + "  " + res["Tarif"] + ", " + res["Steuerung"] + ", " + res["Netzentgelt"])
                   ).mark_bar().encode(
    x=alt.X("€/Jahr:Q", title="€ pro Jahr, brutto"),
    y=alt.Y("Name:N", sort=None, title=None),
    color=alt.condition(alt.datum.Variante == "E", alt.value("#2E7D6B"), alt.value("#9AA5B1")),
    tooltip=["Variante", "Tarif", "Steuerung", "Netzentgelt", alt.Tooltip("€/Jahr:Q", format=",.0f"),
             alt.Tooltip("kWh/Jahr:Q", format=",.0f")],
).properties(height=230)
st.altair_chart(balken, width="stretch")

with st.expander("Tabelle"):
    st.dataframe(res.style.format({"€/Jahr": "{:,.0f}", "kWh/Jahr": "{:,.0f}"}), hide_index=True,
                 width="stretch")

st.caption("Vergleich A ↔ C hängt stark am angenommenen Festpreis. Belastbar sind vor allem die Abstände B → C → D → E.")

# -----------------------------------------------------------------------------
# 3. Methode
# -----------------------------------------------------------------------------
with st.expander("Methode, Annahmen, Quellen"):
    st.markdown(f"""
**Preise:** Day-Ahead-Auktion DE-LU in 15-Minuten-Auflösung, [Energy-Charts](https://api.energy-charts.info/)
(Fraunhofer ISE, Daten Bundesnetzagentur/SMARD, CC BY 4.0). Auf den gesamten Zeitraum werden die Netzentgelte 2026 angewendet.

**Netzentgelt {netz} (netto):** Arbeitspreis {info['ap']:.2f} ct/kWh · Modul 3: HT {info['stufen']['HT']:.2f} /
ST {info['stufen']['ST']:.2f} / NT {info['stufen']['NT']:.2f} ct/kWh · Modul 1: {info['modul1']:.2f} €/Jahr ·
[Preisblatt]({info['quelle']}). *{info['hinweis']}*

**Steuerung:** Das E-Auto lädt in den billigsten Viertelstunden, in denen es an der Wallbox steht; die Day-Ahead-Preise
dafür sind zum Ankunftszeitpunkt bekannt. Die Wärmepumpe verschiebt den gewählten Anteil der Tageswärme in die
Viertelstunden, in denen eine kWh Wärme am billigsten ist (Preis ÷ COP).

**Wärmepumpe:** Wärmebedarf aus stündlicher Außentemperatur Oldenburg ([Open-Meteo](https://open-meteo.com/)),
Heizgrenze 15 °C, 15 % Warmwasser, COP = 0,45 × Carnot.

**Vereinfachungen:** Modul 3 gilt für den ganzen Zähler (inkl. Haushaltsstrom). Kein Heimspeicher, keine PV.
Smart Meter wird vorausgesetzt. Typisierte Lastprofile, keine Messdaten.
""")
