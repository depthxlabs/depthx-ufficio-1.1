/* Configurazione del sito: la fabbrica scrive qui i dati del cliente. Voto e numero delle recensioni si leggono solo da qui.
   Foto: <scena>_16x9 e <scena>_9x16 in fotoDir, ognuna in -640, -1280, -2200 (.webp e .jpg). */
window.BEB_CONFIG = {
  bloccoDellaFoto: ".due__foto, .colazione__seconda > *, .mosaico > *, .spazi > *, .casa__foto, .colazione__foto",  /* una scena senza foto toglie tutto il suo riquadro, senza lasciare cornici vuote (Michele, 9/11/2026) */
  "nome": "",
  "tipoSchema": "BedAndBreakfast",
  "posizione": {
    "via": "",
    "cap": "",
    "citta": "",
    "provincia": "",
    "paese": "IT"
  },
  "geo": {
    "lat": "",
    "lng": ""
  },
  "telefono": "",
  "whatsapp": "",
  "email": "",
  "mappa": "",
  "paginaRecensioni": "",
  "prenotazione": "",
  "facebook": "",
  "instagram": "",
  "voto": "",
  "recensioni": "",
  "orari": "",
  "lingue": [
    "it",
    "en"
  ],
  "logo": "",
  "fotoDir": "media/foto/",
  "videoDir": "media/video/",
  "scenaDellaHome": "casa",
  "scene": {
    "casa": {
      "poster16": "casa_16x9.jpg",
      "poster9": "casa_9x16.jpg",
      "it": "",
      "en": ""
    },
    "ingresso": {
      "poster16": "ingresso_16x9.jpg",
      "poster9": "ingresso_9x16.jpg",
      "it": "",
      "en": ""
    },
    "colazione": {
      "poster16": "colazione_16x9.jpg",
      "poster9": "colazione_9x16.jpg",
      "it": "",
      "en": ""
    },
    "sala": {
      "poster16": "sala_16x9.jpg",
      "poster9": "sala_9x16.jpg",
      "it": "",
      "en": ""
    },
    "credenza": {
      "poster16": "credenza_16x9.jpg",
      "poster9": "credenza_9x16.jpg",
      "it": "",
      "en": ""
    },
    "camera1": {
      "poster16": "camera1_16x9.jpg",
      "poster9": "camera1_9x16.jpg",
      "it": "",
      "en": ""
    },
    "camera2": {
      "poster16": "camera2_16x9.jpg",
      "poster9": "camera2_9x16.jpg",
      "it": "",
      "en": ""
    },
    "camera3": {
      "poster16": "camera3_16x9.jpg",
      "poster9": "camera3_9x16.jpg",
      "it": "",
      "en": ""
    },
    "bagno": {
      "poster16": "bagno_16x9.jpg",
      "poster9": "bagno_9x16.jpg",
      "it": "",
      "en": ""
    },
    "cucina": {
      "poster16": "cucina_16x9.jpg",
      "poster9": "cucina_9x16.jpg",
      "it": "",
      "en": ""
    },
    "terrazzo": {
      "poster16": "terrazzo_16x9.jpg",
      "poster9": "terrazzo_9x16.jpg",
      "it": "",
      "en": ""
    },
    "via": {
      "poster16": "via_16x9.jpg",
      "poster9": "via_9x16.jpg",
      "it": "",
      "en": ""
    },
    "ospiti": {
      "poster16": "ospiti_16x9.jpg",
      "poster9": "ospiti_9x16.jpg",
      "it": "",
      "en": ""
    }
  }
};
