"""Il programma wrangler di Cloudflare installato sul server, lanciato nella cartella del Worker delle demo.

Wrangler pubblica il Worker e legge e scrive il registro delle demo (il KV con il nome TRACCIAMENTO in wrangler.toml).
Se l'accesso a Cloudflare è scaduto o la rete ha un intoppo, si prova fino a 5 volte in tutto, con un'attesa che cresce:
una fabbrica che lavora di notte non si ferma per un errore momentaneo di Cloudflare (8/11/2026). Una scheda che non
esiste (404) non si riprova.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

CARTELLA_DEL_WORKER = Path(__file__).absolute().parent / "_01_PercorsoDelleDemoSuCloudflare"
TENTATIVI_IN_PIU = 4  # 5 tentativi in tutto (Michele, 8/11/2026)


def programmaWrangler(*argomenti, attesa=300, cartella=CARTELLA_DEL_WORKER):
    # se il PATH del processo non ha la cartella di npm, wrangler si cerca dove npm lo installa (11/11/2026)
    installato = Path(os.environ.get("APPDATA", "")) / "npm" / "wrangler.cmd"
    programma = shutil.which("wrangler.cmd") or shutil.which("wrangler") or (str(installato) if installato.is_file() else "")
    if not programma:
        raise RuntimeError("wrangler non è installato sul server")
    ambiente = {**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0", "WRANGLER_SEND_METRICS": "false"}
    lancia = lambda: subprocess.run([programma, *argomenti], capture_output=True, text=True, encoding="utf-8",
                                    errors="ignore", cwd=cartella, env=ambiente, timeout=attesa,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
    esito = lancia()
    for volta in range(TENTATIVI_IN_PIU):
        if esito.returncode == 0 or "404: Not Found" in esito.stdout + esito.stderr:
            break
        time.sleep(10 * (volta + 1))
        esito = lancia()
    return esito
