/* Configurazione del template Agriturismo DepthX. La fabbrica scrive qui i dati veri del cliente. */
window.AGRI_CONFIG = {
  nome: "",
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
    casa:       { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    podere:     { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    paesaggio:  { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    sala:       { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    pasta:      { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    tavola:     { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    camera:     { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    famiglie:   { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" },
    recensione: { poster16: "segnaposto_16x9.svg", poster9: "segnaposto_9x16.svg", it: "", en: "" }
  }
};
