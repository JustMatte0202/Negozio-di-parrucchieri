"""
Genera un dataset sintetico ma realistico per un negozio di parrucchieri/barbiere.

Produce tre file CSV nella cartella `data/`:
  - servizi.csv       il listino dei servizi offerti
  - clienti.csv       l'anagrafica clienti
  - appuntamenti.csv  lo storico degli appuntamenti (la tabella dei "fatti")

Questa struttura a tre tabelle è volutamente quella di un piccolo database
relazionale: `appuntamenti` si collega a `clienti` e `servizi` tramite gli ID.
Quando avrai i dati veri di tuo padre, ti basterà riempire questi stessi file
con le stesse colonne e la dashboard continuerà a funzionare.

Uso:
    python genera_dataset.py
"""

import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

# Seed fisso: rilanciando lo script si ottiene sempre lo stesso dataset.
random.seed(42)

DATA_INIZIO = date(2024, 8, 1)
DATA_FINE = date(2026, 8, 15)
CARTELLA_OUTPUT = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# 1. Listino servizi
# ---------------------------------------------------------------------------
SERVIZI = [
    # (id, nome, categoria, prezzo, durata in minuti, popolarità relativa)
    (1, "Taglio uomo", "Taglio", 18.0, 30, 40),
    (2, "Taglio + barba", "Taglio", 26.0, 45, 25),
    (3, "Barba", "Barba", 12.0, 20, 12),
    (4, "Rasatura tradizionale", "Barba", 15.0, 30, 5),
    (5, "Taglio bambino", "Taglio", 12.0, 25, 8),
    (6, "Shampoo + styling", "Styling", 10.0, 15, 4),
    (7, "Colorazione", "Colore", 35.0, 60, 3),
    (8, "Trattamento cute", "Trattamenti", 22.0, 30, 3),
]

NOMI = [
    "Marco", "Luca", "Andrea", "Francesco", "Alessandro", "Matteo", "Davide",
    "Simone", "Giuseppe", "Antonio", "Giovanni", "Riccardo", "Stefano",
    "Federico", "Paolo", "Gabriele", "Lorenzo", "Salvatore", "Enrico", "Dario",
    "Nicola", "Tommaso", "Fabio", "Claudio", "Vincenzo", "Emanuele", "Pietro",
    "Sergio", "Massimo", "Filippo",
]
COGNOMI = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
    "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca",
    "Mancini", "Costa", "Giordano", "Rizzo", "Lombardi", "Moretti",
    "Barbieri", "Fontana", "Santoro", "Mariani", "Rinaldi", "Caruso",
    "Ferrara", "Galli", "Martini", "Leone",
]
CANALI = ["Passaparola", "Instagram", "Google", "Passava davanti"]
PESI_CANALI = [45, 25, 15, 15]
METODI_PAGAMENTO = ["Contanti", "Carta", "Satispay"]
PESI_PAGAMENTO = [45, 40, 15]

# Il negozio è chiuso domenica (6) e lunedì (0), come molti barbieri in Italia.
GIORNI_CHIUSURA = {0, 6}

# Peso relativo dei giorni di apertura: il venerdì e soprattutto il sabato
# sono i giorni di punta.
PESO_GIORNO = {1: 0.8, 2: 0.9, 3: 1.0, 4: 1.4, 5: 1.9}

# Stagionalità mensile: agosto mezzo vuoto (ferie), dicembre pienissimo (feste).
PESO_MESE = {1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.05, 6: 1.1,
             7: 0.95, 8: 0.55, 9: 1.05, 10: 1.0, 11: 1.05, 12: 1.45}

# Fasce orarie di apertura (9-13, 15-19.30) con i relativi pesi:
# tarda mattinata e tardo pomeriggio sono i momenti più richiesti.
ORARI = [(9, 0.7), (10, 1.0), (11, 1.2), (12, 1.0),
         (15, 0.8), (16, 1.0), (17, 1.3), (18, 1.4), (19, 0.9)]


