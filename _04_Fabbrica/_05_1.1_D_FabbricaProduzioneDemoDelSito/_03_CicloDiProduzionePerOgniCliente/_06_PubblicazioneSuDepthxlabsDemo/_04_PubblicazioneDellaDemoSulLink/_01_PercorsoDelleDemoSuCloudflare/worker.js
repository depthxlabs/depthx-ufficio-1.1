// Worker del percorso depthxlabs.com/demo e www.depthxlabs.com/demo.
// 1. Le demo dei clienti (con la loro scheda nel KV "demo:<nome>") si servono dal bucket R2 "depthx-demo" (binding DEMO).
// 2. Una demo oltre la data di scadenza della sua scheda mostra la pagina "anteprima non più disponibile".
// 3. Ogni pagina aperta di una demo inviata si registra in R2 (".aperture/<nome>/<data e ora>.json"): quando, pagina, dispositivo,
//    città, regione e paese di Cloudflare, provenienza e canale (?c= del link, o il canale scritto nella scheda all'invio). Senza cookie, senza pixel, senza IP.
//    Si registra se il link ha il canale o se la data di invio della scheda è passata; le anteprime dei link (robot) no.
// 4. Tutto il resto di /demo (le demo dei settori del sito) passa al sito depthxlabs.com così com'è.
//
// R2 (task del 12/11/2026): le risorse statiche del Worker avevano raggiunto il limite di file del piano gratuito. Ora i file
// di ogni demo stanno in R2 con lo stesso percorso ("<nome>/<file>") e l'elenco della demo in ".manifesti/<nome>.json"
// ({"file": {"/index.html": [impronta, tipo], ...}}), scritto dal passo 6 della fabbrica dopo i file. risorsaDellaDemo()
// risponde come il server delle risorse di Cloudflare (html_handling "auto-trailing-slash", not_found_handling "none",
// ETag = impronta del file, 304, HEAD, 405, intestazioni di _headers): le risposte restano identiche a prima.

const ANTEPRIME_DEI_LINK = /(whatsapp|facebookexternalhit|facebot|telegrambot|slackbot|linkedinbot|twitterbot|discordbot|skypeuripreview|googlebot|bingbot|google-pagerenderer|googleimageproxy|applebot|yandex|baiduspider|duckduckbot|petalbot|bytespider|headlesschrome|lighthouse|pingdom|uptimerobot|curl|wget|python-requests)/i;

const MARCHIO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-0.662 -1.04 1.122 1.08" width="96" height="92" aria-hidden="true"><path d="M-0.622 -0L-0.481 -0L-0.185 -0.52L-0.325 -0.52ZM-0.325 -0L-0.185 -0L-0.481 -0.52L-0.622 -0.52Z" fill="#006494" stroke="#000000" stroke-width="0.075" stroke-linejoin="miter" paint-order="stroke"/><path d="M-0.531 -0L-0.334 -0L0.083 -0.73L-0.115 -0.73ZM-0.115 -0L0.083 -0L-0.334 -0.73L-0.531 -0.73Z" fill="#0582ca" stroke="#000000" stroke-width="0.075" stroke-linejoin="miter" paint-order="stroke"/><path d="M-0.42 -0L-0.15 -0L0.42 -1L0.15 -1ZM0.15 -0L0.42 -0L-0.15 -1L-0.42 -1Z" fill="#00a6fb" stroke="#000000" stroke-width="0.075" stroke-linejoin="miter" paint-order="stroke"/></svg>';

const PAGINA_SCADUTA = `<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">
<title>DepthX</title>
<style>
html,body{margin:0;height:100%;background:#051923;color:#f4f7f9;font-family:Montserrat,"Segoe UI",Roboto,Arial,sans-serif}
main{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:32px 20px;box-sizing:border-box;gap:22px}
.nome{font-size:30px;font-weight:600;letter-spacing:.5px}.nome span{color:#00a6fb}
p{font-size:18px;line-height:1.6;max-width:520px;margin:0}
a{color:#00a6fb;font-weight:600}
</style></head>
<body><main>${MARCHIO}<div class="nome">Depth<span>X</span></div>
<p>Questa anteprima non è più disponibile. Se volete rivederla, <a href="https://www.depthxlabs.com/contatti">scriveteci</a></p>
</main></body></html>`;

