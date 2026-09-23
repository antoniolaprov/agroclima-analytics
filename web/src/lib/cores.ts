// Mesma paleta do dashboard Streamlit (dashboard/cores.py), validada para
// daltonismo nesta ordem. Um estado tem a mesma cor nos dois dashboards.
export const PALETA = [
  "#2a78d6",
  "#eb6834",
  "#1baf7a",
  "#eda100",
  "#e87ba4",
  "#008300",
  "#4a3aa7",
  "#e34948",
];

export const VERDE_MAPA: [string, string] = ["#eaf4ea", "#14532d"];

export function atribuir(
  ufs: string[],
  atribuidas: Record<string, string>,
): Record<string, string> {
  // A cor acompanha a UF, nao a posicao dela na selecao: tirar uma UF do filtro
  // nao repinta as demais.
  for (const uf of Object.keys(atribuidas)) {
    if (!ufs.includes(uf)) delete atribuidas[uf];
  }
  const usadas = new Set(Object.values(atribuidas));
  const livres = PALETA.filter((cor) => !usadas.has(cor));
  for (const uf of ufs) {
    if (!atribuidas[uf]) {
      const cor = livres.shift();
      if (cor) atribuidas[uf] = cor;
    }
  }
  return Object.fromEntries(ufs.filter((uf) => atribuidas[uf]).map((uf) => [uf, atribuidas[uf]]));
}
