// Pitstop 4 (task #609): l'impronta dei file delle demo, calcolata come la calcola wrangler (blake3 del contenuto in base64
// più l'estensione, primi 32 caratteri). Con la stessa impronta Cloudflare riconosce i file che ha già e chiede di caricare
// solo quelli nuovi.
// Uso: node _10_ImprontaDeiFile.js <cartella di blake3-wasm>  con la lista dei file (JSON) in ingresso; esce la lista delle impronte.
const fs = require("fs");
const path = require("path");
const blake3 = require(process.argv[2]);

let ingresso = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (pezzo) => { ingresso += pezzo; });
process.stdin.on("end", () => {
  const impronte = JSON.parse(ingresso).map((file) => {
    const contenuto = fs.readFileSync(file).toString("base64");
    return blake3.hash(contenuto + path.extname(file).substring(1)).toString("hex").slice(0, 32);
  });
  process.stdout.write(JSON.stringify(impronte));
});
