/* Casa Vacanza: i valori del sito, vuoti nel template. La fabbrica aggiunge in fondo i valori veri del cliente.
   I testi visibili stanno nella pagina (italiano tra i tag, inglese in data-en). */
window.CASA_CONFIG = {
  nome: "",
  nomeBreve: "",
  posizione: "",
  cap: "",
  citta: "",
  provincia: "",
  paese: "IT",
  latitudine: "",
  longitudine: "",
  telefono: "",
  whatsapp: "",
  email: "",
  mappa: "",
  recensioniGoogle: "",
  votoGoogle: "",
  numeroRecensioni: "",
  lingue: ["it", "en"],
  logo: "",
  icona: "assets/logo/icona.svg",
  fotoDir: "media/foto/",
  larghezze16: [640, 1280, 1920],
  larghezze9: [480, 720, 1080],
  servizi: [],
  scene: {
    facciata:   { poster16: "", poster9: "", it: "", en: "" },
    camera:     { poster16: "", poster9: "", it: "", en: "" },
    vasca:      { poster16: "", poster9: "", it: "", en: "" },
    cucina:     { poster16: "", poster9: "", it: "", en: "" },
    cortile:    { poster16: "", poster9: "", it: "", en: "" },
    recensione: { poster16: "", poster9: "", it: "", en: "" },
    g1:         { poster16: "", poster9: "", it: "", en: "" },
    g2:         { poster16: "", poster9: "", it: "", en: "" },
    g3:         { poster16: "", poster9: "", it: "", en: "" },
    g4:         { poster16: "", poster9: "", it: "", en: "" },
    g5:         { poster16: "", poster9: "", it: "", en: "" },
    g6:         { poster16: "", poster9: "", it: "", en: "" }
  }
};

/* Segnaposto del template: foto grigie neutre, nessun cliente. La fabbrica sostituisce questo blocco. */
(function (C) {
  var n = 0;
  Object.keys(C.scene).forEach(function (id) { n++; var k = ("0" + n).slice(-2); C.scene[id].poster16 = "foto_" + k + "_16x9.jpg"; C.scene[id].poster9 = "foto_" + k + "_9x16.jpg"; });
})(window.CASA_CONFIG);
