/* Template Advanced DepthX, comune ai 4 tipi di struttura: tutto viene da window.SITO_CONFIG; nessun testo del cliente è scritto qui. */
(function () {
  "use strict";
  var C = window.SITO_CONFIG || {};
  var K = C.contatti || {};
  var R = C.recensioni || {};
  var doc = document, root = doc.documentElement;
  var $$ = function (s, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(s)); };
  var via = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var calmo = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Link dei contatti: un link senza il dato del cliente esce, con la sua voce di elenco */
  var cifre = function (s) { return String(s || "").replace(/[^\d+]/g, ""); };
  var mappa = K.latitudine && K.longitudine
    ? "https://www.google.com/maps/dir/?api=1&destination=" + K.latitudine + "," + K.longitudine
    : (K.mappa || "");
  var link = {
    tel: K.telefono ? "tel:" + cifre(K.telefono) : "",
    email: K.email ? "mailto:" + K.email : "",
    whatsapp: K.whatsapp ? "https://wa.me/" + cifre(K.whatsapp).replace("+", "") : "",
    mappa: mappa,
    instagram: K.instagram || "",
    facebook: K.facebook || "",
    recensioni: R.link || ""
  };
  $$("[data-link]").forEach(function (a) {
    var h = link[a.getAttribute("data-link")];
    if (h) { a.setAttribute("href", h); return; }
    var li = a.closest("li");
    via(li && li.children.length === 1 ? li : a);
  });
  if (link.whatsapp) $$("[data-se-manca=whatsapp]").forEach(via);
  else $$("[data-solo=whatsapp]").forEach(via);

  /* La mappa di OpenStreetMap (Michele, 11/11/2026): l'anteprima con le tessere vere centrate sulla struttura, la mappa
     interattiva solo quando il visitatore la apre */
  var lat = parseFloat(K.latitudine), lon = parseFloat(K.longitudine);
  $$("[data-mappa]").forEach(function (m) {
    var osm = m.querySelector("[data-osm]");
    if (!isFinite(lat) || !isFinite(lon) || !osm) { var b = m.querySelector("[data-apri-mappa]"); if (b) via(b); return; }
    var z = 16, n = Math.pow(2, z), r = lat * Math.PI / 180;
    var x = (lon + 180) / 360 * n, y = (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * n;
    function tessere() {
      var W = osm.clientWidth || 1200, H = osm.clientHeight || 500;
      osm.textContent = "";
      for (var tx = Math.floor(x - W / 512) - 1; tx <= Math.floor(x + W / 512) + 1; tx++)
        for (var ty = Math.floor(y - H / 512) - 1; ty <= Math.floor(y + H / 512) + 1; ty++) {
          var img = new Image(); img.alt = ""; img.decoding = "async"; img.loading = "lazy";
          img.src = "https://tile.openstreetmap.org/" + z + "/" + tx + "/" + ty + ".png";
          img.style.left = Math.round(W / 2 + (tx - x) * 256) + "px"; img.style.top = Math.round(H / 2 + (ty - y) * 256) + "px";
          osm.appendChild(img);
        }
    }
    tessere();
    var apri = m.querySelector("[data-apri-mappa]");
    if (apri) apri.addEventListener("click", function () {
      var f = doc.createElement("iframe"); f.title = "OpenStreetMap"; f.loading = "lazy";
      f.src = "https://www.openstreetmap.org/export/embed.html?bbox=" + (lon - 0.012) + "%2C" + (lat - 0.007) + "%2C" + (lon + 0.012) + "%2C" + (lat + 0.007) +
              "&layer=mapnik&marker=" + lat + "%2C" + lon;
      m.appendChild(f); m.classList.add("is-attiva");
    });
  });

  /* Marchio: il logo del cliente se c'è, altrimenti il nome nel carattere del template */
  if (C.logo) $$("[data-marchio]").forEach(function (el) {
    var img = new Image(); img.src = C.logo; img.alt = C.nome || ""; img.decoding = "async";
    el.textContent = ""; el.appendChild(img); el.classList.add("con-logo");
  });

  /* Servizi: restano solo le voci vere (la fabbrica le scrive in servizi); senza voci e senza foto la sezione esce */
  var servizi = Array.isArray(C.servizi) ? C.servizi : [];
  if (servizi.length) $$("[data-servizio]").forEach(function (li) { if (servizi.indexOf(li.getAttribute("data-servizio")) < 0) via(li); });
  $$("[data-servizi]").forEach(function (sez) {
    if (!sez.querySelector("[data-servizio]") && !sez.querySelector("picture img[src]")) via(sez);
  });

  /* Recensioni: una sezione senza recensioni esce */
  $$("[data-sezione-recensioni]").forEach(function (sez) { if (!sez.querySelector("[data-recensione]")) via(sez); });

  /* Lingua: italiano e inglese */
  var testiIt = new Map();
  function metti(l) {
    root.lang = l;
    $$("[data-en]").forEach(function (el) {
      if (!testiIt.has(el)) testiIt.set(el, el.textContent);
      el.textContent = l === "en" ? el.getAttribute("data-en") : testiIt.get(el);
    });
    ["aria-label", "alt", "content", "title"].forEach(function (a) {
      $$("[data-en-" + a + "]").forEach(function (el) {
        var k = "data-it-" + a;
        if (!el.hasAttribute(k)) el.setAttribute(k, el.getAttribute(a) || "");
        el.setAttribute(a, l === "en" ? el.getAttribute("data-en-" + a) : el.getAttribute(k));
      });
    });
    $$("[data-lingua]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-lingua") === l)); });
    try { localStorage.setItem("lingua", l); } catch (e) {}
    collegaITelefoni();
  }

  /* Michele, 11/11/2026: il telefono è sempre collegato all'azione. Ogni numero del cliente scritto in una frase diventa un
     collegamento che chiama (le cifre si riconoscono anche con spazi, punti o trattini diversi da quelli del config) */
  function collegaITelefoni() {
    var numero = cifre(K.telefono).replace(/^\+?39/, "");
    if (!link.tel || numero.length < 6) return;
    var modello = new RegExp("(?:\\+?\\s?39[\\s.\\-]*)?" + numero.split("").join("[\\s.\\-/]*"));
    var testi = [], giro = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    while (giro.nextNode()) {
      var n = giro.currentNode;
      if (modello.test(n.nodeValue) && !n.parentNode.closest("a, button, script, style, title, dialog form")) testi.push(n);
    }
    testi.forEach(function (n) {
      var trovato = n.nodeValue.match(modello), a = doc.createElement("a");
      a.href = link.tel; a.className = "telefono-collegato"; a.textContent = trovato[0];
      var dopo = n.splitText(trovato.index); dopo.nodeValue = dopo.nodeValue.slice(trovato[0].length);
      n.parentNode.insertBefore(a, dopo);
    });
  }
  var lingue = C.lingue || ["it", "en"];
  if (lingue.indexOf("en") < 0) $$(".lingue").forEach(via);
  $$("[data-lingua]").forEach(function (b) { b.addEventListener("click", function () { metti(b.getAttribute("data-lingua")); }); });
  var chiesta = (location.search.match(/[?&]lang=(it|en)/) || [])[1];
  var salvata = null; try { salvata = localStorage.getItem("lingua"); } catch (e) {}
  var iniziale = chiesta || salvata || C.linguaPredefinita || "it";
  metti(lingue.indexOf(iniziale) >= 0 ? iniziale : "it");

  /* Preparazione per Google: i dati strutturati della struttura, dai dati del config */
  var ld = {
    "@context": "https://schema.org", "@type": C.tipoSchema || "LodgingBusiness", name: C.nome,
    telephone: K.telefono || undefined, email: K.email || undefined,
    address: { "@type": "PostalAddress", streetAddress: K.via, postalCode: K.cap, addressLocality: K.comune, addressRegion: K.provincia, addressCountry: K.paese || "IT" },
    geo: K.latitudine ? { "@type": "GeoCoordinates", latitude: K.latitudine, longitude: K.longitudine } : undefined,
    hasMap: link.mappa || undefined,
    sameAs: [K.instagram, K.facebook].filter(Boolean)
  };
  var s = doc.createElement("script"); s.type = "application/ld+json"; s.textContent = JSON.stringify(ld); doc.head.appendChild(s);

  /* Testata che si riempie allo scorrimento (le pagine senza foto d'apertura la hanno piena da subito) */
  var testata = doc.getElementById("testata");
  var eroe = doc.querySelector(".eroe");
  /* Michele, 11/11/2026: appena si scorre la testata è bianca, mai trasparente sopra le scritte */
  function suScorri() { if (testata) testata.classList.toggle("is-piena", !eroe || window.scrollY > 10); }
  addEventListener("scroll", suScorri, { passive: true }); suScorri();

  /* Menu */
  var menu = doc.getElementById("menu");
  var apriMenu = doc.querySelector(".testata__menu");
  function menuStato(aperto) {
    if (!menu || !apriMenu) return;
    menu.hidden = !aperto; apriMenu.setAttribute("aria-expanded", String(aperto));
    doc.body.classList.toggle("menu-aperto", aperto);
  }
  if (apriMenu) apriMenu.addEventListener("click", function () { menuStato(menu.hidden); });
  $$("a", menu || doc.createElement("nav")).forEach(function (a) { a.addEventListener("click", function () { menuStato(false); }); });
  addEventListener("keydown", function (e) { if (e.key === "Escape" && menu && !menu.hidden) { menuStato(false); apriMenu.focus(); } });

  /* Prenota: ogni pulsante Prenota apre la finestra delle date; l'invio scrive il messaggio e apre WhatsApp, altrimenti la email */
  var finestra = doc.getElementById("finestra-prenota");
  $$("[data-apri-prenota]").forEach(function (b) {
    b.addEventListener("click", function (e) {
      e.preventDefault(); menuStato(false);
      if (finestra && finestra.showModal) finestra.showModal();
    });
  });
  $$("[data-chiudi]").forEach(function (b) { b.addEventListener("click", function () { finestra.close(); }); });
  if (finestra) finestra.addEventListener("click", function (e) { if (e.target === finestra) finestra.close(); });
  var oggi = new Date().toISOString().slice(0, 10);
  $$("input[type=date]").forEach(function (i) { i.min = oggi; });
  function data(v) { if (!v) return ""; var p = v.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; }
  $$("[data-prenota]").forEach(function (f) {
    var a = f.querySelector("[name=arrivo]"), p = f.querySelector("[name=partenza]");
    if (a && p) a.addEventListener("change", function () { p.min = a.value; if (p.value && p.value <= a.value) p.value = ""; });
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var o = f.querySelector("[name=ospiti]").value;
      var etichette = $$("label", f).map(function (l) { return l.textContent; });
      var righe = [C.nome, etichette[0] + ": " + data(a.value), etichette[1] + ": " + data(p.value), etichette[2] + ": " + o].join("\n");
      var oggetto = f.querySelector("button[type=submit]").textContent + " · " + (C.nome || "");
      if (link.whatsapp) window.open(link.whatsapp + "?text=" + encodeURIComponent(righe), "_blank", "noopener");
      else if (link.email) location.href = link.email + "?subject=" + encodeURIComponent(oggetto) + "&body=" + encodeURIComponent(righe);
      else if (link.tel) location.href = "sms:" + link.tel.replace(/^tel:/, "") + "?&body=" + encodeURIComponent(righe);
    });
  });

  /* Animazione 1 di 3: la comparsa morbida dei blocchi */
  var riv = $$("[data-rivela]");
  if (!("IntersectionObserver" in window) || calmo) riv.forEach(function (el) { el.classList.add("is-visibile"); });
  else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("is-visibile"); io.unobserve(x.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .08 });
    riv.forEach(function (el) { io.observe(el); });
  }
})();

