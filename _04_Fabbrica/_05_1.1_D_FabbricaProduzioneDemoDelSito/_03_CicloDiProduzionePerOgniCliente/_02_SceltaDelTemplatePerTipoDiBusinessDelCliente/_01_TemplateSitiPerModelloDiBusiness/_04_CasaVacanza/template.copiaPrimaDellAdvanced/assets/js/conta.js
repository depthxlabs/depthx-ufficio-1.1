/* DepthX: i numeri che contano. Un elemento con data-conta (per esempio il voto Google) sale da zero al suo valore quando
   entra nello schermo, con la virgola o il punto del suo testo. Con "riduci movimento" il numero resta fermo. */
(function () {
  if (!("IntersectionObserver" in window) || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  var anima = function (el) {
    var testo = (el.textContent || "").trim(), m = testo.match(/^(\d+)(?:([.,])(\d+))?$/);
    if (!m) return;
    var fine = parseFloat(m[1] + (m[3] ? "." + m[3] : "")), cifre = m[3] ? m[3].length : 0, inizio = null, tempo = 1400;
    var passo = function (ora) {
      if (inizio === null) inizio = ora;
      var t = Math.min(1, (ora - inizio) / tempo), v = fine * (1 - Math.pow(1 - t, 3));
      el.textContent = t < 1 ? v.toFixed(cifre).replace(".", m[2] || ".") : testo;
      if (t < 1) requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
  };
  var io = new IntersectionObserver(function (voci) {
    voci.forEach(function (v) { if (v.isIntersecting) { io.unobserve(v.target); anima(v.target); } });
  }, { threshold: 0.6 });
  Array.prototype.forEach.call(document.querySelectorAll("[data-conta]"), function (el) { io.observe(el); });
})();
