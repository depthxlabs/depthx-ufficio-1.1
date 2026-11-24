/* Casa Vacanza: riempie la pagina dai valori di config.js. Nessuna frase visibile vive qui: i testi sono nella pagina. */
(function () {
  "use strict";
  var C = window.CASA_CONFIG || {}, d = document, R = d.documentElement;
  var $ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };
  var togli = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var ridotto = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  R.classList.add("js");

  /* Nome, logo e icona */
  var nome = C.nomeBreve || C.nome;
  if (nome) {
    $("[data-nome-breve]").forEach(function (el) { el.textContent = nome; });
    $("[data-nome-aria]").forEach(function (el) { el.setAttribute("aria-label", nome); });
  }
  if (C.logo) {
    $(".testata__logo .logotipo, .apertura .logotipo").forEach(function (el) {
      el.textContent = ""; var i = new Image(); i.src = C.logo; i.alt = nome || ""; el.appendChild(i);
    });
  }
  if (C.icona) { var ic = d.querySelector('link[rel="icon"]'); if (ic) ic.href = C.icona; }

  /* Apertura: una volta per visita */
  var ap = d.getElementById("apertura");
  if (ap) {
    if (R.classList.contains("senza-apertura") || ridotto) togli(ap);
    else setTimeout(function () { togli(ap); }, 2400);
    try { sessionStorage.setItem("aperturaVista", "1"); } catch (e) {}
  }

  /* Campi assenti: l'elemento esce dalla pagina */
  $("[data-se]").forEach(function (el) { if (!C[el.getAttribute("data-se")]) togli(el); });

  /* Foto: 16:9 sul computer, 9:16 sul telefono dove serve; WebP con JPEG di riserva, tre larghezze */
  var dir = C.fotoDir || "media/foto/";
  var serie = function (file, larg, est) {
    var b = dir + file.replace(/\.(jpe?g|webp)$/i, "");
    return larg.map(function (w) { return b + "-" + w + "." + est + " " + w + "w"; }).join(", ");
  };
  var sorgente = function (pic, img, srcset, tipo, media, sizes) {
    var s = d.createElement("source"); s.srcset = srcset; s.sizes = sizes;
    if (tipo) s.type = tipo; if (media) s.media = media; pic.insertBefore(s, img);
  };
  $("picture[data-scena]").forEach(function (pic) {
    var s = (C.scene || {})[pic.getAttribute("data-scena")] || {}, img = pic.querySelector("img");
    var forma = pic.getAttribute("data-forma") || "16x9";
    var file = forma === "9x16" ? s.poster9 : s.poster16;
    if (!file || !img) { togli(pic.closest("[data-blocco]") || pic.closest("figure") || pic); return; }
    var larg = forma === "9x16" ? (C.larghezze9 || [480, 720, 1080]) : (C.larghezze16 || [640, 1280, 1920]);
    var sizes = pic.getAttribute("data-sizes") || "100vw";
    if (pic.getAttribute("data-telefono") === "9x16" && s.poster9 && forma !== "9x16") {
      var l9 = C.larghezze9 || [480, 720, 1080], m = "(max-width: 700px)";
      sorgente(pic, img, serie(s.poster9, l9, "webp"), "image/webp", m, sizes);
      sorgente(pic, img, serie(s.poster9, l9, "jpg"), "", m, sizes);
    }
    sorgente(pic, img, serie(file, larg, "webp"), "image/webp", "", sizes);
    img.sizes = sizes; img.srcset = serie(file, larg, "jpg");
    img.src = dir + file.replace(/\.(jpe?g|webp)$/i, "") + "-" + larg[1] + ".jpg";
    if (forma === "9x16") { img.width = 1080; img.height = 1920; }
  });
  $(".evidenza").forEach(function (ev) { if (!ev.querySelector("picture")) { togli(ev.querySelector(".evidenza__foto")); ev.classList.add("solo-testo"); } });
  $(".mosaico").forEach(function (m) { if (!m.querySelector("picture")) togli(m.closest("section")); });


  /* Servizi: solo quelli veri */
  if (Array.isArray(C.servizi) && C.servizi.length) {
    $("[data-servizio]").forEach(function (li) { if (C.servizi.indexOf(li.getAttribute("data-servizio")) < 0) togli(li); });
  }

  /* Voto e numero delle recensioni, dai dati Google */
  var voto = String(C.votoGoogle || "");
  $("[data-voto]").forEach(function (el) { el.textContent = el.closest('[data-lingua="en"]') ? voto.replace(",", ".") : voto; });
  var n = parseInt(String(C.numeroRecensioni || "").replace(/\D/g, ""), 10) || 0, arr = Math.floor(n / 10) * 10;
  $("[data-recensioni-arrotondate]").forEach(function (el) { el.textContent = String(arr); });
  var tNum = d.querySelector('[data-titolo-recensioni="numero"]'), tSem = d.querySelector('[data-titolo-recensioni="semplice"]');
  if (!voto || arr < 10) { togli(tNum); if (tSem) tSem.hidden = false; } else togli(tSem);

  /* Contatti e collegamenti */
  var cifre = function (t) { return String(t || "").replace(/[^\d+]/g, ""); };
  var wa = cifre(C.whatsapp).replace(/^\+/, "");
  $("[data-tel]").forEach(function (a) { a.href = "tel:" + cifre(C.telefono); if (!a.textContent.trim() && !a.classList.contains("tondo")) a.textContent = C.telefono; });
  $("[data-whatsapp]").forEach(function (a) { a.href = "https://wa.me/" + wa; });
  $("[data-mappa]").forEach(function (a) { a.href = C.mappa; });
  $("[data-recensioni-google]").forEach(function (a) { if (C.recensioniGoogle) a.href = C.recensioniGoogle; else togli(a.closest("p")); });
  if (C.indirizzo) $("[data-indirizzo]").forEach(function (el) { el.textContent = C.indirizzo + ", " + [C.cap, C.citta].filter(Boolean).join(" "); });

  /* Lingua */
  var lingue = C.lingue || ["it"], lingua = "it";
  try { lingua = localStorage.getItem("lingua") || "it"; } catch (e) {}
  if (lingue.indexOf("en") < 0) { lingua = "it"; $("[data-cambia-lingua]").forEach(togli); }
  var attr = [["data-en-alt", "alt"], ["data-en-aria-label", "aria-label"], ["data-en-content", "content"]];
  var applica = function (l) {
    lingua = l; R.lang = l;
    $("[data-en]").forEach(function (el) {
      if (el.dataset.it === undefined) el.dataset.it = el.textContent;
      el.textContent = l === "en" ? el.getAttribute("data-en") : el.dataset.it;
    });
    attr.forEach(function (a) {
      $("[" + a[0] + "]").forEach(function (el) {
        var k = "it" + a[1].replace(/-/g, "");
        if (el.dataset[k] === undefined) el.dataset[k] = el.getAttribute(a[1]) || "";
        el.setAttribute(a[1], l === "en" ? el.getAttribute(a[0]) : el.dataset[k]);
      });
    });
    $("[data-lingua]").forEach(function (el) { el.hidden = el.getAttribute("data-lingua") !== l; });
    $("[data-scegli-lingua]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-scegli-lingua") === l ? "true" : "false"); });
  };
  $("[data-scegli-lingua]").forEach(function (b) {
    b.addEventListener("click", function () { var l = b.getAttribute("data-scegli-lingua"); try { localStorage.setItem("lingua", l); } catch (e) {} applica(l); });
  });
  if (lingua === "en") applica("en");

  /* Modulo: il messaggio si apre su WhatsApp, già scritto */
  var barra = d.getElementById("barra");
  if (barra) barra.addEventListener("submit", function (e) {
    e.preventDefault();
    var f = barra.elements, data = function (v) { var p = String(v || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : v; };
    var t = (barra.getAttribute("data-messaggio-" + lingua) || barra.getAttribute("data-messaggio-it") || "")
      .replace("{arrivo}", data(f.arrivo.value)).replace("{partenza}", data(f.partenza.value)).replace("{ospiti}", f.ospiti.value || "");
    window.open("https://wa.me/" + wa + "?text=" + encodeURIComponent(t), "_blank", "noopener");
  });

  /* Testata e menu */
  var testata = d.getElementById("testata"), eroe = d.querySelector(".eroe");
  var scorri = function () { testata.classList.toggle("solida", window.scrollY > (eroe ? eroe.offsetHeight - 90 : 40)); };
  window.addEventListener("scroll", scorri, { passive: true }); scorri();
  var bm = d.getElementById("apriMenu"), menu = d.getElementById("menu");
  var chiudi = function () { menu.hidden = true; bm.setAttribute("aria-expanded", "false"); R.classList.remove("menu-aperto"); };
  bm.addEventListener("click", function () {
    var apri = menu.hidden; menu.hidden = !apri; bm.setAttribute("aria-expanded", String(apri)); R.classList.toggle("menu-aperto", apri);
  });
  $("a", menu).forEach(function (a) { a.addEventListener("click", chiudi); });
  d.addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { chiudi(); bm.focus(); } });

  /* Comparsa leggera allo scorrere */
  var vedi = $(".rivela, .servizi");
  if (ridotto || !("IntersectionObserver" in window)) vedi.forEach(function (el) { el.classList.add("visibile"); });
  else {
    var oss = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("visibile"); oss.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .12 });
    vedi.forEach(function (el) { oss.observe(el); });
  }

  /* Dati strutturati */
  var sc = d.getElementById("schema");
  if (sc && C.nome) {
    var j = { "@context": "https://schema.org", "@type": "VacationRental", name: C.nome,
      address: { "@type": "PostalAddress", streetAddress: C.indirizzo, postalCode: C.cap, addressLocality: C.citta, addressRegion: C.provincia, addressCountry: C.paese } };
    if (C.telefono) j.telephone = C.telefono;
    if (C.latitudine) j.geo = { "@type": "GeoCoordinates", latitude: C.latitudine, longitude: C.longitudine };
    if (C.mappa) j.hasMap = C.mappa;
    if (voto && n) j.aggregateRating = { "@type": "AggregateRating", ratingValue: voto.replace(",", "."), reviewCount: n, bestRating: 5 };
    var f0 = (C.scene || {}).facciata; if (f0 && f0.poster16) j.image = new URL(dir + f0.poster16.replace(/\.jpg$/i, "") + "-1920.jpg", location.href).href;
    sc.textContent = JSON.stringify(j);
  }
})();
