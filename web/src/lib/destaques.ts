import type { LinhaClimaSafra, LinhaSafra } from "./dados";

export function ultimoAno(linhas: { ano: number }[]): number {
  return linhas.reduce((maior, linha) => Math.max(maior, linha.ano), 0);
}

export function producaoPorCodigoUf(
  safra: LinhaSafra[],
  cultura: string,
  ano: number,
): Record<string, number> {
  const mapa: Record<string, number> = {};
  for (const linha of safra) {
    if (linha.cultura === cultura && linha.ano === ano && linha.producao !== null) {
      mapa[linha.uf_codigo] = linha.producao;
    }
  }
  return mapa;
}

// Ordena pela chuva acumulada no ciclo, da safra mais seca pra mais chuvosa,
// e devolve as n primeiras; linhas sem chuva registrada ficam de fora.
export function safrasMaisSecas(linhas: LinhaClimaSafra[], n: number): LinhaClimaSafra[] {
  return [...linhas]
    .filter((linha) => linha.precip_ciclo !== null)
    .sort((a, b) => (a.precip_ciclo as number) - (b.precip_ciclo as number))
    .slice(0, n);
}
