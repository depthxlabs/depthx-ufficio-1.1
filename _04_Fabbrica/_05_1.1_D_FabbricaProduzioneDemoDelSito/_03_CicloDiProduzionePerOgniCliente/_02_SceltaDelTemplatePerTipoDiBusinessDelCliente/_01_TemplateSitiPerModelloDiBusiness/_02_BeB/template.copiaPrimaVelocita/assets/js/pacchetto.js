/* Pacchetto Advanced DepthX (nessuna libreria esterna), comune ai 4 tipi di struttura.
   Animazioni di transizione (3): 1 comparsa morbida dei blocchi (main.js, data-rivela), 2 velo tra una pagina e l'altra (qui),
   3 tendina che svela il titolo d'apertura (style.css). Elemento 3D di codice (1): gira da solo, il visitatore non deve fare niente
   (Michele, 11/11/2026). Pulsanti animati: WhatsApp e chiamata, Prenota, mappa (style.css). */
(function () {
  "use strict";
  var calmo = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Animazione 2 di 3: il velo tra le pagine */
  var velo = document.createElement("div");
  velo.className = "pk-velo"; velo.setAttribute("aria-hidden", "true");
  document.body.appendChild(velo);
  requestAnimationFrame(function () { document.body.classList.add("pk-pronta"); });
  window.addEventListener("pageshow", function () { document.body.classList.remove("pk-esce"); });
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || calmo || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || a.target) return;
    var h = a.getAttribute("href");
    if (!/^[\w-]+\.html/.test(h)) return;
    if (h.split("#")[0] === (location.pathname.split("/").pop() || "index.html") && h.indexOf("#") > -1) return;
    e.preventDefault();
    document.body.classList.add("pk-esce");
    setTimeout(function () { location.href = a.href; }, 420);
  });

  /* Il 3D più ricco (Michele, 11/11/2026): lo spessore vero (strati tra il fronte e il retro), l'anello nel foro della chiave,
     il nucleo pieno del dado (gli angoli arrotondati non lasciano vedere attraverso), il monogramma sul retro del biglietto e
     "Saluti da" con il comune vero sulla cartolina */
  function arricchisci(ogg, dado) {
    var el = function (classe, testo) { var e = document.createElement("span"); e.className = classe; e.setAttribute("aria-hidden", "true"); if (testo) e.textContent = testo; return e; };
    if (dado) {
      ["", "rotateY(90deg) ", "rotateY(180deg) ", "rotateY(-90deg) ", "rotateX(90deg) ", "rotateX(-90deg) "].forEach(function (r) {
        var n = el("pk-nucleo"); n.style.transform = r + "translateZ(102px)"; ogg.insertBefore(n, ogg.firstChild);
      });
      return;
    }
    var spessore = ogg.classList.contains("pk-chiave") ? 2.5 : ogg.classList.contains("pk-biglietto") ? 2 : 1;
    for (var z = -spessore; z <= spessore + 0.01; z += 0.5) {
      var s = el("pk-strato"); s.style.transform = "translateZ(" + z.toFixed(1) + "px)"; ogg.insertBefore(s, ogg.firstChild);
    }
    if (ogg.classList.contains("pk-chiave")) ogg.appendChild(el("pk-anello"));
    var K = window.SITO_CONFIG || {}, C = K.contatti || {};
    /* il monogramma sul retro del biglietto è tolto (Michele, 11/11/2026): il retro resta pulito */
    if (ogg.classList.contains("pk-cartolina") && C.comune) {
      var fronte = ogg.querySelector(".pk-fronte"), it = (document.documentElement.lang || "it").indexOf("en") !== 0;
      if (fronte) { var sal = el("pk-saluti", (it ? "Saluti da " : "Greetings from ") + C.comune); sal.setAttribute("data-en", "Greetings from " + C.comune); fronte.appendChild(sal); }
    }
  }

  /* L'elemento 3D gira da solo (Michele, 11/11/2026: non è mai il visitatore a doverlo fare): la chiave, il biglietto e la
     cartolina mostrano davanti e dietro, il dado tutte le facce; resta sempre dentro il suo riquadro. Si gira solo quando si
     vede, e con "riduci movimento" resta fermo sul fronte. */
  Array.prototype.forEach.call(document.querySelectorAll("[data-3d]"), function (scena) {
    var ogg = scena.firstElementChild, dado = scena.getAttribute("data-asse") === "xy", t = 0, ultimo = 0, visibile = false;
    arricchisci(ogg, dado);
    scena.style.setProperty("--altezza-scena", scena.clientHeight + "px");
    /* Il testo non esce mai dalla faccia (Michele, 11/11/2026: "la scritta viene sotto"): se il contenuto di una faccia è più
       alto o più largo della faccia, la scritta si rimpicciolisce a passi fino a starci; si riprova quando arrivano i caratteri */
    function adatta() {
      Array.prototype.forEach.call(ogg.querySelectorAll(".pk-faccia"), function (f) {
        /* tutto il contenuto della faccia (nome, indirizzo, telefono, email) si riduce insieme, in proporzione */
        var figli = Array.prototype.filter.call(f.children, function (c) { return !c.matches("picture, .pk-monogramma, .pk-chiave__foro"); });
        var esce = function () { return f.scrollHeight > f.clientHeight + 1 || f.scrollWidth > f.clientWidth + 1; };
        figli.forEach(function (c) { c.style.zoom = ""; });
        for (var s = 0.95; s >= 0.6 && esce(); s -= 0.05) figli.forEach(function (c) { c.style.zoom = s.toFixed(2); });
      });
    }
    adatta();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(adatta);
    window.addEventListener("resize", adatta);
    function disegna() {
      var rx = dado ? 18 * Math.sin(t / 7090) - 14 : 6 * Math.sin(t / 8180);  /* lento (Michele, 11/11/2026) */
      var ry = dado ? t / 89.3 : (t / 74.6) % 360;  /* il 10% più veloce, poi un altro 12% (Michele, 11/11/2026) */
      ogg.style.transform = "rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg)";
      /* il riflesso scorre sulle facce mentre gira; l'ombra a terra si stringe quando l'oggetto è di taglio */
      var a = ((ry % 360) + 360) % 360;
      ogg.style.setProperty("--luce", (a / 360 * 200 - 50).toFixed(1) + "%");
      scena.style.setProperty("--ombra", dado ? "0.75" : (0.25 + 0.75 * Math.abs(Math.cos(a * Math.PI / 180))).toFixed(3));
    }
    function gira(ora) {
      if (visibile) { t += Math.min(64, ora - (ultimo || ora)); disegna(); }
      ultimo = ora;
      requestAnimationFrame(gira);
    }
    disegna();
    if (calmo) return;
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { visibile = es[0].isIntersecting; }).observe(scena);
    else visibile = true;
    requestAnimationFrame(gira);
  });
})();
