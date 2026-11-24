/* Template Hotel (DepthX): tutto viene da window.HOTEL_CONFIG; nessun testo del cliente è scritto qui. */
(function () {
  "use strict";
  var C = window.HOTEL_CONFIG || {};
  var K = C.contatti || {};
  var R = C.recensioni || {};
  var doc = document, root = doc.documentElement;
  var $$ = function (s, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(s)); };
  var via = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var leggi = function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } };
  var scrivi = function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} };
  var lingua = "it";

  /* Link dei contatti */
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

  /* Marchio: il logo del cliente se c'è, altrimenti il nome nel carattere del template */
  if (C.logo) $$("[data-marchio]").forEach(function (el) {
    var img = new Image(); img.src = C.logo; img.alt = C.nome || ""; img.decoding = "async";
    el.textContent = ""; el.appendChild(img);
  });

  /* Scene senza foto: il blocco si toglie */
  var scene = C.scene || {};
  $$("picture[data-scena]").forEach(function (p) {
    var s = scene[p.getAttribute("data-scena")];
    if (s && s.poster16) return;
    var blocco = p.closest(".camera, .recensione, [data-rivela]") || p;
    via(blocco);
  });

  /* Recensioni: titolo con voto e numero solo se esistono nei dati */
  var tRec = doc.getElementById("titolo-rec");
  if (tRec && R.voto && R.numero) {
    tRec.setAttribute("data-rec-dati", "1");
  }
  if (!$$("[data-recensione]").length) via(doc.getElementById("recensioni"));

  /* Lingua */
  var testiIt = new Map();
  function metti(l) {
    lingua = l;
    root.lang = l;
    $$("[data-en]").forEach(function (el) {
      if (!testiIt.has(el)) testiIt.set(el, el.textContent);
      el.textContent = l === "en" ? el.getAttribute("data-en") : testiIt.get(el);
    });
    ["aria-label", "alt", "content"].forEach(function (a) {
      $$("[data-en-" + a + "]").forEach(function (el) {
        var k = "data-it-" + a;
        if (!el.hasAttribute(k)) el.setAttribute(k, el.getAttribute(a) || "");
        el.setAttribute(a, l === "en" ? el.getAttribute("data-en-" + a) : el.getAttribute(k));
      });
    });
    if (tRec && tRec.hasAttribute("data-rec-dati")) {
      var voto = l === "en" ? String(R.voto).replace(",", ".") : String(R.voto).replace(".", ",");
      tRec.textContent = tRec.getAttribute("data-modello-" + l).replace("{voto}", voto).replace("{numeroRecensioni}", R.numero);
    }
    $$("[data-lingua]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-lingua") === l)); });
    try { localStorage.setItem("lingua", l); } catch (e) {}
  }
  var lingue = C.lingue || ["it"];
  if (lingue.indexOf("en") < 0) $$(".lingue").forEach(via);
  $$("[data-lingua]").forEach(function (b) { b.addEventListener("click", function () { metti(b.getAttribute("data-lingua")); }); });
  var chiesta = (location.search.match(/[?&]lang=(it|en)/) || [])[1];
  var salvata = null; try { salvata = localStorage.getItem("lingua"); } catch (e) {}
  var iniziale = chiesta || salvata || C.linguaPredefinita || "it";
  metti(lingue.indexOf(iniziale) >= 0 ? iniziale : "it");

  /* Dati strutturati per Google, dai dati del config */
  var ld = {
    "@context": "https://schema.org", "@type": C.tipoSchema || "Hotel", name: C.nome,
    telephone: K.telefono || undefined, email: K.email || undefined,
    address: { "@type": "PostalAddress", streetAddress: K.via, postalCode: K.cap, addressLocality: K.comune, addressRegion: K.provincia, addressCountry: K.paese || "IT" },
    geo: K.latitudine ? { "@type": "GeoCoordinates", latitude: K.latitudine, longitude: K.longitudine } : undefined,
    numberOfRooms: C.camere || undefined,
    sameAs: [K.instagram, K.facebook].filter(Boolean),
    aggregateRating: R.voto && R.numero ? { "@type": "AggregateRating", ratingValue: String(R.voto).replace(",", "."), reviewCount: R.numero, bestRating: "5" } : undefined
  };
  var s = doc.createElement("script"); s.type = "application/ld+json"; s.textContent = JSON.stringify(ld); doc.head.appendChild(s);

  /* Apertura con il marchio, una volta per visita */
  var apertura = doc.querySelector(".apertura");
  var calmo = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (apertura) {
    if (calmo || leggi("aperturaVista") || /[?&]senzaApertura/.test(location.search)) { via(apertura); }
    else {
      scrivi("aperturaVista", "1");
      requestAnimationFrame(function () { apertura.classList.add("is-in"); });
      setTimeout(function () { apertura.classList.add("is-via"); }, 1500);
      setTimeout(function () { via(apertura); }, 2800);
    }
  }

  /* Testata che si riempie allo scorrimento */
  var testata = doc.getElementById("testata");
  var hero = doc.querySelector(".hero");
  function suScorri() { testata.classList.toggle("is-piena", window.scrollY > (hero ? hero.offsetHeight - 80 : 10)); }
  addEventListener("scroll", suScorri, { passive: true }); suScorri();

  /* Menu */
  var menu = doc.getElementById("menu");
  var apriMenu = doc.querySelector(".testata__menu");
  function menuStato(aperto) {
    menu.hidden = !aperto; apriMenu.setAttribute("aria-expanded", String(aperto));
    doc.body.classList.toggle("menu-aperto", aperto);
  }
  apriMenu.addEventListener("click", function () { menuStato(menu.hidden); });
  $$("a", menu).forEach(function (a) { a.addEventListener("click", function () { menuStato(false); }); });
  addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { menuStato(false); apriMenu.focus(); } });

  /* Prenotazione: il modulo scrive il messaggio e apre WhatsApp, altrimenti la email */
  var finestra = doc.getElementById("finestra-prenota");
  $$("[data-apri-prenota]").forEach(function (b) {
    b.addEventListener("click", function () {
      menuStato(false);
      if (finestra && finestra.showModal) finestra.showModal(); else location.hash = "#contenuto";
    });
  });
  $$("[data-chiudi]").forEach(function (b) { b.addEventListener("click", function () { finestra.close(); }); });
  if (finestra) finestra.addEventListener("click", function (e) { if (e.target === finestra) finestra.close(); });
  var oggi = new Date().toISOString().slice(0, 10);
  $$("input[type=date]").forEach(function (i) { i.min = oggi; });
  function data(v) { if (!v) return ""; var p = v.split("-"); return p[2] + "/" + p[1] + "/" + p[0]; }
  $$("[data-prenota]").forEach(function (f) {
    var a = f.querySelector("[name=arrivo]"), p = f.querySelector("[name=partenza]");
    a.addEventListener("change", function () { p.min = a.value; if (p.value && p.value <= a.value) p.value = ""; });
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var o = f.querySelector("[name=ospiti]").value;
      var etichette = $$("label", f).map(function (l) { return l.textContent; });
      var righe = [C.nome, etichette[0] + ": " + data(a.value), etichette[1] + ": " + data(p.value), etichette[2] + ": " + o].join("\n");
      var oggetto = f.querySelector("button[type=submit]").textContent + " · " + (C.nome || "");
      if (link.whatsapp) window.open(link.whatsapp + "?text=" + encodeURIComponent(righe), "_blank", "noopener");
      else if (link.email) location.href = link.email + "?subject=" + encodeURIComponent(oggetto) + "&body=" + encodeURIComponent(righe);
      else if (link.tel) location.href = link.tel;
    });
  });


  /* Comparsa leggera */
  var riv = $$("[data-rivela]");
  if (!("IntersectionObserver" in window) || calmo) riv.forEach(function (el) { el.classList.add("is-visibile"); });
  else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("is-visibile"); io.unobserve(x.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .08 });
    riv.forEach(function (el) { io.observe(el); });
  }
})();
