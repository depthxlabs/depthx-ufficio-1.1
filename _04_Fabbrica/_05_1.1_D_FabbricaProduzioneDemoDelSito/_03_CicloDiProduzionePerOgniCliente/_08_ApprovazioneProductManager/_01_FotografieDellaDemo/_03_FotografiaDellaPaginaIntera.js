/* Passo 8.1: la fotografia della pagina intera, dall'alto al basso, con uno schermo vero (per esempio 390x844 sul telefono).
   Uso: node _03_FotografiaDellaPaginaIntera.js <chrome> <cartellaDelProfilo> <paginaFile> <larghezza> <altezza> <telefono 0|1> <fotografia.png> <millisecondi>
   Chrome parte senza finestra con il protocollo di controllo; la pagina si carica con "riduci movimento", si scorre fino in
   fondo (le foto che si caricano allo scorrere arrivano) e si fotografa intera. */
"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const [chrome, profilo, pagina, larghezza, altezza, telefono, arrivo, attesa] = process.argv.slice(2);
const L = parseInt(larghezza, 10), A = parseInt(altezza, 10), mobile = telefono === "1", ms = parseInt(attesa, 10) || 6000;
const aspetta = (t) => new Promise((r) => setTimeout(r, t));

/* Le misure della pagina vista, prese nella pagina con la pagina in cima:
   - apertura: le foto grandi del primo schermo e quanta parte se ne vede;
   - sezioni: per ogni sezione con un titolo, le parole e le frasi dei testi (senza pulsanti, link, moduli e recensioni);
   - whatsapp: le frasi che nominano WhatsApp e se nella loro sezione c'è un pulsante o un link WhatsApp visibile. */
