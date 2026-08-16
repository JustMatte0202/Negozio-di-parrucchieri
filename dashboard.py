"""
Dashboard del negozio di parrucchieri.

Avvio:
    streamlit run dashboard.py

Legge i tre CSV in `data/` (generati da `genera_dataset.py` oppure, in
futuro, riempiti con i dati reali del negozio) e mostra i principali
indicatori: incassi, appuntamenti, clienti nuovi e di ritorno, servizi
più richiesti, giorni e orari di punta.
"""

from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Palette e stile dei grafici (colori validati per accessibilità)
# ---------------------------------------------------------------------------
BLU = "#2a78d6"        # serie principale
ARANCIO = "#eb6834"    # seconda serie
ACQUA = "#1baf7a"      # terza serie
GRIGIO_TESTO = "#52514e"
GRIGIO_GRIGLIA = "#e1e0d9"
SCALA_BLU = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def stile_grafico(fig: go.Figure, mostra_legenda: bool = False) -> go.Figure:
    """Applica a tutti i grafici lo stesso aspetto pulito e coerente."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, sans-serif", color=GRIGIO_TESTO, size=13),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=mostra_legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRIGIO_GRIGLIA, title=None)
    fig.update_yaxes(gridcolor=GRIGIO_GRIGLIA, zeroline=False, title=None)
    return fig


# ---------------------------------------------------------------------------
# Caricamento dati
# ---------------------------------------------------------------------------
@st.cache_data
def carica_dati():
    appuntamenti = pd.read_csv("data/appuntamenti.csv", parse_dates=["data"])
    clienti = pd.read_csv("data/clienti.csv", parse_dates=["data_prima_visita"])
    servizi = pd.read_csv("data/servizi.csv")

    df = (
        appuntamenti
        .merge(servizi, on="id_servizio")
        .merge(clienti[["id_cliente", "nome", "cognome", "canale_acquisizione",
                        "data_prima_visita"]], on="id_cliente")
    )
    df["ora_num"] = pd.to_datetime(df["ora"], format="%H:%M:%S").dt.hour
    df["mese"] = df["data"].dt.to_period("M").dt.to_timestamp()
    giorni = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Gio", 4: "Ven", 5: "Sab", 6: "Dom"}
    df["giorno_settimana"] = df["data"].dt.weekday.map(giorni)
    df["cliente_completo"] = df["nome"] + " " + df["cognome"]
    # Un appuntamento è di un "nuovo cliente" se cade nello stesso mese
    # della sua prima visita.
    df["tipo_cliente"] = (
        df["data"].dt.to_period("M") == df["data_prima_visita"].dt.to_period("M")
    ).map({True: "Nuovo cliente", False: "Cliente di ritorno"})
    return df, clienti, servizi


df, clienti, servizi = carica_dati()

# ---------------------------------------------------------------------------
# Intestazione e filtri
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Barbiere", page_icon="💈", layout="wide")
st.title("💈 Dashboard del negozio")

col_f1, col_f2, _ = st.columns([1, 1, 2])
with col_f1:
    periodo = st.selectbox(
        "Periodo",
        ["Ultimi 30 giorni", "Ultimi 90 giorni", "Ultimi 12 mesi", "Tutto lo storico"],
        index=2,
    )
with col_f2:
    categoria = st.selectbox(
        "Categoria servizio", ["Tutte"] + sorted(df["categoria"].unique())
    )

ultima_data = df["data"].max()
giorni_periodo = {"Ultimi 30 giorni": 30, "Ultimi 90 giorni": 90, "Ultimi 12 mesi": 365}
if periodo in giorni_periodo:
    inizio = ultima_data - timedelta(days=giorni_periodo[periodo])
else:
    inizio = df["data"].min()

sel = df[df["data"] >= inizio]
if categoria != "Tutte":
    sel = sel[sel["categoria"] == categoria]

completati = sel[sel["stato"] == "Completato"]

# Periodo precedente di pari lunghezza, per confrontare i KPI.
durata = ultima_data - inizio
prec = df[(df["data"] >= inizio - durata) & (df["data"] < inizio)]
if categoria != "Tutte":
    prec = prec[prec["categoria"] == categoria]
prec_completati = prec[prec["stato"] == "Completato"]

# ---------------------------------------------------------------------------
# KPI principali
# ---------------------------------------------------------------------------
def variazione(attuale: float, precedente: float) -> str | None:
    if precedente == 0:
        return None
    return f"{(attuale - precedente) / precedente:+.0%} vs periodo precedente"


incasso = completati["prezzo_pagato"].sum()
n_appuntamenti = len(completati)
n_clienti = completati["id_cliente"].nunique()
scontrino_medio = completati["prezzo_pagato"].mean() if n_appuntamenti else 0
tasso_no_show = (sel["stato"] == "No-show").mean() if len(sel) else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Incasso", f"€ {incasso:,.0f}",
          variazione(incasso, prec_completati["prezzo_pagato"].sum()))
k2.metric("Appuntamenti", f"{n_appuntamenti:,}",
          variazione(n_appuntamenti, len(prec_completati)))
k3.metric("Clienti serviti", f"{n_clienti:,}",
          variazione(n_clienti, prec_completati["id_cliente"].nunique()))
k4.metric("Scontrino medio", f"€ {scontrino_medio:.2f}")
k5.metric("Tasso no-show", f"{tasso_no_show:.1%}")

st.divider()

# ---------------------------------------------------------------------------
# Riga 1 — Incassi nel tempo + servizi più richiesti
# ---------------------------------------------------------------------------
c1, c2 = st.columns([3, 2])

with c1:
    st.subheader("Incassi mensili")
    mensile = completati.groupby("mese", as_index=False)["prezzo_pagato"].sum()
    fig = px.bar(mensile, x="mese", y="prezzo_pagato",
                 color_discrete_sequence=[BLU])
    fig.update_traces(marker_line_width=0,
                      hovertemplate="%{x|%b %Y}<br>€ %{y:,.0f}<extra></extra>")
    fig.update_yaxes(tickprefix="€ ")
    st.plotly_chart(stile_grafico(fig), use_container_width=True)

with c2:
    st.subheader("Servizi più richiesti")
    top_servizi = (
        completati.groupby("nome_servizio", as_index=False)
        .agg(n=("id_appuntamento", "count"), incasso=("prezzo_pagato", "sum"))
        .sort_values("n")
    )
    fig = px.bar(top_servizi, x="n", y="nome_servizio", orientation="h",
                 color_discrete_sequence=[BLU],
                 custom_data=["incasso"])
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="%{y}<br>%{x} appuntamenti · € %{customdata[0]:,.0f}<extra></extra>",
    )
    st.plotly_chart(stile_grafico(fig), use_container_width=True)

# ---------------------------------------------------------------------------
# Riga 2 — Nuovi clienti vs ritorni + canali di acquisizione
# ---------------------------------------------------------------------------
c3, c4 = st.columns([3, 2])

with c3:
    st.subheader("Clienti nuovi e di ritorno per mese")
    per_tipo = (
        completati.groupby(["mese", "tipo_cliente"])["id_cliente"]
        .nunique().reset_index(name="clienti")
    )
    fig = px.bar(
        per_tipo, x="mese", y="clienti", color="tipo_cliente",
        color_discrete_map={"Cliente di ritorno": BLU, "Nuovo cliente": ARANCIO},
        category_orders={"tipo_cliente": ["Cliente di ritorno", "Nuovo cliente"]},
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(legend_title=None, bargap=0.25)
    st.plotly_chart(stile_grafico(fig, mostra_legenda=True), use_container_width=True)

with c4:
    st.subheader("Come ci hanno conosciuto")
    canali = (
        completati.drop_duplicates("id_cliente")
        .groupby("canale_acquisizione", as_index=False)
        .agg(clienti=("id_cliente", "count"))
        .sort_values("clienti")
    )
    fig = px.bar(canali, x="clienti", y="canale_acquisizione", orientation="h",
                 color_discrete_sequence=[BLU])
    fig.update_traces(marker_line_width=0,
                      hovertemplate="%{y}: %{x} clienti<extra></extra>")
    st.plotly_chart(stile_grafico(fig), use_container_width=True)

# ---------------------------------------------------------------------------
# Riga 3 — Mappa affluenza (giorno × ora) + top clienti
# ---------------------------------------------------------------------------
c5, c6 = st.columns([3, 2])

with c5:
    st.subheader("Affluenza per giorno e orario")
    ordine_giorni = ["Mar", "Mer", "Gio", "Ven", "Sab"]
    affluenza = (
        completati[completati["giorno_settimana"].isin(ordine_giorni)]
        .groupby(["giorno_settimana", "ora_num"])
        .size().reset_index(name="n")
        .pivot(index="giorno_settimana", columns="ora_num", values="n")
        .reindex(ordine_giorni)
    )
    fig = px.imshow(
        affluenza,
        color_continuous_scale=SCALA_BLU,
        labels=dict(color="Appuntamenti"),
        aspect="auto",
    )
    fig.update_traces(
        hovertemplate="%{y} · ore %{x}:00<br>%{z} appuntamenti<extra></extra>"
    )
    fig.update_layout(coloraxis_colorbar=dict(title=None, thickness=12))
    st.plotly_chart(stile_grafico(fig), use_container_width=True)

with c6:
    st.subheader("Migliori clienti del periodo")
    top_clienti = (
        completati.groupby("cliente_completo")
        .agg(Visite=("id_appuntamento", "count"),
             Spesa=("prezzo_pagato", "sum"))
        .sort_values("Spesa", ascending=False)
        .head(10)
        .reset_index(names="Cliente")
    )
    top_clienti["Spesa"] = top_clienti["Spesa"].map("€ {:,.0f}".format)
    st.dataframe(top_clienti, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Dati di dettaglio (vista tabellare, utile anche per l'accessibilità)
# ---------------------------------------------------------------------------
with st.expander("Vedi i dati del periodo selezionato"):
    st.dataframe(
        sel[["data", "ora", "cliente_completo", "nome_servizio", "categoria",
             "stato", "prezzo_pagato", "metodo_pagamento"]]
        .sort_values(["data", "ora"], ascending=False),
        use_container_width=True, hide_index=True,
    )

st.caption(
    f"Dati dal {df['data'].min():%d/%m/%Y} al {df['data'].max():%d/%m/%Y} · "
    "negozio chiuso domenica e lunedì · dataset sintetico generato da genera_dataset.py"
)
