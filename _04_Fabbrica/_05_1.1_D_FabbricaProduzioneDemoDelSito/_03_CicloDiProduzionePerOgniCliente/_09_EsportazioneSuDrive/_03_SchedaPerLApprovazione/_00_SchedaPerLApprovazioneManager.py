"""Manager del passo 9.3: la scheda della demo per l'Approvazione del Centro Gestione (Michele, 11/11/2026)."""

from ._01_SchedaPerLApprovazione import schedaPerLApprovazione


def schedaPerLApprovazioneManager(scheda, copia, link):
    return schedaPerLApprovazione(scheda, copia, link)
