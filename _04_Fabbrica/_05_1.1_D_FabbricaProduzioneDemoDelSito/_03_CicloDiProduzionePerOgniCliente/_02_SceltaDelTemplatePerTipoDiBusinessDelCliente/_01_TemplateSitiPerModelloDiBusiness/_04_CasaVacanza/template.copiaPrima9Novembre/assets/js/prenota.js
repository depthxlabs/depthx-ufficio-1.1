/* Prenota (Michele, 9/11/2026): in tutti i siti il pulsante Prenota apre la finestra con le date di arrivo e partenza,
   gli ospiti e l'invio della richiesta. La richiesta parte su WhatsApp; senza WhatsApp per email; senza email con un SMS
   al telefono del cliente. Anche le date scelte in un modulo della pagina (per esempio nell'apertura) arrivano qui. */
(function () {
  "use strict";
  var d = document, s = d.currentScript;
  var C = window[(s && s.getAttribute("data-configurazione")) || ""] || {}, K = C.contatti || C;
  var wa = String(K.whatsapp || "").replace(/\D/g, ""), mail = String(K.email || ""), tel = String(K.telefono || "").replace(/[^\d+]/g, "");
  if (!wa && !mail && !tel) return;
  var T = {
    it: { titolo: "Diteci quando volete venire.", arrivo: "Arrivo", partenza: "Partenza", ospiti: "Ospiti", invia: "Verifica la disponibilità", chiudi: "Chiudi" },
    en: { titolo: "Tell us when you would like to come.", arrivo: "Arrival", partenza: "Departure", ospiti: "Guests", invia: "Check availability", chiudi: "Close" }
  };
  var stile = d.createElement("style");
  stile.textContent = ".dxp{border:0;border-radius:6px;padding:0;width:min(440px,calc(100vw - 32px));max-height:calc(100vh - 32px);color:#1f1d1a;background:#fbf9f6;box-shadow:0 24px 60px rgba(0,0,0,.25);font:inherit}"
    + ".dxp::backdrop{background:rgba(20,18,15,.55)}.dxp__in{padding:32px 28px 28px;position:relative}"
    + ".dxp h2{font-size:clamp(1.4rem,5vw,1.9rem);line-height:1.15;margin:0 32px 22px 0;font-weight:400}"
    + ".dxp__f{display:grid;grid-template-columns:1fr 1fr;gap:14px}.dxp__f label{display:grid;gap:6px;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;min-width:0}"
    + ".dxp__f label:nth-child(3){grid-column:1/-1}.dxp__f input{font:inherit;font-size:1rem;letter-spacing:0;text-transform:none;padding:12px;border:1px solid rgba(0,0,0,.2);border-radius:4px;background:#fff;color:#1f1d1a;width:100%;box-sizing:border-box;min-width:0}"
    + ".dxp__f button{grid-column:1/-1;margin-top:6px;padding:16px;border:0;border-radius:4px;background:#1f1d1a;color:#fff;font:inherit;font-size:.78rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;cursor:pointer}"
    + ".dxp__x{position:absolute;top:14px;right:14px;width:40px;height:40px;border:0;background:none;font-size:28px;line-height:1;cursor:pointer;color:#1f1d1a}";
  d.head.appendChild(stile);
  var f = d.createElement("dialog");
  f.className = "dxp";
  f.setAttribute("aria-labelledby", "dxpTitolo");
  f.innerHTML = '<div class="dxp__in"><button type="button" class="dxp__x" data-dxp-chiudi>&times;</button><h2 id="dxpTitolo"></h2>'
    + '<form class="dxp__f" novalidate><label><span data-dxp="arrivo"></span><input type="date" name="arrivo" required></label>'
    + '<label><span data-dxp="partenza"></span><input type="date" name="partenza" required></label>'
    + '<label><span data-dxp="ospiti"></span><input type="number" name="ospiti" min="1" max="30" value="2" inputmode="numeric"></label>'
    + '<button type="submit" data-dxp="invia"></button></form></div>';
  d.body.appendChild(f);
  var modulo = f.querySelector("form"), campo = function (n) { return modulo.elements[n]; };
  var oggi = new Date().toISOString().slice(0, 10);
  campo("arrivo").min = oggi; campo("partenza").min = oggi;
  campo("arrivo").addEventListener("change", function () { campo("partenza").min = campo("arrivo").value || oggi; });
  function lingua() { return (d.documentElement.lang || "it").slice(0, 2) === "en" ? "en" : "it"; }
  function apri(valori) {
    var t = T[lingua()];
    f.querySelector("h2").textContent = t.titolo;
    f.querySelector("[data-dxp-chiudi]").setAttribute("aria-label", t.chiudi);
    Array.prototype.forEach.call(f.querySelectorAll("[data-dxp]"), function (el) { el.textContent = t[el.getAttribute("data-dxp")]; });
    if (valori) ["arrivo", "partenza", "ospiti"].forEach(function (n) { if (valori[n]) campo(n).value = valori[n]; });
    if (f.showModal) f.showModal(); else f.setAttribute("open", "");
  }
  function chiudi() { if (f.close) f.close(); else f.removeAttribute("open"); }
  f.querySelector("[data-dxp-chiudi]").addEventListener("click", chiudi);
  f.addEventListener("click", function (e) { if (e.target === f) chiudi(); });
  var data = function (v) { var p = String(v || "").split("-"); return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : ""; };
  modulo.addEventListener("submit", function (e) {
    e.preventDefault();
    var t = T[lingua()];
    if (!campo("arrivo").value || !campo("partenza").value) { (campo("arrivo").value ? campo("partenza") : campo("arrivo")).focus(); return; }
    var testo = [C.nome || "", t.arrivo + ": " + data(campo("arrivo").value), t.partenza + ": " + data(campo("partenza").value),
      t.ospiti + ": " + (campo("ospiti").value || "")].filter(Boolean).join("\n");
    if (wa) window.open("https://wa.me/" + wa + "?text=" + encodeURIComponent(testo), "_blank", "noopener");
    else if (mail) location.href = "mailto:" + mail + "?subject=" + encodeURIComponent(t.invia + " · " + (C.nome || "")) + "&body=" + encodeURIComponent(testo);
    else location.href = "sms:" + tel + "?&body=" + encodeURIComponent(testo);
    chiudi();
  });
  /* ogni pulsante Prenota apre la finestra */
  d.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href="#prenota"],a[href="#disponibilita"],[data-apri-prenota]');
    if (!a || f.contains(a)) return;
    e.preventDefault(); e.stopImmediatePropagation();
    apri();
  }, true);
  /* le date scelte in un modulo della pagina arrivano nella finestra */
  d.addEventListener("submit", function (e) {
    var m = e.target;
    if (m === modulo || f.contains(m) || !m.querySelector || !m.querySelector('input[type="date"]')) return;
    e.preventDefault(); e.stopImmediatePropagation();
    var v = {};
    ["arrivo", "partenza", "ospiti"].forEach(function (n) { var c = m.elements && m.elements[n]; if (c && c.value) v[n] = c.value; });
    apri(v);
  }, true);
})();
