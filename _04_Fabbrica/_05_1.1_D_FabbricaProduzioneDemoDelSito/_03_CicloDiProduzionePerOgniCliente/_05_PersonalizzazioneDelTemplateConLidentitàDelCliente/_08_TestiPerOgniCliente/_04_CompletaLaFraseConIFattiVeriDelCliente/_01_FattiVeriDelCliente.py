"""I fatti veri del cliente che completano le graffe delle frasi: nome, tipo, posizione, contatti e link.

Vengono dai dati del CRM e dalla scheda Google del passo 3.5 e dal tipo del CRM del passo 1; il voto mai, perché nel
sito delle recensioni restano solo i testi (Michele, 8/11/2026); la regione dalla sigla della provincia (_03_RegioniDelleProvince.json); l'anno corrente per il piede. Un fatto che non c'è non entra:
la frase che lo chiede non si usa. Nessun fatto si inventa.
"""

import datetime
import json
import re
from pathlib import Path
from urllib.parse import quote_plus

FILE_DELLE_REGIONI = Path(__file__).absolute().parent / "_03_RegioniDelleProvince.json"

TIPO_DAL_CRM = {"hotel": "Hotel", "b&b": "B&B", "agriturism": "Agriturismo", "case vacanz": "Casa vacanza"}
PAROLE_DEL_TIPO = re.compile(r"^(hotel|albergo|ristorante|pizzeria|locanda|b&b|bnb|bed and breakfast|agriturismo|"
                             r"casa vacanze?|casa|villa|residence|affittacamere)\s+", re.I)


def fattiVeriDelCliente(datiUnici, schedaDelCliente):
    crm = datiUnici["crm"]
    nome = (crm.get("nome") or (datiUnici["schedaGoogle"].get("displayName") or {}).get("text") or "").strip()
    # il nome breve si ferma prima di " - ", " | " o " · ": "La Portesina - Casa Vacanza a Mantova" diventa "La Portesina" (Michele, 9/11/2026)
    nomeBreve = re.split(r"\s+[-\u2013|\u00b7]\s+", nome)[0].strip() or nome
    while PAROLE_DEL_TIPO.match(nomeBreve):
        nomeBreve = PAROLE_DEL_TIPO.sub("", nomeBreve, count=1)
    tipo = next((v for k, v in TIPO_DAL_CRM.items() if k in (schedaDelCliente.get("tipo") or "").lower()), "")
    telefono = (crm.get("telefono") or crm.get("cellulare") or "").strip()
    placeId = (crm.get("googleMaps") or "").strip()
    placeId = placeId if placeId.startswith("ChIJ") else ""
    ricerca = quote_plus(" ".join(v for v in (nome, crm.get("via"), crm.get("comune")) if v))
    provincia = (crm.get("provincia") or "").strip().upper()
    regioni = json.loads(FILE_DELLE_REGIONI.read_text(encoding="utf-8-sig"))
    regione = next((r for r, sigle in regioni.items() if isinstance(sigle, list) and provincia in sigle), "")
    whatsapp = ""
    for numero in (crm.get("cellulare"), crm.get("telefono")):
        cifre = re.sub(r"\D", "", numero or "")
        cifre = cifre[2:] if cifre.startswith("39") and len(cifre) > 10 else cifre
        if cifre.startswith("3") and 9 <= len(cifre) <= 10:
            whatsapp = "39" + cifre
            break
    fatti = {
        "whatsapp": whatsapp, "regione": regione, "annoCorrente": datetime.date.today().year,
        # il nome completo nelle frasi, con " · " al posto del trattino storto del font (Michele, 9/11/2026)
        "nomestruttura": re.sub(r"\s+[-–—]\s+", " · ", nome), "nomeBreve": nomeBreve or nome, "tipo": tipo,
        "comune": crm.get("comune"), "via": crm.get("via"), "cap": crm.get("cap"), "provincia": crm.get("provincia"),
        "telefono": telefono, "telefonoLink": re.sub(r"[^\d+]", "", telefono), "email": crm.get("email"),
        "facebook": crm.get("facebook"), "instagram": crm.get("instagram"),
        "linkRecensioni": (f"https://search.google.com/local/reviews?placeid={placeId}" if placeId
                           else f"https://www.google.com/search?q={quote_plus(nome + ' recensioni')}"),
        "linkIndicazioni": f"https://www.google.com/maps/dir/?api=1&destination={ricerca}" if ricerca else "",
    }
    return {chiave: str(valore).strip() for chiave, valore in fatti.items() if valore and str(valore).strip()}
