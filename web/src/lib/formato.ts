export function numero(valor: number | null | undefined, casas = 0): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return "-";
  return valor.toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
}

export function inteiro(valor: number | null | undefined): string {
  return numero(valor, 0);
}

// Numeros pequenos no meio de uma frase leem melhor por extenso; acima de 10
// (ou fora da faixa coberta) cai no algarismo de inteiro.
const NOMES_NUMERO: Record<number, string> = {
  1: "um",
  2: "dois",
  3: "três",
  4: "quatro",
  5: "cinco",
  6: "seis",
  7: "sete",
  8: "oito",
  9: "nove",
  10: "dez",
};

export function porExtenso(valor: number): string {
  return NOMES_NUMERO[valor] ?? inteiro(valor);
}

// O pipeline normaliza os nomes das culturas sem acento; a interface mostra o
// nome como se escreve.
const NOMES_CULTURA: Record<string, string> = {
  cafe: "Café",
  cana: "Cana-de-açúcar",
  milho: "Milho",
  soja: "Soja",
};

export function cultura(chave: string): string {
  return NOMES_CULTURA[chave] ?? chave;
}
