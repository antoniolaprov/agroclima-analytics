export function correlacao(pares: [number, number][]): number | null {
  const validos = pares.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  if (validos.length < 3) return null;

  const n = validos.length;
  const mediaX = validos.reduce((soma, [x]) => soma + x, 0) / n;
  const mediaY = validos.reduce((soma, [, y]) => soma + y, 0) / n;

  let covariancia = 0;
  let variaciaX = 0;
  let variaciaY = 0;
  for (const [x, y] of validos) {
    covariancia += (x - mediaX) * (y - mediaY);
    variaciaX += (x - mediaX) ** 2;
    variaciaY += (y - mediaY) ** 2;
  }
  if (variaciaX === 0 || variaciaY === 0) return null;
  return covariancia / Math.sqrt(variaciaX * variaciaY);
}