def giorno_aperto(giorno: date) -> bool:
    return giorno.weekday() not in GIORNI_CHIUSURA


def peso_giornata(giorno: date) -> float:
    """Quanto è 'appetibile' una certa giornata per un appuntamento."""
    if not giorno_aperto(giorno):
        return 0.0
    peso = PESO_GIORNO[giorno.weekday()] * PESO_MESE[giorno.month]
    # Le due settimane prima di Natale sono ancora più piene.
    if giorno.month == 12 and 10 <= giorno.day <= 24:
        peso *= 1.3
    # Settimana di Ferragosto: quasi deserto.
    if giorno.month == 8 and 10 <= giorno.day <= 20:
        peso *= 0.4
    return peso


def scegli_orario() -> time:
    ore, pesi = zip(*ORARI)
    ora = random.choices(ore, weights=pesi)[0]
    minuti = random.choice([0, 15, 30, 45])
    return time(ora, minuti)


def genera_clienti() -> list[dict]:
    """Crea l'anagrafica: il negozio parte con uno zoccolo duro di clienti
    storici e ne acquisisce di nuovi ogni mese, con una crescita leggera."""
    clienti = []
    id_cliente = 1
    coppie_usate = set()

    def nuovo_cliente(prima_visita: date) -> dict:
        nonlocal id_cliente
        while True:
            nome, cognome = random.choice(NOMI), random.choice(COGNOMI)
            if (nome, cognome) not in coppie_usate:
                coppie_usate.add((nome, cognome))
                break
        anno_nascita = random.randint(1955, prima_visita.year - 5)
        cliente = {
            "id_cliente": id_cliente,
            "nome": nome,
            "cognome": cognome,
            "anno_nascita": anno_nascita,
            "canale_acquisizione": random.choices(CANALI, weights=PESI_CANALI)[0],
            "data_prima_visita": prima_visita,
            # Ogni quanto torna in media (in giorni): chi cura la barba torna
            # più spesso di chi fa solo il taglio.
            "intervallo_medio": random.choice([21, 25, 28, 30, 35, 42, 50]),
            # Probabilità di "sparire" dopo ogni visita (churn).
            "prob_abbandono": random.uniform(0.01, 0.10),
            # Servizio abituale del cliente.
            "servizio_abituale": random.choices(
                [s[0] for s in SERVIZI], weights=[s[5] for s in SERVIZI]
            )[0],
        }
        id_cliente += 1
        return cliente

    # Clienti storici, già abituali quando inizia lo storico dei dati.
    for _ in range(90):
        giorno = DATA_INIZIO + timedelta(days=random.randint(0, 45))
        clienti.append(nuovo_cliente(giorno))

    # Nuovi clienti mese per mese, con una crescita graduale del negozio.
    mese = date(DATA_INIZIO.year, DATA_INIZIO.month, 1)
    indice_mese = 0
    while mese <= DATA_FINE:
        base = 6 + indice_mese * 0.25          # crescita: ~6 → ~13 nuovi/mese
        n_nuovi = max(1, round(random.gauss(base * PESO_MESE[mese.month], 1.5)))
        for _ in range(n_nuovi):
            giorno = mese + timedelta(days=random.randint(0, 27))
            if DATA_INIZIO + timedelta(days=46) <= giorno <= DATA_FINE:
                clienti.append(nuovo_cliente(giorno))
        indice_mese += 1
        mese = (mese.replace(day=28) + timedelta(days=4)).replace(day=1)

    return clienti


