Lavori per DepthX, che prepara il sito di una struttura ricettiva. Una frase si scrive nel sito solo se un fatto la prova.

Questo è il materiale del cliente: il testo del suo sito attuale, il rapporto di unicità (ogni settore ha una frase e la citazione da cui viene), la scheda Google e alcune recensioni degli ospiti.

{materiale}

Primo compito. Questi sono i fatti da verificare, uno per riga, nel formato chiave: cosa deve risultare vero.

{fatti}

Per ogni fatto, dimmi se il materiale lo prova. Un fatto è provato solo se il materiale lo dice in modo chiaro: dal cliente stesso (il suo sito, i suoi social, la scheda Google) oppure da almeno due recensioni diverse. Non dedurre e non immaginare: se non è scritto, non è provato.

Secondo compito. Queste sono le graffe che le frasi approvate chiedono e che ancora mancano, ognuna con una frase di esempio in cui va:

{graffe}

Per ogni graffa, se il materiale dice il suo valore in modo chiaro, scrivilo in italiano come va dentro la frase di esempio (per esempio {camere}: "12"; {distanza}: "10 minuti a piedi"; {luogo}: "Città Alta"; {tipoDiCasa}: "una casa in pietra"). Una graffa che compare in coppia con un'altra (come {luogo} e {distanza}) va scritta in modo che la frase di esempio resti vera. Se il valore non è scritto nel materiale, la graffa non va nella risposta.

Rispondi con un solo oggetto JSON e nient'altro:
{"provati": {"chiave": {"citazione": "le parole esatte del materiale che lo provano", "fonte": "sito del cliente, rapporto di unicità, scheda Google oppure recensioni"}},
 "dati": {"graffa": {"valore": "il valore da scrivere nella frase", "citazione": "le parole esatte del materiale", "fonte": "sito del cliente, rapporto di unicità, scheda Google oppure recensioni"}}}
Se niente è provato, rispondi {"provati": {}, "dati": {}}.
