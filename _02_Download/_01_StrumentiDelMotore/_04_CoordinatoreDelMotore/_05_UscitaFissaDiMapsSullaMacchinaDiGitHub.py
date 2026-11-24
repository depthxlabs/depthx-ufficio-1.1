# Uscita fissa di Google Maps sulla macchina di GitHub: il Chrome di Maps usa questo proxy locale (127.0.0.1:8898).
# Le destinazioni di Google vanno al proxy del server attraverso il tunnel Cloudflare "uscita-maps" (cloudflared access tcp
# su 127.0.0.1:8899), così Google vede sempre l'indirizzo del server; le altre destinazioni escono direttamente.
# Se il tunnel non risponde, Google non si raggiunge: mai dall'indirizzo di GitHub.
# La chiave (MAPS_USCITA_CHIAVE) e l'indirizzo del server (MAPS_INDIRIZZO_DEL_SERVER) non si stampano mai.
#   python -B _05_UscitaFissaDiMapsSullaMacchinaDiGitHub.py avvia      acceso fino alla fine del lavoro
#   python -B _05_UscitaFissaDiMapsSullaMacchinaDiGitHub.py verifica   stampa "indirizzo fisso: sì/no"
import asyncio
import base64
import os
import sys
import time
import urllib.request

PORTA_LOCALE = 8898
PORTA_DEL_TUNNEL = 8899
DOMINI_DEL_SERVER = ("google.com", "google.it", "gstatic.com", "googleusercontent.com", "ggpht.com", "googleapis.com", "api.ipify.org")


def chiave():
    return os.environ.get("MAPS_USCITA_CHIAVE", "").strip()


def dalServer(host):
    host = host.lower().rstrip(".")
    return any(host == dominio or host.endswith("." + dominio) for dominio in DOMINI_DEL_SERVER)


async def travasa(lettore, scrittore):
    try:
        while True:
            dati = await asyncio.wait_for(lettore.read(65536), 300)
            if not dati:
                break
            scrittore.write(dati)
            await scrittore.drain()
    except Exception:
        pass
    finally:
        try:
            scrittore.close()
        except Exception:
            pass


async def rifiuta(scrittore, stato, testo):
    try:
        scrittore.write(f"HTTP/1.1 {stato} {testo}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode())
        await scrittore.drain()
    except Exception:
        pass
    scrittore.close()


async def attraversoIlServer(host, porta):
    lettore, scrittore = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", PORTA_DEL_TUNNEL), 20)
    accesso = base64.b64encode(f"maps:{chiave()}".encode()).decode()
    scrittore.write(f"CONNECT {host}:{porta} HTTP/1.1\r\nHost: {host}:{porta}\r\nProxy-Authorization: Basic {accesso}\r\n\r\n".encode())
    await scrittore.drain()
    risposta = await asyncio.wait_for(lettore.readuntil(b"\r\n\r\n"), 30)
    if b" 200 " not in risposta.split(b"\r\n", 1)[0] + b" ":
        scrittore.close()
        raise ConnectionError("il server non apre la destinazione")
    return lettore, scrittore


async def cliente(lettore, scrittore):
    try:
        testa = await asyncio.wait_for(lettore.readuntil(b"\r\n\r\n"), 30)
    except Exception:
        scrittore.close()
        return
    parti = testa.split(b"\r\n", 1)[0].decode("latin-1").split(" ")
    if len(parti) != 3 or parti[0] != "CONNECT" or ":" not in parti[1]:
        await rifiuta(scrittore, 405, "Method Not Allowed")
        return
    host, porta = parti[1].rsplit(":", 1)
    try:
        if dalServer(host):
            lontano_lettore, lontano_scrittore = await attraversoIlServer(host, int(porta))
        else:
            lontano_lettore, lontano_scrittore = await asyncio.wait_for(asyncio.open_connection(host, int(porta)), 20)
    except Exception:
        await rifiuta(scrittore, 502, "Bad Gateway")
        return
    scrittore.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
    await scrittore.drain()
    await asyncio.gather(travasa(lettore, lontano_scrittore), travasa(lontano_lettore, scrittore))


async def avvia():
    server = await asyncio.start_server(cliente, "127.0.0.1", PORTA_LOCALE, limit=32768)
    print(f"uscita fissa di Maps accesa su 127.0.0.1:{PORTA_LOCALE}", flush=True)
    async with server:
        await server.serve_forever()


def indirizzoVistoDaFuori():
    apri = urllib.request.build_opener(urllib.request.ProxyHandler({"https": f"http://127.0.0.1:{PORTA_LOCALE}"}))
    for giro in range(6):
        try:
            return apri.open("https://api.ipify.org", timeout=20).read().decode().strip()
        except Exception:
            time.sleep(5)
    return ""


def verifica():
    atteso = os.environ.get("MAPS_INDIRIZZO_DEL_SERVER", "").strip()
    visto = indirizzoVistoDaFuori()
    fisso = bool(atteso) and visto == atteso
    print("indirizzo fisso:", "sì" if fisso else "no", flush=True)
    return fisso


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verifica":
        sys.exit(0 if verifica() else 1)
    if not chiave():
        raise SystemExit("MAPS_USCITA_CHIAVE mancante: uscita fissa di Maps non accesa")
    asyncio.run(avvia())
