/* Template Agriturismo DepthX. Nessuna frase visibile vive qui: i testi sono nella pagina (IT tra i tag, EN in data-en). */
(function () {
  "use strict";
  var C = window.AGRI_CONFIG || {};
  var K = C.contatti || {};
  var G = C.google || {};
  var doc = document, root = doc.documentElement;
  var tutti = function (s, b) { return Array.prototype.slice.call((b || doc).querySelectorAll(s)); };
  var togli = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var pocoMoto = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var leggi = function (m, k) { try { return window[m].getItem(k); } catch (e) { return null; } };
  var scrivi = function (m, k, v) { try { window[m].setItem(k, v); } catch (e) { /* niente */ } };
  root.classList.remove("nojs"); root.classList.add("js");

  /* 1. sezioni facoltative: false = la sezione e il suo link nel menu spariscono */
  var sez = C.sezioni || {};
  tutti("[data-sezione]").forEach(function (el) { if (sez[el.getAttribute("data-sezione")] === false) togli(el); });
  tutti("[data-sezione-link]").forEach(function (el) { if (sez[el.getAttribute("data-sezione-link")] === false) togli(el); });

  /* 2. foto: srcset WebP e JPEG a 640, 1280 e 2200 punti; 16:9 su computer, 9:16 su telefono */
  var dir = C.fotoDir || "media/foto/";
  var scene = C.scene || {};
  var misure = { schermo: "100vw", larga: "(max-width: 768px) 100vw, 62vw", alta: "(max-width: 768px) 100vw, 44vw" };
  /* tre larghezze in punti per ogni forma, uguali in tutti i template: <scena>_<forma>-<larghezza>.webp e .jpg */
  function serie(nome, est) {
    var b = dir + nome.replace(/\.(jpe?g|webp)$/i, ""), larg = /9x16/.test(nome) ? (C.larghezze9 || [480, 720, 1080]) : (C.larghezze16 || [640, 1280, 1920]);
    return larg.map(function (w) { return b + "-" + w + "." + est + " " + w + "w"; }).join(", ");
  }
  function sorgente(pic, nome, media, sizes) {
    ["webp", "jpg"].forEach(function (est) {
      var s = doc.createElement("source");
      if (media) s.media = media;
      s.type = est === "webp" ? "image/webp" : "image/jpeg";
      s.srcset = serie(nome, est); s.sizes = sizes;
      pic.appendChild(s);
    });
  }
  function foto(pic, lingua) {
    var id = pic.getAttribute("data-scena"), s = scene[id], forma = pic.getAttribute("data-forma") || "larga";
    var fig = pic.closest("figure") || pic;
    if (!s || !(s.poster16 || s.poster9)) { togli(fig.tagName === "FIGURE" ? fig : pic); return; }
    var p16 = s.poster16 || s.poster9, p9 = s.poster9 || s.poster16;
    var img = doc.createElement("img");
    var verticale = forma === "alta";
    img.width = verticale ? 900 : 1600; img.height = verticale ? 1600 : 900;
    img.alt = (lingua === "en" ? s.en : s.it) || s.it || "";
    if (pic.hasAttribute("data-subito")) { img.setAttribute("fetchpriority", "high"); img.loading = "eager"; }
    else { img.loading = "lazy"; }
    img.decoding = "async";
    if (/\.jpg$/.test(p16)) {
      var sizes = misure[forma] || "100vw";
      if (forma === "schermo") { sorgente(pic, p9, "(max-width: 768px)", sizes); sorgente(pic, p16, "", sizes); img.src = dir + p16.replace(/\.jpg$/, "-1280.jpg"); }
      else { var n = verticale ? p9 : p16; sorgente(pic, n, "", sizes); img.src = dir + n.replace(/\.jpg$/, "-1280.jpg"); }
    } else {
      img.src = dir + (verticale ? p9 : p16);
    }
    pic.appendChild(img);
  }

  /* 3. lingua: IT nella pagina, EN in data-en; con lingue ["it"] il selettore sparisce */
  var lingue = C.lingue || ["it"];
  var lingua = leggi("localStorage", "agriLingua");
  if (lingue.indexOf(lingua) < 0) lingua = "it";
  if (lingue.indexOf("en") < 0) tutti("[data-lingua]").forEach(togli);
  function cambiaLingua(l) {
    lingua = l; root.lang = l;
    tutti("[data-en]").forEach(function (el) {
      if (!el.hasAttribute("data-it")) el.setAttribute("data-it", el.textContent);
      el.textContent = el.getAttribute(l === "en" ? "data-en" : "data-it");
    });
    tutti("[data-en-aria]").forEach(function (el) {
      if (!el.hasAttribute("data-it-aria")) el.setAttribute("data-it-aria", el.getAttribute("aria-label") || "");
      el.setAttribute("aria-label", el.getAttribute(l === "en" ? "data-en-aria" : "data-it-aria"));
    });
    tutti("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === l)); });
    tutti("picture[data-scena] img").forEach(function (img) {
      var s = scene[img.parentNode.getAttribute("data-scena")]; if (s) img.alt = (l === "en" ? s.en : s.it) || s.it || "";
    });
    scrivi("localStorage", "agriLingua", l);
  }
  tutti("picture[data-scena]").forEach(function (p) { foto(p, lingua); });
  tutti("[data-lang]").forEach(function (b) { b.addEventListener("click", function () { cambiaLingua(b.getAttribute("data-lang")); }); });
  if (lingua !== "it") cambiaLingua(lingua);

  /* 4. il marchio: il logo del cliente, altrimenti il nome nel serif del template */
  var tipo = C.tipo || "";
  var nome = C.nome || "";
  var breve = tipo && nome.toLowerCase().indexOf(tipo.toLowerCase() + " ") === 0 ? nome.slice(tipo.length + 1) : nome;
  tutti("[data-marchio]").forEach(function (m) {
    if (C.logo) { m.innerHTML = ""; var i = doc.createElement("img"); i.src = C.logo; i.alt = nome; m.appendChild(i); return; }
    var sopra = m.querySelector("[data-marchio-sopra]"), n = m.querySelector("[data-marchio-nome]");
    if (n && breve) n.textContent = breve;
    if (sopra) { if (breve !== nome) sopra.textContent = tipo; else togli(sopra); }
  });

  /* 5. collegamenti dai contatti veri */
  var cifre = (K.telefono || "").replace(/[^\d+]/g, "");
  var linkRecensioni = G.placeId ? "https://search.google.com/local/reviews?placeid=" + encodeURIComponent(G.placeId)
    : (G.linkRecensioni || (nome ? "https://www.google.com/search?q=" + encodeURIComponent(nome + " recensioni") : ""));
  var meta = K.lat && K.lng ? K.lat + "," + K.lng : [K.via, K.cap, K.comune, K.provincia].filter(Boolean).join(" ");
  var link = {
    telefono: cifre ? "tel:" + cifre : "",
    whatsapp: K.whatsapp ? "https://wa.me/" + K.whatsapp : "",
    email: K.email ? "mailto:" + K.email : "",
    recensioni: linkRecensioni,
    indicazioni: meta ? "https://www.google.com/maps/dir/?api=1&destination=" + encodeURIComponent(meta) : "",
    facebook: K.facebook || "", instagram: K.instagram || ""
  };
  tutti("[data-link]").forEach(function (a) {
    var v = link[a.getAttribute("data-link")];
    if (v) a.href = v; else if (/\{/.test(a.getAttribute("href") || "")) togli(a.closest("[data-se]") || a);
  });
  tutti("[data-se]").forEach(function (li) { if (!link[li.getAttribute("data-se")]) togli(li); });

  /* 6. voto e numero delle recensioni, sempre dai dati Google (mai scritti fissi) */
  var quante = parseInt(G.recensioni, 10) || 0;
  var riga = doc.querySelector("[data-voto-google]");
  if (G.voto && quante >= 10) {
    tutti("[data-voto]").forEach(function (el) { el.textContent = G.voto; });
    tutti("[data-recensioni-arrotondate]").forEach(function (el) { el.textContent = String(Math.floor(quante / 10) * 10); });
    var st = doc.querySelector("[data-stelle]");
    if (st) st.innerHTML = new Array(6).join('<svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.5l2.9 6.2 6.6.7-5 4.5 1.4 6.6L12 17.2l-5.9 3.3 1.4-6.6-5-4.5 6.6-.7z"/></svg>');
  } else togli(riga);


  /* 8. apertura con il logo, una volta per visita */
  var ap = doc.querySelector("[data-apertura]");
  if (ap) {
    if (leggi("sessionStorage", "agriAperta") || pocoMoto) togli(ap);
    else { scrivi("sessionStorage", "agriAperta", "1"); setTimeout(function () { ap.classList.add("via"); setTimeout(function () { togli(ap); }, 1000); }, 1500); }
  }

  /* 9. testata piena dopo la foto, menu a tutto schermo */
  var testata = doc.querySelector("[data-testata]");
  var eroe = doc.querySelector(".eroe");
  function scorri() { if (testata) testata.classList.toggle("piena", !eroe || window.scrollY > Math.min(eroe.offsetHeight * .6, 420)); }
  window.addEventListener("scroll", scorri, { passive: true }); scorri();
  var menu = doc.querySelector("[data-menu]"), apri = doc.querySelector("[data-apri-menu]");
  function chiudi() { if (!menu) return; menu.classList.remove("aperto"); apri.setAttribute("aria-expanded", "false"); setTimeout(function () { menu.hidden = true; }, 450); doc.body.style.overflow = ""; apri.focus(); }
  if (menu && apri) {
    apri.addEventListener("click", function () { menu.hidden = false; requestAnimationFrame(function () { menu.classList.add("aperto"); }); apri.setAttribute("aria-expanded", "true"); doc.body.style.overflow = "hidden"; var a = menu.querySelector("nav a"); if (a) a.focus(); });
    menu.querySelector("[data-chiudi-menu]").addEventListener("click", chiudi);
    tutti("nav a", menu).forEach(function (a) { a.addEventListener("click", chiudi); });
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape" && menu.classList.contains("aperto")) chiudi(); });
  }

  /* 10. comparsa leggera e icone che si disegnano */
  var guarda = tutti(".sale, [data-disegna]");
  if (pocoMoto || !("IntersectionObserver" in window)) guarda.forEach(function (el) { el.classList.add("visto", "disegnata"); });
  else {
    var io = new IntersectionObserver(function (voci) {
      voci.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("visto", "disegnata"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .08 });
    guarda.forEach(function (el) { io.observe(el); });
  }

  /* 11. i moduli raccolgono il messaggio e lo aprono su WhatsApp, oppure nella email */
  tutti("form[data-modulo]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var righe = [];
      tutti("label", f).forEach(function (l) {
        var campo = l.querySelector("input, select, textarea"), t = l.querySelector("span");
        if (campo && campo.value && t) righe.push(t.textContent + ": " + campo.value);
      });
      var testo = righe.join("\n");
      var via = (e.submitter && e.submitter.value) || "whatsapp";
      if (via === "email" && K.email) window.location.href = "mailto:" + K.email + "?subject=" + encodeURIComponent(nome) + "&body=" + encodeURIComponent(testo);
      else if (K.whatsapp) window.open("https://wa.me/" + K.whatsapp + "?text=" + encodeURIComponent(testo), "_blank", "noopener");
      else if (cifre) window.location.href = "tel:" + cifre;
    });
  });
  var oggi = new Date().toISOString().slice(0, 10);
  tutti('input[type="date"]').forEach(function (i) { i.min = oggi; });

  /* 12. dati strutturati per Google */
  var ld = { "@context": "https://schema.org", "@type": ["LodgingBusiness", "Restaurant"], name: nome, servesCuisine: "Italiana",
    telephone: K.telefono || undefined, email: K.email || undefined, url: window.location.href.split("#")[0],
    address: { "@type": "PostalAddress", streetAddress: K.via, postalCode: K.cap, addressLocality: K.comune, addressRegion: K.provincia, addressCountry: K.paese || "IT" },
    sameAs: [K.facebook, K.instagram].filter(Boolean) };
  if (K.lat && K.lng) ld.geo = { "@type": "GeoCoordinates", latitude: K.lat, longitude: K.lng };
  if (G.voto && quante) ld.aggregateRating = { "@type": "AggregateRating", ratingValue: String(G.voto).replace(",", "."), reviewCount: quante, bestRating: 5 };
  var sc = doc.createElement("script"); sc.type = "application/ld+json"; sc.textContent = JSON.stringify(ld); doc.head.appendChild(sc);
  tutti("[data-anno]").forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
})();