// Le stesse regole del file _headers della cartella di pubblicazione (se lo cambi, cambia anche questo testo).
const INTESTAZIONI_DELLE_DEMO = `/*
  X-Robots-Tag: noindex, nofollow
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000
  Cache-Control: no-cache
`;

function paginaScaduta() {
  return new Response(PAGINA_SCADUTA, {
    status: 410,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex, nofollow" },
  });
}

// ---- le regole di _headers, come le applica il server delle risorse di Cloudflare ----
function regoleDelleIntestazioni(testo) {
  const regole = [];
  let regola = null;
  for (const riga of testo.split(/\r?\n/)) {
    if (!riga.trim() || riga.trim().startsWith("#")) continue;
    if (!/^\s/.test(riga)) { regola = { percorso: riga.trim(), set: [], unset: [] }; regole.push(regola); continue; }
    if (!regola) continue;
    const voce = riga.trim();
    if (voce.startsWith("!")) { regola.unset.push(voce.slice(1).trim()); continue; }
    const due = voce.indexOf(":");
    if (due > 0) regola.set.push([voce.slice(0, due).trim(), voce.slice(due + 1).trim()]);
  }
  const scappa = (s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");
  return regole.map((r) => {
    let espressione = r.percorso.split("*").map(scappa).join("(?<splat>.*)");
    for (const m of espressione.matchAll(/:([A-Za-z]\w*)/g)) espressione = espressione.split(m[0]).join(`(?<${m[1]}>[^/]+)`);
    return { ...r, altroHost: r.percorso.startsWith("https://"), espressione: new RegExp("^" + espressione + "$") };
  });
}
const REGOLE = regoleDelleIntestazioni(INTESTAZIONI_DELLE_DEMO);

function conLeIntestazioni(link, risposta) {
  const fatte = new Set();
  for (const r of REGOLE) {
    const trovata = r.espressione.exec(r.altroHost ? `https://${link.hostname}${link.pathname}` : link.pathname);
    if (!trovata) continue;
    const sostituisci = (v) => Object.entries(trovata.groups || {}).reduce((t, [k, x]) => t.replaceAll(":" + k, x), v);
    for (const nome of r.unset) risposta.headers.delete(nome);
    for (const [nome, valore] of r.set) {
      if (fatte.has(nome.toLowerCase())) risposta.headers.append(nome, sostituisci(valore));
      else { risposta.headers.set(nome, sostituisci(valore)); fatte.add(nome.toLowerCase()); }
    }
  }
  return risposta;
}

// ---- i percorsi delle pagine, come il server delle risorse di Cloudflare (html_handling "auto-trailing-slash") ----
const decodificaIlPercorso = (p) => p.split("/").map((x) => { try { return decodeURIComponent(x); } catch { return x; } }).join("/").replace(/\/+/g, "/");
const codificaIlPercorso = (p) => p.split("/").map((x) => { try { return encodeURIComponent(x); } catch { return x; } }).join("/");

async function intento(p, esiste, senzaRimandi = false) {
  const rimando = async (file, destinazione) => {
    if (senzaRimandi || esiste(destinazione)) return null;
    const altro = await intento(destinazione, esiste, true);
    return altro?.asset && altro.asset.eTag === esiste(file) ? { asset: null, redirect: destinazione } : null;
  };
  const esatto = esiste(p);
  let r = null, impronta = null;
  if (p.endsWith("/index")) {
    if (esatto) return { asset: { eTag: esatto, status: 200 }, redirect: null };
    if ((r = await rimando(`${p}.html`, p.slice(0, -5)))) return r;
    if ((r = await rimando(`${p.slice(0, -6)}.html`, p.slice(0, -6)))) return r;
  } else if (p.endsWith("/index.html")) {
    if ((r = await rimando(p, p.slice(0, -10)))) return r;
    if ((r = await rimando(`${p.slice(0, -11)}.html`, p.slice(0, -11)))) return r;
  } else if (p.endsWith("/")) {
    if ((impronta = esiste(`${p}index.html`))) return { asset: { eTag: impronta, status: 200 }, redirect: null };
    if ((r = await rimando(`${p.slice(0, -1)}.html`, p.slice(0, -1)))) return r;
  } else if (p.endsWith(".html")) {
    if ((r = await rimando(p, p.slice(0, -5)))) return r;
    if ((r = await rimando(`${p.slice(0, -5)}/index.html`, `${p.slice(0, -5)}/`))) return r;
  }
  if (esatto) return { asset: { eTag: esatto, status: 200 }, redirect: null };
  if ((impronta = esiste(`${p}.html`))) return { asset: { eTag: impronta, status: 200 }, redirect: null };
  if ((r = await rimando(`${p}/index.html`, `${p}/`))) return r;
  return null;
}

// La risposta per un file della demo: la stessa che dava env.ASSETS.fetch() con le risorse statiche del Worker.
async function risorsaDellaDemo(richiesta, link, nome, env) {
  let manifesto = null;
  try { manifesto = await env.DEMO.get(".manifesti/" + nome + ".json").then((o) => (o ? o.json() : null)); } catch (e) { manifesto = null; }
  const file = (manifesto && manifesto.file) || {};
  const prefisso = "/" + nome + "/";
  const voce = (p) => (p.startsWith(prefisso) && Object.prototype.hasOwnProperty.call(file, p.slice(prefisso.length - 1)) ? file[p.slice(prefisso.length - 1)] : null);
  const esiste = (p) => (voce(p) ? voce(p)[0] : null);
  const percorsoDelFile = {};

  const decodificato = decodificaIlPercorso(link.pathname);
  const trovato = await intento(decodificato, (p) => { const v = voce(p); if (v) percorsoDelFile[v[0]] = percorsoDelFile[v[0]] || p; return v ? v[0] : null; });
  if (!trovato) return conLeIntestazioni(link, new Response(null, { status: 404, statusText: "Not Found" }));
  const metodo = richiesta.method.toUpperCase();
  if (!["GET", "HEAD"].includes(metodo)) return conLeIntestazioni(link, new Response(null, { status: 405, statusText: "Method Not Allowed" }));
  const destinazione = codificaIlPercorso(trovato.redirect !== null ? trovato.redirect : decodificato);
  if ((destinazione !== link.pathname && trovato.asset) || trovato.redirect !== null) {
    return conLeIntestazioni(link, new Response(null, { status: 307, statusText: "Temporary Redirect", headers: { Location: destinazione + link.search } }));
  }

  const impronta = trovato.asset.eTag;
  // il file che ha questa impronta: quello esatto, o la pagina .html / index.html trovata dalle regole qui sopra
  const percorso = [decodificato, `${decodificato}.html`, `${decodificato}index.html`].find((p) => esiste(p) === impronta) || percorsoDelFile[impronta];
  const intestazioni = new Headers({ ETag: `"${impronta}"` });
  const tipo = voce(percorso)[1];
  if (tipo) intestazioni.append("Content-Type", tipo);
  if (!richiesta.headers.has("Authorization") && !richiesta.headers.has("Range")) intestazioni.append("Cache-Control", "public, max-age=0, must-revalidate");
  const condizione = richiesta.headers.get("If-None-Match") || "";
  if ([`W/"${impronta}"`, `"${impronta}"`].includes(condizione)) {
    return conLeIntestazioni(link, new Response(null, { status: 304, statusText: "Not Modified", headers: intestazioni }));
  }
  if (metodo === "HEAD") return conLeIntestazioni(link, new Response(null, { status: 200, headers: intestazioni }));
  const oggetto = await env.DEMO.get(percorso.slice(1));
  if (!oggetto) return conLeIntestazioni(link, new Response(null, { status: 404, statusText: "Not Found" }));
  return conLeIntestazioni(link, new Response(oggetto.body, { status: 200, headers: intestazioni }));
}

export default {
  async fetch(richiesta, env, ctx) {
    const link = new URL(richiesta.url);
    if (link.pathname === "/demo") return Response.redirect(link.origin + "/demo/" + link.search, 301);
    const parti = link.pathname.split("/").filter(Boolean);
    const nome = (parti[1] || "").toLowerCase();
    if (!nome || !/^[a-z0-9]+$/.test(nome)) return fetch(richiesta);

    // la scheda della demo sta su R2 (.registro/demo:<nome>.json); il vecchio registro KV resta solo come riserva
    let scheda = null;
    try { const oggetto = await env.DEMO.get(".registro/demo:" + nome + ".json"); if (oggetto) scheda = ((await oggetto.json()) || {}).valore || null; } catch (e) { scheda = null; }
    if (!scheda) { try { scheda = await env.TRACCIAMENTO.get("demo:" + nome, { type: "json", cacheTtl: 60 }); } catch (e) { scheda = null; } }
    if (!scheda) return fetch(richiesta);

    const ora = new Date();
    if (scheda.scadenza && ora >= new Date(scheda.scadenza)) return paginaScaduta();
    if (parti.length === 2 && !link.pathname.endsWith("/")) return Response.redirect(link.origin + "/demo/" + nome + "/" + link.search, 301);

    const percorso = link.pathname.replace(/^\/demo/, "");
    let risposta = await risorsaDellaDemo(richiesta, new URL(percorso + link.search, link.origin), nome, env);
    const rimando = risposta.headers.get("location");
    if (rimando && rimando.startsWith("/") && !rimando.startsWith("/demo/")) {  // i rimandi restano dentro /demo/<nome>/
      const intestazioni = new Headers(risposta.headers);
      intestazioni.set("location", "/demo" + rimando);
      risposta = new Response(risposta.body, { status: risposta.status, headers: intestazioni });
    }

    const pagina = (richiesta.headers.get("sec-fetch-dest") === "document") ||
      ((richiesta.headers.get("accept") || "").includes("text/html") && (risposta.headers.get("content-type") || "").includes("text/html"));
    const dispositivo = richiesta.headers.get("user-agent") || "";
    const canale = (link.searchParams.get("c") || (scheda.invio && scheda.canale) || "").toLowerCase().replace(/[^a-z]/g, "").slice(0, 20);
    const inviata = canale || (scheda.invio && ora >= new Date(scheda.invio));
    if (richiesta.method === "GET" && pagina && risposta.status === 200 && inviata && !ANTEPRIME_DEI_LINK.test(dispositivo)) {
      const cf = richiesta.cf || {};
      let provenienza = "";
      try { provenienza = new URL(richiesta.headers.get("referer") || "").hostname; } catch (e) { provenienza = ""; }
      const apertura = { quando: ora.toISOString(), pagina: percorso, canale, dispositivo: /mobi|android|iphone|ipad/i.test(dispositivo) ? "telefono" : "computer",
                         citta: cf.city || "", regione: cf.region || "", paese: cf.country || "", provenienza,
                         browser: (dispositivo.match(/(Edg|OPR|Chrome|Firefox|Safari)\/[\d.]+/) || [""])[0].split("/")[0] };
      const chiave = ".aperture/" + nome + "/" + apertura.quando.replace(/[:.]/g, "-") + "-" + Math.random().toString(36).slice(2, 8) + ".json";
      ctx.waitUntil(env.DEMO.put(chiave, JSON.stringify(apertura), { httpMetadata: { contentType: "application/json" } }).catch(() => {}));
    }
    return risposta;
  },
};
