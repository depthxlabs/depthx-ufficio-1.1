Lavori per DepthX, che prepara il sito di una struttura ricettiva. Nel sito entra solo una frase verificata: ogni cosa che dice della struttura è scritta nel materiale del cliente o nei suoi dati.

Questo è il materiale del cliente: il testo del suo sito attuale, il rapporto di unicità, la scheda Google e alcune recensioni degli ospiti.

{materiale}

Questi sono i dati del cliente, dal CRM e dal materiale:

{dati}

Primo compito. Queste sono le frasi candidate, una per riga, con il loro numero e, tra parentesi quadre, l'argomento della sezione della pagina dove vanno:

{frasi}

Per ogni frase decidi se è verificata.
- È verificata solo se ogni cosa che afferma sulla struttura (servizi, cibo, persone, luoghi, distanze, storia, modo di lavorare) è scritta in modo chiaro nel materiale o nei dati: dal cliente stesso (il suo sito, la scheda Google, i dati) oppure da almeno due recensioni diverse.
- Una frase che il materiale smentisce, anche solo in parte, non è verificata. Per esempio "Il caffè lo prepariamo al momento" non è verificata dove la colazione è a buffet o la struttura è senza personale.
- Non dedurre e non immaginare: se non è scritto, non è verificata.
- Una frase è verificata solo se parla dell'argomento tra parentesi quadre. Sotto "Chi siamo" vanno solo frasi su chi è e cosa fa la struttura, mai l'indirizzo, la posizione o i contatti; sotto "Gli spazi comuni e gli esterni" solo gli spazi, mai dove si trova la struttura. L'indirizzo e la posizione vanno solo sotto "Dove siamo e come arrivare". Telefono, email e inviti a scrivere o prenotare vanno sotto un argomento solo se parlano di quell'argomento (per esempio "Per le camere libere nelle vostre date, chiamateci" sotto "Le camere"), e sempre sotto l'invito a prenotare e i contatti. I titoli valgono se annunciano l'argomento.
- Nei dati, fotoDelCliente elenca le aree di cui il cliente ha le foto (per esempio ristorante, colazione, giardino): una foto prova che quell'area esiste, non i suoi dettagli. "Il ristorante vi aspetta" è verificata con la foto del ristorante; "La cucina è casalinga" no.
- Sono verificate anche le frasi che non affermano niente sulla struttura: titoli, note legali, inviti a scrivere, chiamare o prenotare, purché il contatto che nominano sia nei dati, e gli inviti a leggere le recensioni su Google (per esempio "Leggete tutte le recensioni su Google").

Secondo compito. Questi sono gli argomenti del sito, uno per riga nel formato chiave: argomento.

{argomenti}

Per ogni argomento scegli dal testo del sito attuale del cliente fino a 5 frasi che lo raccontano bene, copiate parola per parola. Ogni frase deve parlare proprio di quell'argomento e di nient'altro: sotto "Le camere" solo frasi sulle camere, sotto "La colazione" solo frasi sulla colazione. Una frase che parla di un altro argomento, o di più argomenti insieme, non va. Prendi solo frasi intere e chiare, in italiano corretto e senza errori di battitura o di grammatica, di almeno 5 parole, che parlano con il noi o in modo neutro: mai con io, mai chiamando l'ospite con il tu. Niente prezzi, offerte, orari che cambiano, voti o nomi di chi ha scritto recensioni. Se il sito non ha frasi buone per un argomento, lascia fuori l'argomento.

Terzo compito: per ogni frase verificata e per ogni frase scelta dal sito scrivi la sua traduzione in inglese, fedele, naturale e con lo stesso tono, senza aggiungere niente. I nomi propri e i nomi dei luoghi restano come sono. Nella traduzione non usare mai queste parole vietate, nemmeno dentro un'altra frase: {paroleVietate}.

Rispondi con un solo oggetto JSON e nient'altro:
{"verificate": {"numero della frase": {"citazione": "le parole esatte del materiale che la provano, al massimo 20", "fonte": "sito del cliente, dati, rapporto di unicità, scheda Google oppure recensioni", "inglese": "la frase in inglese"}},
 "dalSito": {"chiave dell'argomento": ["frase copiata parola per parola dal sito del cliente"]},
 "ingleseDalSito": {"frase copiata dal sito, uguale a quella in dalSito": "la frase in inglese"}}
Una frase non verificata non va nella risposta.
