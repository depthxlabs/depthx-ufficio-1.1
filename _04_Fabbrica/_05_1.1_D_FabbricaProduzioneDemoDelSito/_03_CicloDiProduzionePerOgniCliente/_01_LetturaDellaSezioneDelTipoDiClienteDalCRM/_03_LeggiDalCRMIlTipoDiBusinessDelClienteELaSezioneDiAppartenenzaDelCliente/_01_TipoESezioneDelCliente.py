"""Passo 1.3: il tipo di business del cliente e la sezione del CRM a cui appartiene.

Il tipo (Hotel, B&B, Agriturismo, Casa Vacanza) sceglie il template nel passo 2.
La sezione dice il punto di partenza: Section 1 senza sito, 2 e 3 con un sito da superare, 4 su misura.
"""


def tipoESezioneDelCliente(idCliente, cartellaSuDrive, statoNelMotore):
    numero = "".join(carattere for carattere in (cartellaSuDrive.get("sezione") or "")[:4] if carattere.isdigit())
    return {"idCliente": idCliente, "nome": statoNelMotore.get("nome", ""), "tipo": cartellaSuDrive.get("tipo", ""),
            "sezione": int(numero or 0), "sezioneCompleta": cartellaSuDrive.get("sezione", ""),
            "industria": statoNelMotore.get("industria", ""), "idDrive": cartellaSuDrive["idDrive"],
            "cartella": cartellaSuDrive.get("cartella", "")}
