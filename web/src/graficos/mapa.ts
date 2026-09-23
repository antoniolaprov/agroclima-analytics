import { interpolateRgb } from "d3-interpolate";
import { VERDE_MAPA } from "@/src/lib/cores";

export type Poligono = [number, number][][];

export type FeicaoUF = {
  type: "Feature";
  properties: { codarea: string };
  geometry:
    | { type: "Polygon"; coordinates: Poligono }
    | { type: "MultiPolygon"; coordinates: Poligono[] };
};

export type MalhaUF = { type: "FeatureCollection"; features: FeicaoUF[] };

export const SEM_DADO = "#e7e5e4";

export function areaDoAnel(anel: [number, number][]): number {
  let soma = 0;
  for (let i = 0; i < anel.length - 1; i += 1) {
    const [x1, y1] = anel[i];
    const [x2, y2] = anel[i + 1];
    soma += x1 * y2 - x2 * y1;
  }
  return soma / 2;
}

export function corrigirOrientacao(malha: MalhaUF): MalhaUF {
  // O IBGE segue a RFC 7946 (anel externo anti-horario); o d3-geo espera o
  // sentido oposto e, sem inverter, pinta o mapa inteiro.
  for (const feicao of malha.features) {
    const poligonos =
      feicao.geometry.type === "Polygon"
        ? [feicao.geometry.coordinates]
        : feicao.geometry.coordinates;
    for (const poligono of poligonos) {
      for (const anel of poligono) anel.reverse();
    }
  }
  return malha;
}

const gradiente = interpolateRgb(VERDE_MAPA[0], VERDE_MAPA[1]);

export function escalaVerde(valor: number | null, maximo: number): string {
  if (valor === null || !Number.isFinite(valor) || maximo <= 0) return SEM_DADO;
  return gradiente(Math.min(valor / maximo, 1));
}
