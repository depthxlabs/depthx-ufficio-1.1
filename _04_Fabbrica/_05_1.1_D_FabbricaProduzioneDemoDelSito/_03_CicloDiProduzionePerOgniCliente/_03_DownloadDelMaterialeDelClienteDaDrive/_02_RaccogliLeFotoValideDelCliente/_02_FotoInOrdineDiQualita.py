"""Le foto in ordine di qualità: prima il voto, poi la nitidezza, poi la grandezza in punti."""


def fotoInOrdineDiQualita(foto):
    return sorted(foto, key=lambda voce: (-(voce.get("qualita") or 0), -(voce.get("nitidezza") or 0),
                                          -((voce.get("larghezza") or 0) * (voce.get("altezza") or 0))))
