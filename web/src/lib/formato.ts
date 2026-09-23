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
