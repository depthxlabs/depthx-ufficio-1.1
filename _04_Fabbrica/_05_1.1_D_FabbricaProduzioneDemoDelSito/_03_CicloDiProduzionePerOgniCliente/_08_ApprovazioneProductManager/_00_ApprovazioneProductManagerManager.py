"""Manager del passo 8: il product manager controlla che la demo rispetti la direzione fissa della fabbrica.

Le cose tecniche sono del collaudo basico (passo 7). Riceve la copia del template del passo 2 e il materiale del passo 3
(le recensioni, che sono degli ospiti). Prima i controlli fissi della pagina vista (passo 8.3: apertura intera, prima
sezione non spoglia, WhatsApp con il suo pulsante), poi la checklist fissa di Claude (passo 8.2). Passa o non passa,
senza note (Michele, 8/11/2026): GO solo se passano tutti e due; NOTGO con i soli punti non passati, che vanno alla
correzione del passo 10.
"""

from ._01_FotografieDellaDemo._00_FotografieDellaDemoManager import fotografieDellaDemoManager
from ._02_GiudizioEsteticoDiClaude._00_GiudizioEsteticoDiClaudeManager import giudizioEsteticoDiClaudeManager
from ._03_ControlliDellaPaginaVista._00_ControlliDellaPaginaVistaManager import controlliDellaPaginaVistaManager


def approvazioneProductManagerManager(copiaDelTemplate, materiale):
    fotografie = fotografieDellaDemoManager(copiaDelTemplate["sito"], copiaDelTemplate["cartellaDelClienteInCorso"])
    paginaVista = controlliDellaPaginaVistaManager(fotografie)
    giudizio = giudizioEsteticoDiClaudeManager(copiaDelTemplate["sito"], fotografie, materiale.get("recensioni") or [])
    note = dict(giudizio["note"])
    if paginaVista:
        note["paginaVista"] = paginaVista
    esito = "GO" if giudizio["esito"] == "GO" and not paginaVista else "NOTGO"
    return {"idCliente": materiale["idCliente"], "fotografie": fotografie, "esito": esito, "note": note if esito == "NOTGO" else {}}
