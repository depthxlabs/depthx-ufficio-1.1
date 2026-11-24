/* Configurazione del template Agriturismo DepthX. La fabbrica scrive qui i dati veri del cliente. */
window.AGRI_CONFIG = {
  nome: "Agriturismo Il Crepuscolo",
  tipo: "Agriturismo",
  logo: "",                       /* PNG o SVG del logo del cliente; vuoto = il nome nel serif del template */
  contatti: {
    telefono: "",                 /* come si legge, per esempio +39 333 000 0000 */
    whatsapp: "",                 /* solo cifre con il prefisso, per esempio 39333... */
    email: "",
    via: "", cap: "", comune: "", provincia: "", regione: "", paese: "IT",
    lat: null, lng: null,
    facebook: "", instagram: ""
  },
  google: {
    voto: "",                     /* il voto della scheda Google, per esempio "4,7" */
    recensioni: 0,                /* il numero vero delle recensioni Google: il sito scrive "più di" la decina sotto */
    placeId: "",                  /* se c'è, il link va a search.google.com/local/reviews?placeid=... */
    linkRecensioni: ""            /* altrimenti la ricerca Google del nome esatto con "recensioni" */
  },
  lingue: ["it", "en"],
  sezioni: { podere: true, paesaggio: true, camere: true, famiglie: true },
  fotoDir: "media/foto/",
  /* per ogni foto la fabbrica salva <nome>.jpg/.webp a 2200 punti e le varianti -640 e -1280 */
  scene: {
    casa:       { poster16: "", poster9: "", it: "", en: "" },
    podere:     { poster16: "", poster9: "", it: "", en: "" },
    paesaggio:  { poster16: "", poster9: "", it: "", en: "" },
    sala:       { poster16: "", poster9: "", it: "", en: "" },
    pasta:      { poster16: "", poster9: "", it: "", en: "" },
    tavola:     { poster16: "", poster9: "", it: "", en: "" },
    camera:     { poster16: "", poster9: "", it: "", en: "" },
    famiglie:   { poster16: "", poster9: "", it: "", en: "" },
    recensione: { poster16: "", poster9: "", it: "", en: "" }
  }
};

/* DepthX, fabbrica dei siti: i dati veri del cliente (CRM, scheda Google, foto). */
(function (C) {
  if (!C) return;
  C.nome = "Agriturismo Il Crepuscolo";
  C.tipo = "Agriturismo";
  C.logo = "";
  C.contatti = {"telefono": "+39 333 314 6682", "whatsapp": "393333146682", "email": "ilcrepuscoloagriturismo@gmail.com", "via": "Contrada Piano Rivitale, 1", "cap": "85034", "comune": "Francavilla in Sinni", "provincia": "PZ", "regione": "Basilicata", "paese": "IT", "lat": 40.0374059, "lng": 16.2265083, "facebook": "https://facebook.com/p/Agriturismo-Il-Crepuscolo-100063533081879", "instagram": ""};
  C.google = {"voto": "", "recensioni": 0, "placeId": "", "linkRecensioni": "https://www.google.com/search?q=Agriturismo+Il+Crepuscolo+recensioni"};
  C.lingue = ["it", "en"];
  C.sezioni = { podere: true, paesaggio: true, camere: true, famiglie: true };
  C.fotoDir = "media/foto/";
  C.scene = {
    "casa": {
      "poster16": "foto_01_16x9.jpg",
      "poster9": "foto_01_9x16.jpg",
      "it": "La casa in pietra con la scala e i fiori",
      "en": "The stone house with its steps and flowers"
    },
    "podere": {
      "poster16": "foto_02_16x9.jpg",
      "poster9": "foto_02_9x16.jpg",
      "it": "La casa in pietra su più piani, con il giardino",
      "en": "The stone house on several floors, with its garden"
    },
    "paesaggio": {
      "poster16": "foto_03_16x9.jpg",
      "poster9": "foto_03_9x16.jpg",
      "it": "Il prato e i boschi intorno alla casa",
      "en": "The meadow and the woods around the house"
    },
    "sala": {
      "poster16": "foto_04_16x9.jpg",
      "poster9": "foto_04_9x16.jpg",
      "it": "La sala con la finestra sul verde",
      "en": "The dining room with its window on the green"
    },
    "pasta": {
      "poster16": "foto_05_16x9.jpg",
      "poster9": "foto_05_9x16.jpg",
      "it": "La pasta fatta in casa",
      "en": "Home-made pasta"
    },
    "tavola": {
      "poster16": "foto_06_16x9.jpg",
      "poster9": "foto_06_9x16.jpg",
      "it": "Un tavolo apparecchiato nella sala",
      "en": "A table laid in the dining room"
    },
    "camera": {
      "poster16": "foto_07_16x9.jpg",
      "poster9": "foto_07_9x16.jpg",
      "it": "Una camera",
      "en": "A bedroom"
    },
    "famiglie": {
      "poster16": "foto_08_16x9.jpg",
      "poster9": "foto_08_9x16.jpg",
      "it": "Il prato davanti alla casa",
      "en": "The lawn in front of the house"
    },
    "recensione": {
      "poster16": "foto_09_16x9.jpg",
      "poster9": "foto_09_9x16.jpg",
      "it": "La terrazza con i fiori",
      "en": "The terrace with flowers"
    }
  };
})(window.AGRI_CONFIG);
