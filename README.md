# 💈 Negozio di parrucchieri — dataset e dashboard

Progetto di allenamento per data analysis: un dataset realistico dei clienti di
un negozio di parrucchieri/barbiere e una dashboard interattiva per monitorare
l'andamento dell'attività.

## Avvio rapido

```bash
pip install -r requirements.txt
python genera_dataset.py      # genera i CSV in data/ (già inclusi nel repo)
streamlit run dashboard.py    # apre la dashboard nel browser
```

## Struttura del progetto

```
├── genera_dataset.py   # genera il dataset sintetico
├── dashboard.py        # dashboard Streamlit
├── requirements.txt
└── data/
    ├── clienti.csv       # anagrafica clienti
    ├── servizi.csv       # listino servizi
    └── appuntamenti.csv  # storico appuntamenti (la tabella dei "fatti")
```

Le tre tabelle sono collegate come in un piccolo database relazionale:
`appuntamenti` contiene un `id_cliente` e un `id_servizio` che puntano alle
altre due tabelle. È lo stesso schema che troveresti in un gestionale vero.

## Dizionario dei dati

**clienti.csv**

| Colonna | Descrizione |
|---|---|
| `id_cliente` | identificativo univoco del cliente |
| `nome`, `cognome` | anagrafica |
| `anno_nascita` | per analisi sull'età della clientela |
| `canale_acquisizione` | come ha conosciuto il negozio (passaparola, Instagram, …) |
| `data_prima_visita` | prima volta che è venuto |

**servizi.csv**

| Colonna | Descrizione |
|---|---|
| `id_servizio` | identificativo del servizio |
| `nome_servizio`, `categoria` | es. "Taglio + barba", categoria "Taglio" |
| `prezzo_listino` | prezzo standard in euro |
| `durata_min` | durata in minuti (utile per analisi di capacità) |

**appuntamenti.csv**

| Colonna | Descrizione |
|---|---|
| `id_appuntamento` | identificativo, in ordine cronologico |
| `id_cliente`, `id_servizio` | collegamenti alle altre tabelle |
| `data`, `ora` | quando |
| `stato` | `Completato`, `No-show` (non si è presentato) o `Cancellato` |
| `prezzo_pagato` | quanto ha pagato davvero (0 se non completato, sconti inclusi) |
| `metodo_pagamento` | contanti, carta o Satispay |

## Cosa mostra la dashboard

- **KPI del periodo** con confronto sul periodo precedente: incasso,
  appuntamenti, clienti serviti, scontrino medio, tasso di no-show
- **Incassi mensili** e **servizi più richiesti**
- **Clienti nuovi vs di ritorno** mese per mese (per capire fidelizzazione e crescita)
- **Canali di acquisizione** dei clienti
- **Mappa di affluenza** per giorno della settimana e orario (per organizzare i turni)
- **Migliori clienti** del periodo e tabella di dettaglio dei dati

I filtri in alto (periodo e categoria di servizio) aggiornano tutta la pagina.

## Il dataset sintetico è "realistico" apposta

`genera_dataset.py` non estrae numeri a caso: simula i comportamenti veri di un
negozio, così le analisi che farai hanno pattern da scoprire.

- Negozio **chiuso domenica e lunedì**; venerdì e sabato sono i giorni di punta
- **Stagionalità**: dicembre pienissimo (feste), agosto mezzo vuoto (ferie)
- Ogni cliente ha un **ritmo di ritorno** suo (dai 21 ai 50 giorni) e un
  servizio abituale; alcuni clienti col tempo abbandonano (churn)
- Il negozio **cresce**: acquisisce sempre più nuovi clienti col passare dei mesi
- ~4% di no-show e ~5% di cancellazioni, sconti occasionali

Il seed è fisso (`random.seed(42)`): rilanciando lo script ottieni sempre lo
stesso dataset.

## Passare ai dati veri del negozio

Quando vorrai usare i dati di tuo padre:

1. Compila i tre CSV in `data/` con le stesse colonne (bastano Excel o Google
   Sheets, esportando in CSV). Se il negozio non prende appuntamenti, puoi
   registrare solo gli scontrini: `data`, `ora`, `servizio`, `prezzo`.
2. La dashboard continuerà a funzionare senza modifiche.
3. **Attenzione alla privacy**: nomi e telefoni dei clienti sono dati personali
   (GDPR). Per le analisi basta un ID anonimo — tieni l'anagrafica vera fuori
   da GitHub e non pubblicarla mai in un repo pubblico.

## Idee di analisi per allenarti

In ordine di difficoltà crescente:

1. Qual è il giorno con lo scontrino medio più alto? E il metodo di pagamento
   più usato il sabato?
2. Quanto vale in media un cliente nel suo primo anno (customer lifetime value)?
3. Quali canali di acquisizione portano i clienti che poi restano più fedeli?
4. Analisi di **retention per coorte**: dei clienti arrivati a settembre 2024,
   quanti erano ancora attivi dopo 3, 6, 12 mesi?
5. Dopo quanti giorni di assenza un cliente si può considerare "perso"? (utile
   per decidere quando mandare un messaggio di richiamo)
6. Previsione degli incassi del mese prossimo a partire dallo storico.
