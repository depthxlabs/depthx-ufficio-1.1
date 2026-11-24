// Lettura dei CRM nuovi (cartella Drive "_01_CRM Linea 1.2"), in SOLA LETTURA.
// Uso: node _01_LetturaDeiFogliDaGoogleSheets.js ID_FOGLIO [ID_FOGLIO ...]
// Scrive su stdout un JSON { "<idFoglio>": { "righe": [[...], ...] } oppure { "errore": "..." } }.
// Il token arriva da libreria.js del Centro Gestione, resta in memoria e non si stampa mai.
// Al massimo una lettura al secondo; risposta 429: attesa di 15 secondi e ripetizione.
"use strict";
const libreria = require("C:/_02_DepthXSoftware/_01_CentroGestioneDepthX/_02_ModuliJavascriptCentroGestione/libreria.js");
const SCHEDA = "Lista";
const INTERVALLO = SCHEDA + "!A1:AZ";
const attendi = (ms) => new Promise((r) => setTimeout(r, ms));
const sicuro = (t) => String(t || "").replace(/ya29\.[0-9A-Za-z_\-.]+/g, "***").replace(/(token|key)=[^&\s"']+/gi, "$1=***").slice(0, 300);

async function leggi(id) {
  for (let giro = 0; giro < 8; giro++) {
    let r;
    try {
      r = await fetch("https://sheets.googleapis.com/v4/spreadsheets/" + encodeURIComponent(id) + "/values/" + encodeURIComponent(INTERVALLO) + "?majorDimension=ROWS",
        { headers: { Authorization: "Bearer " + await libreria.chiave() }, signal: AbortSignal.timeout(60000) });
    } catch (e) { await attendi(5000); continue; }
    if (r.status === 429) { await attendi(15000); continue; }
    if ([500, 502, 503, 504].includes(r.status)) { await attendi(5000 * (giro + 1)); continue; }
    const j = await r.json().catch(() => ({}));
    if (!r.ok) return { errore: "risposta " + r.status + " " + sicuro((j.error || {}).message) };
    return { righe: j.values || [] };
  }
  return { errore: "lettura non riuscita dopo le ripetizioni" };
}

(async () => {
  const esito = {};
  const ids = process.argv.slice(2);
  for (let n = 0; n < ids.length; n++) {
    if (n) await attendi(1100);
    try { esito[ids[n]] = await leggi(ids[n]); } catch (e) { esito[ids[n]] = { errore: sicuro(e.message) }; }
  }
  process.stdout.write(JSON.stringify(esito));
})();
