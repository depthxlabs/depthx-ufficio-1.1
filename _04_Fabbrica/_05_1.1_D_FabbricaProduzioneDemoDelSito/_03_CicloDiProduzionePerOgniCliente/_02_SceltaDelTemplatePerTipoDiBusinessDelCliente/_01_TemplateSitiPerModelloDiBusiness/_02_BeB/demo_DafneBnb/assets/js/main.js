/* Template B&B: lingua, menu, apertura, prenotazione su WhatsApp, voto e recensioni da config.js, dati per Google. */
(function () {
  "use strict";
  var C = window.BEB_CONFIG || {};
  var doc = document.documentElement;
  var lingue = (C.lingue && C.lingue.length) ? C.lingue : ["it"];

  /* Lingua: il testo italiano è tra i tag, l'inglese in data-en */
  var nodi = Array.prototype.slice.call(document.querySelectorAll("[data-en]"));
  nodi.forEach(function (n) { n.setAttribute("data-it", n.innerHTML); });
  var attributi = Array.prototype.slice.call(document.querySelectorAll("[data-en-aria]"));
  attributi.forEach(function (n) { n.setAttribute("data-it-aria", n.getAttribute("aria-label") || ""); });
  var alt = Array.prototype.slice.call(document.querySelectorAll("img[data-en-alt]"));
  alt.forEach(function (n) { n.setAttribute("data-it-alt", n.alt); });
  function lingua(l) {
    if (lingue.indexOf(l) < 0) l = "it";
    alt.forEach(function (n) { n.alt = n.getAttribute(l === "en" ? "data-en-alt" : "data-it-alt"); });
    nodi.forEach(function (n) { n.innerHTML = n.getAttribute(l === "en" ? "data-en" : "data-it"); });
    attributi.forEach(function (n) { n.setAttribute("aria-label", n.getAttribute(l === "en" ? "data-en-aria" : "data-it-aria")); });
    doc.lang = l;
    document.querySelectorAll(".lingue button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-lingua") === l)); });
    try { localStorage.setItem("lingua", l); } catch (e) {}
    datiDallaConfig();
  }
  if (lingue.indexOf("en") < 0) document.querySelectorAll(".lingue").forEach(function (n) { n.remove(); });
  document.querySelectorAll(".lingue button").forEach(function (b) {
    b.addEventListener("click", function () { lingua(b.getAttribute("data-lingua")); });
  });

  /* Voto, numero delle recensioni e collegamenti: sempre da config.js, mai scritti fissi */
  function datiDallaConfig() {
    var haVoto = C.voto && C.recensioni;
    document.querySelectorAll("[data-se-voto]").forEach(function (n) { n.hidden = !haVoto; });
    document.querySelectorAll("[data-senza-voto]").forEach(function (n) { n.hidden = !!haVoto; });
    var en = doc.lang === "en";
    document.querySelectorAll("[data-cfg]").forEach(function (n) {
      var k = n.getAttribute("data-cfg"), v = C[k] || "";
      if (k === "voto" && en) v = String(v).replace(",", ".");
      n.textContent = v;
    });
  }
  function collega(sel, url) {
    document.querySelectorAll(sel).forEach(function (a) { if (url) a.href = url; else a.remove(); });
  }
  var tel = (C.telefono || "").replace(/[^+\d]/g, "");
  collega("[data-tel]", tel ? "tel:" + tel : "");
  collega("[data-wa]", C.whatsapp ? "https://wa.me/" + C.whatsapp : "");
  collega("[data-mail]", C.email ? "mailto:" + C.email : "");
  collega("[data-mappa]", C.mappa);
  collega("[data-recensioni]", C.paginaRecensioni);
  collega("[data-facebook]", C.facebook);
  collega("[data-instagram]", C.instagram);
  if (C.prenotazione) document.querySelectorAll("[data-motore]").forEach(function (a) { a.href = C.prenotazione; a.target = "_blank"; a.rel = "noopener"; });

  /* Il modulo non invia dati: apre WhatsApp con il messaggio già scritto */
  document.querySelectorAll("form[data-modulo]").forEach(function (f) {
    var oggi = new Date().toISOString().slice(0, 10);
    f.querySelectorAll("input[type=date]").forEach(function (i) { i.min = oggi; });
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var a = f.elements.arrivo.value, p = f.elements.partenza.value, o = f.elements.ospiti.value;
      var d = function (s) { return s ? s.split("-").reverse().join("/") : "..."; };
      var testo = doc.lang === "en"
        ? "Hello, we would like to stay from " + d(a) + " to " + d(p) + ", " + o + " guests."
        : "Buongiorno, vorremmo soggiornare dal " + d(a) + " al " + d(p) + ", " + o + " ospiti.";
      var url = C.whatsapp ? "https://wa.me/" + C.whatsapp + "?text=" + encodeURIComponent(testo)
        : (C.email ? "mailto:" + C.email + "?body=" + encodeURIComponent(testo) : (tel ? "tel:" + tel : ""));
      if (url) window.open(url, "_blank", "noopener");
    });
  });

  /* Testata e menu */
  var testata = document.querySelector(".testata");
  var menu = document.getElementById("menu");
  var apri = document.querySelector("[data-apri-menu]");
  function chiudiMenu() { menu.classList.remove("aperto"); apri.setAttribute("aria-expanded", "false"); menu.setAttribute("aria-hidden", "true"); apri.focus(); }
  if (menu && apri) {
    apri.addEventListener("click", function () {
      menu.classList.add("aperto"); apri.setAttribute("aria-expanded", "true"); menu.setAttribute("aria-hidden", "false");
      var primo = menu.querySelector("a,button"); if (primo) primo.focus();
    });
    menu.querySelector("[data-chiudi-menu]").addEventListener("click", chiudiMenu);
    menu.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", function () { menu.classList.remove("aperto"); apri.setAttribute("aria-expanded", "false"); menu.setAttribute("aria-hidden", "true"); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && menu.classList.contains("aperto")) chiudiMenu(); });
  }
  window.addEventListener("scroll", function () { if (testata) testata.classList.toggle("scorsa", window.scrollY > 10); }, { passive: true });

  /* Apertura con il logo: si toglie da sola */
  var ap = document.querySelector(".apertura");
  if (ap) setTimeout(function () { ap.remove(); }, 2000);


  /* Comparsa leggera allo scorrimento */
  var sale = document.querySelectorAll(".sale, .voci");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("visto"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    sale.forEach(function (n) { io.observe(n); });
  } else { sale.forEach(function (n) { n.classList.add("visto"); }); }

  /* Dati strutturati per Google, dai valori di config.js */
  var ind = C.indirizzo || {};
  var ld = {
    "@context": "https://schema.org", "@type": C.tipoSchema || "BedAndBreakfast", "name": C.nome,
    "telephone": C.telefono || undefined, "email": C.email || undefined, "url": location.href.split("#")[0],
    "address": { "@type": "PostalAddress", "streetAddress": ind.via, "postalCode": ind.cap, "addressLocality": ind.citta, "addressRegion": ind.provincia, "addressCountry": ind.paese || "IT" },
    "image": (C.fotoDir || "") + (((C.scene || {})[C.scenaDellaHome || "casa"] || {}).poster16 || ""),
    "sameAs": [C.facebook, C.instagram].filter(Boolean)
  };
  if (C.geo && C.geo.lat) ld.geo = { "@type": "GeoCoordinates", "latitude": C.geo.lat, "longitude": C.geo.lng };
  if (C.voto && C.recensioni) ld.aggregateRating = { "@type": "AggregateRating", "ratingValue": String(C.voto).replace(",", "."), "reviewCount": String(C.recensioni).replace(/\D/g, ""), "bestRating": "5" };
  var sc = document.createElement("script"); sc.type = "application/ld+json"; sc.textContent = JSON.stringify(ld); document.head.appendChild(sc);

  var salvata = null; try { salvata = localStorage.getItem("lingua"); } catch (e) {}
  lingua(salvata || "it");
})();

/* DepthX: l'altezza vera della testata, per l'apertura che sta tutta nel primo schermo */
(function () {
  var testata = document.querySelector(".testata");
  function misura() { if (testata) document.documentElement.style.setProperty("--altezza-testata", testata.offsetHeight + "px"); }
  misura();
  window.addEventListener("resize", misura);
})();