/* DepthX, regole di Michele (9/11/2026): mai mezza pagina vuota; nel menu solo le voci delle sezioni presenti.
   Gira dopo le foto: un blocco a due colonne senza foto diventa una colonna sola centrata (classe senza-foto),
   una galleria con foto mancanti si ricompone (galleria-ridotta). */
(function (C, P) {
  var d = document;
  var tutti = function (s) { return s ? [].slice.call(d.querySelectorAll(s)) : []; };
  var togli = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var foto = function (el) { return !!(el && el.querySelector("picture img[src]")); };
  var vuoto = function (el) { return !foto(el) && !el.textContent.trim() && !el.querySelector("input, select, button, a[href], iframe"); };
  tutti(P.vuoti).forEach(function (el) { if (vuoto(el)) togli(el); });
  (P.coppie || []).forEach(function (c) {
    tutti(c[0]).forEach(function (b) {
      var col = [].filter.call(b.children, function (x) { return x.matches(c[1]); });
      col.forEach(function (x) { if (vuoto(x)) togli(x); });
      b.classList.toggle("senza-foto", !col.some(foto));
      var testo = [].filter.call(b.children, function (x) { return !x.matches(c[1]); });
      b.classList.toggle("senza-testo", !testo.some(function (x) { return x.textContent.trim(); }));
    });
  });
  (P.gallerie || []).forEach(function (g) {
    tutti(g[0]).forEach(function (el) {
      [].slice.call(el.children).forEach(function (x) { if (vuoto(x)) togli(x); });
      var n = el.children.length;
      if (!n) { togli(g[2] ? (el.closest("section") || el) : el); return; }
      el.setAttribute("data-quante", String(n));
      el.classList.toggle("galleria-ridotta", n < g[1]);
    });
  });
  tutti(P.menu).forEach(function (m) {
    [].slice.call(m.querySelectorAll('a[href^="#"]')).forEach(function (a) {
      var id = a.getAttribute("href").slice(1);
      if (id && !d.getElementById(id)) togli(a.closest("li") || a);
    });
  });
})(window.SITO_CONFIG || {}, { vuoti: ".mosaico > *, .schede > *, .camere__elenco dl > div, .camere__elenco", coppie: [[".coppia", ".coppia__foto"]], gallerie: [[".galleria", 3, true], [".anteprima__foto", 3], [".mosaico", 2], [".schede", 1], [".camere__griglia", 2]], menu: "#menu, .testata__voci" });
