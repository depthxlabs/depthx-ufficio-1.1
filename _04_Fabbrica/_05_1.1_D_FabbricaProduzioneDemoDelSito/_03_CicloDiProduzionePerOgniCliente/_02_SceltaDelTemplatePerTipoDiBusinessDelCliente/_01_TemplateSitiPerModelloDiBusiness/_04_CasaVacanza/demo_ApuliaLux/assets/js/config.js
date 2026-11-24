/* Casa Vacanza: i valori del sito, vuoti nel template. La fabbrica aggiunge in fondo i valori veri del cliente.
   I testi visibili stanno nella pagina (italiano tra i tag, inglese in data-en). */
window.CASA_CONFIG = {
  nome: "",
  nomeBreve: "",
  indirizzo: "",
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

/* DepthX, fabbrica dei siti: i dati del cliente. */
(function (C) {
  Object.assign(C, {"nome": "Apulia lux casa vacanza con vasca idromassaggio", "nomeBreve": "Apulia Lux", "indirizzo": "Via Regina Elena 103", "cap": "74123", "citta": "Taranto", "provincia": "TA", "paese": "IT", "latitudine": "40.4672157", "longitudine": "17.247466", "telefono": "+39 391 411 2688", "whatsapp": "+39 391 411 2688", "email": "", "mappa": "https://maps.google.com/?cid=8049420193536163375", "recensioniGoogle": "https://www.google.com/search?q=Apulia+lux+casa+vacanza+con+vasca+idromassaggio+recensioni", "votoGoogle": "", "numeroRecensioni": "", "lingue": ["it", "en"], "logo": "", "icona": "assets/logo/icona.svg", "servizi": ["vasca", "cucina", "tv"]});
  var V = {"facciata": ["foto_01_16x9.jpg", "foto_01_9x16.jpg"], "camera": ["foto_02_16x9.jpg", ""], "vasca": ["foto_03_16x9.jpg", ""], "cucina": ["", "foto_04_9x16.jpg"], "cortile": ["foto_05_16x9.jpg", ""], "recensione": ["foto_10_16x9.jpg", ""], "g1": ["", "foto_09_9x16.jpg"], "g2": ["foto_07_16x9.jpg", ""], "g3": ["foto_08_16x9.jpg", ""], "g4": ["", "foto_06_9x16.jpg"], "g5": ["foto_11_16x9.jpg", ""], "g6": ["foto_12_16x9.jpg", ""]};
  Object.keys(V).forEach(function (id) { C.scene[id].poster16 = V[id][0]; C.scene[id].poster9 = V[id][1]; });
})(window.CASA_CONFIG);
