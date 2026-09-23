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
