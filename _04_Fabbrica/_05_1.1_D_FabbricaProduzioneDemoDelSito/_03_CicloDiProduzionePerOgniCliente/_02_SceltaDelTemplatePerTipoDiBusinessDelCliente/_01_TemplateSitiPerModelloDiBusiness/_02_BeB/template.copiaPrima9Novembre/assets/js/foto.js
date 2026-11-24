/* DepthX: le foto delle scene, costruite dal file di configurazione.
   Ogni <picture data-scena> prende la foto della sua scena (poster16 o poster9) in tre larghezze, WebP con JPEG di riserva;
   con data-telefono="9x16" sul telefono si vede la foto verticale. Una scena senza foto toglie il suo blocco. */
(function () {
  var nome = document.currentScript && document.currentScript.getAttribute("data-configurazione");
  var C = (nome && window[nome]) || {};
  var dir = C.fotoDir || "media/foto/";
  var L16 = C.larghezze16 || [640, 1280, 1920], L9 = C.larghezze9 || [480, 720, 1080];
  var serie = function (file, larg, est) {
    var b = dir + file.replace(/\.(jpe?g|webp)$/i, "");
    return larg.map(function (w) { return b + "-" + w + "." + est + " " + w + "w"; }).join(", ");
  };
  var sorgente = function (pic, img, srcset, tipo, media, sizes) {
    var s = document.createElement("source"); s.srcset = srcset; s.sizes = sizes;
    if (tipo) s.type = tipo; if (media) s.media = media; pic.insertBefore(s, img);
  };
  var togli = function (el) { if (el && el.parentNode) el.parentNode.removeChild(el); };
  var sezioni = [];
  Array.prototype.forEach.call(document.querySelectorAll("picture[data-scena]"), function (pic) {
    var sezione = pic.closest("section");
    if (sezione && sezioni.indexOf(sezione) < 0) sezioni.push(sezione);
  });
  Array.prototype.forEach.call(document.querySelectorAll("picture[data-scena]"), function (pic) {
    var s = (C.scene || {})[pic.getAttribute("data-scena")] || {}, img = pic.querySelector("img");
    var forma = pic.getAttribute("data-forma") || "16x9", file = forma === "9x16" ? s.poster9 : s.poster16;
    if (!file || !img) { togli((C.bloccoDellaFoto && pic.closest(C.bloccoDellaFoto)) || pic); return; }
    var larg = forma === "9x16" ? L9 : L16, sizes = pic.getAttribute("data-sizes") || "100vw";
    if (pic.getAttribute("data-telefono") === "9x16" && s.poster9 && forma !== "9x16") {
      var m = pic.getAttribute("data-media-telefono") || "(max-width: 760px)";
      sorgente(pic, img, serie(s.poster9, L9, "webp"), "image/webp", m, sizes);
      sorgente(pic, img, serie(s.poster9, L9, "jpg"), "image/jpeg", m, sizes);
    }
    sorgente(pic, img, serie(file, larg, "webp"), "image/webp", "", sizes);
    img.sizes = sizes; img.srcset = serie(file, larg, "jpg");
    img.src = dir + file.replace(/\.(jpe?g|webp)$/i, "") + "-" + larg[1] + ".jpg";
  });
  /* Una sezione che aveva foto e resta senza foto e senza testo esce intera, con i link del menu che portano a lei */
  sezioni.forEach(function (sezione) {
    if (!sezione.parentNode || sezione.querySelector("picture")) return;
    var testo = Array.prototype.some.call(sezione.querySelectorAll("p, li, blockquote, figcaption"), function (el) {
      return !el.closest("a, button") && el.textContent.trim().length > 0;
    });
    if (testo) return;
    if (sezione.id) Array.prototype.forEach.call(document.querySelectorAll('a[href="#' + sezione.id + '"]'), function (a) {
      togli(a.closest("li") || a);
    });
    togli(sezione);
  });
})();
