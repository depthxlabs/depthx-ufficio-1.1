"""RICONOSCIMENTO DELLE FOTO SULLA MACCHINA, Linea 1.1 Outbound Websites, Download materiale clienti.

Le 12 categorie dell'ospitalità assegnate a ogni foto da un modello di immagini (OpenCLIP ViT-B-32) che gira sulla macchina,
senza Claude e senza limiti di richieste: per ogni foto vince la categoria con la descrizione più vicina.
Il voto di qualità resta quello misurato dal motore (grandezza e nitidezza).
"""
import open_clip, torch
from PIL import Image

CATEGORIE = {
    "esterno della struttura": ["a photo of the outside facade of a hotel building", "a photo of the exterior of a guesthouse or farmhouse building"],
    "esterni senza struttura": ["a photo of a garden, a landscape or a scenic view", "a photo of nature, hills, a lake or mountains without buildings"],
    "camere": ["a photo of a hotel bedroom with a bed", "a photo of a guest room interior with beds"],
    "bagni": ["a photo of a bathroom with a shower or a sink", "a photo of a hotel bathroom"],
    "piscina": ["a photo of a swimming pool", "a photo of an outdoor pool with sun loungers"],
    "ristorante": ["a photo of a restaurant dining room with tables", "a photo of a plated dish served at a restaurant"],
    "colazione": ["a photo of a breakfast buffet", "a photo of a breakfast table with croissants, coffee and juice"],
    "prodotti": ["a photo of wine bottles or local food products", "a photo of jars, cheese, oil or farm products"],
    "persone": ["a photo of people posing for the camera", "a portrait photo of a person or a group of people"],
    "locandine": ["a flyer or poster with a lot of text", "a menu or an advertisement image with printed text"],
    "logo": ["a logo on a plain background", "a brand logo"],
    "altro": ["a photo of a hotel lobby, reception or bar", "a photo of a living room or a common area of a hotel"],
}


class Riconoscimento:
    def __init__(self):
        torch.set_num_threads(max(1, torch.get_num_threads()))
        self.modello, _, self.prepara = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        self.modello.eval()
        testi = open_clip.get_tokenizer("ViT-B-32")
        self.nomi = list(CATEGORIE)
        with torch.no_grad():
            vettori = []
            for nome in self.nomi:
                v = self.modello.encode_text(testi(CATEGORIE[nome]))
                v = v / v.norm(dim=-1, keepdim=True)
                vettori.append(v.mean(dim=0))
            self.testi = torch.stack(vettori)
            self.testi = self.testi / self.testi.norm(dim=-1, keepdim=True)

    def categorie(self, percorsi, insieme=16):
        """La categoria di ogni foto, nell'ordine dei percorsi."""
        uscita = []
        for k in range(0, len(percorsi), insieme):
            immagini = torch.stack([self.prepara(Image.open(p).convert("RGB")) for p in percorsi[k:k + insieme]])
            with torch.no_grad():
                v = self.modello.encode_image(immagini)
                v = v / v.norm(dim=-1, keepdim=True)
                punteggi = v @ self.testi.T
            uscita += [self.nomi[i] for i in punteggi.argmax(dim=-1).tolist()]
        return uscita