def genera_appuntamenti(clienti: list[dict]) -> list[dict]:
    """Simula la vita di ogni cliente: prima visita, poi ritorni periodici
    finché non abbandona (o finché non finisce il periodo osservato)."""
    servizi = {s[0]: s for s in SERVIZI}
    appuntamenti = []
    id_app = 1

    for cliente in clienti:
        giorno = cliente["data_prima_visita"]
        attivo = True
        while attivo and giorno <= DATA_FINE:
            # Sposta l'appuntamento sul giorno di apertura "migliore" vicino.
            candidati = [giorno + timedelta(days=d) for d in range(-3, 4)]
            candidati = [g for g in candidati
                         if DATA_INIZIO <= g <= DATA_FINE and giorno_aperto(g)]
            if candidati:
                giorno_app = random.choices(
                    candidati, weights=[peso_giornata(g) for g in candidati]
                )[0]

                # Nel 75% dei casi fa il suo servizio abituale, altrimenti varia.
                if random.random() < 0.75:
                    id_servizio = cliente["servizio_abituale"]
                else:
                    id_servizio = random.choices(
                        [s[0] for s in SERVIZI], weights=[s[5] for s in SERVIZI]
                    )[0]
                servizio = servizi[id_servizio]

                stato = random.choices(
                    ["Completato", "No-show", "Cancellato"],
                    weights=[91, 4, 5],
                )[0]
                prezzo = servizio[3] if stato == "Completato" else 0.0
                # Ogni tanto uno sconto (studenti, promozioni, arrotondamenti).
                if stato == "Completato" and random.random() < 0.08:
                    prezzo = round(prezzo * random.choice([0.8, 0.9]), 2)

                appuntamenti.append({
                    "id_appuntamento": id_app,
                    "id_cliente": cliente["id_cliente"],
                    "id_servizio": id_servizio,
                    "data": giorno_app,
                    "ora": scegli_orario(),
                    "stato": stato,
                    "prezzo_pagato": prezzo,
                    "metodo_pagamento": (
                        random.choices(METODI_PAGAMENTO, weights=PESI_PAGAMENTO)[0]
                        if stato == "Completato" else ""
                    ),
                })
                id_app += 1

            # Il cliente decide se tornare, e quando.
            if random.random() < cliente["prob_abbandono"]:
                attivo = False
            else:
                intervallo = max(10, round(random.gauss(
                    cliente["intervallo_medio"], cliente["intervallo_medio"] * 0.25
                )))
                giorno = giorno + timedelta(days=intervallo)

    appuntamenti.sort(key=lambda a: (a["data"], a["ora"]))
    # Riassegna gli ID in ordine cronologico, come farebbe un gestionale.
    for nuovo_id, app in enumerate(appuntamenti, start=1):
        app["id_appuntamento"] = nuovo_id
    return appuntamenti


def scrivi_csv(percorso: Path, righe: list[dict], colonne: list[str]) -> None:
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colonne)
        writer.writeheader()
        for riga in righe:
            writer.writerow({c: riga[c] for c in colonne})


def main() -> None:
    CARTELLA_OUTPUT.mkdir(exist_ok=True)

    scrivi_csv(
        CARTELLA_OUTPUT / "servizi.csv",
        [{"id_servizio": s[0], "nome_servizio": s[1], "categoria": s[2],
          "prezzo_listino": s[3], "durata_min": s[4]} for s in SERVIZI],
        ["id_servizio", "nome_servizio", "categoria", "prezzo_listino", "durata_min"],
    )

    clienti = genera_clienti()
    scrivi_csv(
        CARTELLA_OUTPUT / "clienti.csv",
        clienti,
        ["id_cliente", "nome", "cognome", "anno_nascita",
         "canale_acquisizione", "data_prima_visita"],
    )

    appuntamenti = genera_appuntamenti(clienti)
    scrivi_csv(
        CARTELLA_OUTPUT / "appuntamenti.csv",
        appuntamenti,
        ["id_appuntamento", "id_cliente", "id_servizio", "data", "ora",
         "stato", "prezzo_pagato", "metodo_pagamento"],
    )

    completati = [a for a in appuntamenti if a["stato"] == "Completato"]
    incasso = sum(a["prezzo_pagato"] for a in completati)
    print(f"Generati {len(clienti)} clienti e {len(appuntamenti)} appuntamenti "
          f"({len(completati)} completati, incasso totale €{incasso:,.2f}) "
          f"dal {DATA_INIZIO} al {DATA_FINE}.")


if __name__ == "__main__":
    main()
