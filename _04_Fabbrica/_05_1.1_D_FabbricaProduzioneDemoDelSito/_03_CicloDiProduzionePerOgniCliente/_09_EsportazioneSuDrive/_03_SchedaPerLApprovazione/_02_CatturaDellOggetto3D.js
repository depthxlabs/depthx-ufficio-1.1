/* Passo 9.3: la cattura dell'oggetto 3D che gira, per la pagina Approvazione (Michele, 12/11/2026, task #681).
   Uso: node _02_CatturaDellOggetto3D.js <chrome> <cartellaDelProfilo> <pagina> <larghezza> <altezza> <telefono 0|1> <cartellaDeiFotogrammi> <fotogrammi>
   Chrome parte senza finestra; la pagina si apre, si porta l'oggetto 3D al centro dello schermo, si ferma il suo giro
   automatico e lo si gira a passi uguali per un giro intero (davanti e dietro, il dado tutte le facce), con le stesse
   formule di pacchetto.js: ogni passo è un fotogramma JPEG ritagliato sul riquadro dell'oggetto (f00.jpg, f01.jpg, ...).
   Il giro è chiuso: l'ultimo fotogramma si lega al primo, così l'anteprima gira senza scatti. Stampa le misure in JSON. */
"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const [chrome, profilo, pagina, larghezza, altezza, telefono, arrivo, quanti] = process.argv.slice(2);
const L = parseInt(larghezza, 10), A = parseInt(altezza, 10), mobile = telefono === "1", N = parseInt(quanti, 10) || 36;
const aspetta = (t) => new Promise((r) => setTimeout(r, t));

(async () => {
  const processo = spawn(chrome, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--renderer-process-limit=2", "--js-flags=--max-old-space-size=384",
    "--disable-extensions", "--mute-audio", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run",
    "--lang=it-IT", "--accept-lang=it-IT,it", "--remote-debugging-port=0", "--user-data-dir=" + profilo, "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
  const chiudi = () => { try { processo.kill(); } catch (e) { /* già chiuso */ } };
  const limite = setTimeout(() => { console.error("tempo scaduto"); chiudi(); process.exit(1); }, 150000);
  try {
    let porta = null, errori = "";
    processo.stderr.on("data", (d) => { errori += d; const m = /DevTools listening on ws:\/\/[^:]+:(\d+)/.exec(errori); if (m) porta = m[1]; });
    for (let i = 0; i < 100 && !porta; i++) await aspetta(100);
    if (!porta) throw new Error("Chrome non risponde");
    const pagine = await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json();
    const ws = new WebSocket(pagine.find((p) => p.type === "page").webSocketDebuggerUrl);
    await new Promise((r, e) => { ws.onopen = r; ws.onerror = e; });
    let numero = 0; const attese = new Map(); const eventi = [];
    ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && attese.has(d.id)) { attese.get(d.id)(d); attese.delete(d.id); } else eventi.push(d.method); };
    const invia = (method, params = {}) => new Promise((r) => { const id = ++numero; attese.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
    const valuta = async (e) => { const r = await invia("Runtime.evaluate", { expression: e, returnByValue: true, awaitPromise: true }); if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.text); return r.result.result.value; };
    await invia("Page.enable");
    await invia("Emulation.setDeviceMetricsOverride", { width: L, height: A, deviceScaleFactor: 1, mobile });
    await invia("Page.navigate", { url: pagina });
    for (let i = 0; i < 300 && !eventi.includes("Page.loadEventFired"); i++) await aspetta(100);
    await aspetta(1200);
    /* l'oggetto 3D visibile (la variante mostrata), portato al centro dello schermo; le foto e i caratteri arrivano */
    const trovato = await valuta(`(() => {
      const s = [...document.querySelectorAll("[data-3d]")].find((x) => x.getClientRects().length && x.getBoundingClientRect().width > 40);
      if (!s) return false;
      s.scrollIntoView({ block: "center" }); window.__scena3d = s; return true; })()`);
    if (!trovato) throw new Error("nella pagina non c'è l'oggetto 3D ([data-3d])");
    await aspetta(1800);
    await valuta("document.fonts ? document.fonts.ready.then(() => true) : true");
    /* si ferma il giro automatico di pacchetto.js: il prossimo requestAnimationFrame non riparte più */
    await valuta("window.requestAnimationFrame = function () { return 0; }; true");
    await aspetta(200);
    const r = await valuta(`(() => { const s = window.__scena3d; s.scrollIntoView({ block: "center" }); const b = s.getBoundingClientRect();
      return { x: b.left + scrollX, y: b.top + scrollY, l: b.width, a: b.height, dado: s.getAttribute("data-asse") === "xy" }; })()`);
    await aspetta(300);
    const m = 10, x = Math.max(0, Math.floor(r.x - m)), y = Math.max(0, Math.floor(r.y - m));
    const clip = { x, y, width: Math.min(L - x, Math.ceil(r.l + 2 * m)), height: Math.ceil(r.a + 2 * m), scale: 1 };
    fs.mkdirSync(arrivo, { recursive: true });
    for (let k = 0; k < N; k++) {
      /* le formule di pacchetto.js (disegna), con l'inclinazione legata al giro perché il giro sia chiuso */
      await valuta(`(() => { const s = window.__scena3d, o = s.firstElementChild, f = ${k} / ${N}, a = 360 * f;
        const rx = s.getAttribute("data-asse") === "xy" ? 18 * Math.sin(2 * Math.PI * f) - 14 : 6 * Math.sin(2 * Math.PI * f);
        o.style.transform = "rotateX(" + rx.toFixed(2) + "deg) rotateY(" + a.toFixed(2) + "deg)";
        o.style.setProperty("--luce", (a / 360 * 200 - 50).toFixed(1) + "%");
        s.style.setProperty("--ombra", s.getAttribute("data-asse") === "xy" ? "0.75" : (0.25 + 0.75 * Math.abs(Math.cos(a * Math.PI / 180))).toFixed(3));
        return true; })()`);
      await aspetta(40);
      const foto = await invia("Page.captureScreenshot", { format: "jpeg", quality: 85, clip });
      if (!foto.result || !foto.result.data) throw new Error("fotogramma non riuscito");
      fs.writeFileSync(path.join(arrivo, `f${String(k).padStart(2, "0")}.jpg`), Buffer.from(foto.result.data, "base64"));
    }
    console.log(JSON.stringify({ fotogrammi: N, larghezza: clip.width, altezza: clip.height, dado: r.dado }));
    ws.close();
  } finally { clearTimeout(limite); chiudi(); }
})().catch((e) => { console.error(String(e && e.message || e)); process.exit(1); });
