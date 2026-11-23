"""RAPPORTO DI UNICITÀ CON UN MODELLO GRATUITO, Linea 1.1 Outbound Websites, Download materiale clienti.

La stessa domanda del rapporto fatto con Claude, mandata a un modello gratuito di GitHub Models (con il GITHUB_TOKEN del workflow).
Regola: niente inventato. Ogni settore ha una citazione copiata parola per parola dal materiale; il codice la cerca nel materiale vero
e scarta il settore se non la trova.
"""
import json, os, re, time, unicodedata
import requests

MODELLO = os.environ.get("MODELLO_GRATUITO", "openai/gpt-4.1-mini")
INDIRIZZO = "https://models.github.ai/inference/chat/completions"
SISTEMA = "Rispondi solo con un oggetto JSON valido, in italiano, senza altro testo."
LUNGHEZZA_MINIMA_DI_UNA_CITAZIONE = 12
DOMANDA = (
    "Materiale vero di {nome} ({tipo}); ogni riga inizia con la fonte tra [ ]. Scegli da 3 a 8 settori in cui questa struttura ha qualcosa "
    "di caratteristico e concreto (nome del settore di 1-3 parole, per esempio ambiente, colazione, cocktail). Per ognuno una frase di massimo 8 parole "
    "e una citazione copiata parola per parola dal materiale (5-20 parole). Niente inventato, niente di generico. "
    "JSON: {{\"sintesi\":\"1 frase\",\"settori\":{{\"nome del settore\":{{\"frase\":\"...\",\"citazione\":\"...\"}}}}}}\n\n{materiale}"
)


def normalizza(testo):
    testo = unicodedata.normalize("NFKC", str(testo or "")).lower()
    testo = re.sub(r"[\"'«»“”‘’`´]", "", testo)
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", testo)).strip()


def materiale(crm, recensioni, massimo=8000):
    righe = [f"[CRM {k}] {v}" for k, v in crm.items() if isinstance(v, (str, int, float)) and str(v).strip()][:25]
    for n, r in enumerate(sorted([r for r in recensioni if (r.get("testo") or "").strip()], key=lambda r: -len(r["testo"])), start=1):
        righe.append(f"[recensione {n} · {r.get('autore') or 'ospite'}] " + re.sub(r"\s+", " ", r["testo"])[:350])
    testo, uscita = 0, []
    for riga in righe:
        if testo + len(riga) > massimo:
            break
        uscita.append(riga); testo += len(riga) + 1
    return "\n".join(uscita)


def chiedi(domanda):
    """Una domanda al modello gratuito; restituisce (testo, codice HTTP, limiti rimasti)."""
    r = requests.post(INDIRIZZO, timeout=120, headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
                      json={"model": MODELLO, "messages": [{"role": "system", "content": SISTEMA}, {"role": "user", "content": domanda}], "temperature": 0.2})
    limiti = {k: v for k, v in r.headers.items() if "ratelimit" in k.lower()}
    if r.status_code != 200:
        return "", r.status_code, limiti
    return r.json()["choices"][0]["message"]["content"], 200, limiti


def rapporto(nome, tipo, crm, recensioni):
    testo = materiale(crm, recensioni)
    inizio = time.time()
    risposta, codice, limiti = chiedi(DOMANDA.format(nome=nome, tipo=tipo, materiale=testo))
    trovato = re.search(r"\{[\s\S]*\}", risposta or "")
    try:
        dati = json.loads(trovato.group(0)) if trovato else {}
    except ValueError:
        dati = {}
    vero, buoni, scartati = normalizza(testo), {}, []
    for settore, voce in (dati.get("settori") or {}).items():
        citazione = normalizza((voce or {}).get("citazione"))
        if len(citazione) >= LUNGHEZZA_MINIMA_DI_UNA_CITAZIONE and citazione in vero:
            buoni[settore] = voce
        else:
            scartati.append(settore)
    return {"modello": MODELLO, "codiceHttp": codice, "secondi": round(time.time() - inizio, 1), "limiti": limiti,
            "sintesi": dati.get("sintesi", ""), "settori": buoni, "settoriScartatiPerCitazioneNonTrovata": scartati}