function misureDellaPagina() {
  const H = window.innerHeight, W = window.innerWidth;
  const visibile = (el) => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden" && getComputedStyle(el).opacity !== "0";
  const apertura = [...document.querySelectorAll("img, video")].filter(visibile).map((el) => el.getBoundingClientRect())
    .filter((r) => r.width >= W * 0.5 && r.height >= 120 && r.top < H * 0.25 && r.bottom > 0) /* solo la foto che apre lo schermo, non quella della sezione dopo che spunta in fondo */
    .map((r) => ({ alto: Math.round(r.top), basso: Math.round(r.bottom), schermo: H, parteVista: Math.round(100 * (Math.min(r.bottom, H) - Math.max(r.top, 0)) / r.height) }));
  const testoProprio = (el) => [...el.childNodes].map((n) => n.nodeType === 3 ? n.textContent : (n.nodeType === 1 && (!n.matches("a, button, label, select, input") || n.matches("a.telefono-collegato")) ? testoProprio(n) : "")).join(" ");
  const sezioni = [...document.querySelectorAll("section")].filter((s) => visibile(s) && s.querySelector("h1, h2") && !s.querySelector("blockquote, form, iframe, h1, [data-3d]") && !/-in-breve$/.test(s.id || "")) /* le anteprime della Home sono brevi apposta (Michele, 11/11/2026) */
    .map((s) => {
      const testo = [...s.querySelectorAll("p, li, dd")].filter(visibile).filter((el) => !el.closest("a, button, form")).map(testoProprio).join(" ").replace(/\s+/g, " ").trim();
      const h = s.querySelector("h2");
      return { titolo: h ? h.innerText.trim() : "", parole: testo ? testo.split(" ").length : 0, frasi: (testo.match(/[.!?:](\s|$)/g) || []).length, testo: testo.slice(0, 300) };
    });
  const whatsapp = [...document.querySelectorAll("p, li, span, dd, div, h2, h3")].filter(visibile)
    .filter((el) => /whatsapp/i.test([...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ")) && !el.closest("a, button"))
    .map((el) => {
      const zona = el.closest("section, footer, header, nav, aside") || document.body;
      const pulsante = [...zona.querySelectorAll("a, button")].filter(visibile)
        .some((b) => /wa\.me|whatsapp/i.test(b.getAttribute("href") || "") || /whatsapp/i.test(b.innerText || ""));
      return { frase: el.innerText.trim().slice(0, 200), pulsante };
    });
  /* l'oggetto 3D: ogni faccia con una scritta che esce dai suoi bordi (Michele, 11/11/2026: "la scritta viene sotto") */
  const oggetto3d = [...document.querySelectorAll("[data-3d] .pk-faccia")].filter((f) => f.closest(".pk-variante") && getComputedStyle(f.closest(".pk-variante")).display !== "none")
    .filter((f) => f.scrollHeight > f.clientHeight + 2 || f.scrollWidth > f.clientWidth + 2)
    .map((f) => ({ faccia: f.className, alta: f.scrollHeight, spazio: f.clientHeight, testo: f.innerText.replace(/\s+/g, " ").trim().slice(0, 120) }));
  return { apertura, sezioni, whatsapp, oggetto3d };
}

/* Ogni elemento fisso visibile nella metà bassa dello schermo diventa assoluto, alla stessa distanza dal fondo della pagina
   che aveva dal fondo dello schermo, con la stessa larghezza e la stessa posizione orizzontale. */
function pulsantiFissiInFondo() {
  window.scrollTo(0, 0);
  const H = document.documentElement.scrollHeight, schermo = window.innerHeight, spostati = [];
  for (const el of document.querySelectorAll("body *")) {
    const s = getComputedStyle(el);
    if (s.position !== "fixed" || s.display === "none" || s.visibility === "hidden") continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height || r.top < schermo / 2) continue;
    const dalFondo = schermo - r.bottom, imposta = (k, v) => el.style.setProperty(k, v, "important");
    imposta("position", "absolute"); imposta("transform", "none"); imposta("margin", "0"); imposta("bottom", "auto"); imposta("right", "auto");
    imposta("width", r.width + "px"); imposta("top", "0px"); imposta("left", "0px");
    const base = el.getBoundingClientRect();
    imposta("top", (H - dalFondo - r.height - base.top) + "px"); imposta("left", (r.left - base.left) + "px");
    spostati.push(el.className || el.tagName);
  }
  return spostati;
}

(async () => {
  const processo = spawn(chrome, ["--headless=new", "--disable-gpu", "--hide-scrollbars", /* Chrome leggero come quello del motore (Michele, 9/11/2026) */ "--renderer-process-limit=3", "--js-flags=--max-old-space-size=512", "--disable-extensions", "--mute-audio", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run", "--lang=it-IT", "--accept-lang=it-IT,it",
    "--remote-debugging-port=0", "--user-data-dir=" + profilo, "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
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
  await invia("Page.enable");
  await invia("Emulation.setDeviceMetricsOverride", { width: L, height: A, deviceScaleFactor: 1, mobile });
  await invia("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await invia("Page.navigate", { url: pagina });
  for (let i = 0; i < 100 && !eventi.includes("Page.loadEventFired"); i++) await aspetta(100);
  await aspetta(1000);
  const valuta = async (e) => (await invia("Runtime.evaluate", { expression: e, returnByValue: true })).result.result.value;
  const alta = await valuta("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)");
  for (let y = 0; y < alta; y += A) { await valuta(`window.scrollTo(0, ${y})`); await aspetta(250); }
  await valuta("window.scrollTo(0, 0)");
  await aspetta(ms);
  /* accanto alla fotografia, le misure della pagina vista per il passo 8.3 */
  fs.writeFileSync(arrivo.replace(/\.png$/i, ".json"), JSON.stringify(await valuta(`(${misureDellaPagina})()`)), "utf8");
  /* i pulsanti fissi in basso (per esempio "Chiamateci" sul telefono) vanno in fondo alla pagina, dove li vede chi arriva in
     fondo: senza questo la fotografia lunga li disegnava in fondo al primo schermo, cioè a metà pagina (Michele, 13/11/2026,
     B&B i Krotoniati). Gli elementi fissi in alto restano in cima, come quando la pagina si apre. */
  await valuta(`(${pulsantiFissiInFondo})()`);
  const totale = Math.min(await valuta("document.documentElement.scrollHeight"), 16000);
  const foto = await invia("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: L, height: totale, scale: 1 } });
  fs.writeFileSync(arrivo, Buffer.from(foto.result.data, "base64"));
  /* accanto alla fotografia, il testo che il visitatore vede nella pagina, una riga per frase */
  fs.writeFileSync(arrivo.replace(/\.png$/i, ".txt"), String(await valuta("document.body ? document.body.innerText : ''")), "utf8");
  ws.close(); processo.kill();
})().catch((e) => { console.error(String(e && e.message || e)); process.exit(1); });
