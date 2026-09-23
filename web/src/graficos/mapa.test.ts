import { readFileSync } from "node:fs";
import { join } from "node:path";
import { geoMercator, geoPath } from "d3-geo";
import { describe, expect, it } from "vitest";
import { VERDE_MAPA } from "@/src/lib/cores";
import { areaDoAnel, corrigirOrientacao, escalaVerde, type MalhaUF } from "./mapa";

// Quadrado no sentido anti-horario, como o IBGE entrega (RFC 7946).
const quadradoAntiHorario: [number, number][] = [
  [0, 0], [1, 0], [1, 1], [0, 1], [0, 0],
];

describe("orientacao dos aneis", () => {
  it("mede o sentido pelo sinal da area", () => {
    expect(areaDoAnel(quadradoAntiHorario)).toBeGreaterThan(0);
  });

  it("inverte para o sentido que o d3-geo espera", () => {
    // Sem inverter, o d3-geo le o anel como "o globo menos este poligono" e
    // pinta o mapa inteiro.
    const malha = {
      type: "FeatureCollection" as const,
      features: [
        {
          type: "Feature" as const,
          properties: { codarea: "51" },
          geometry: { type: "Polygon" as const, coordinates: [quadradoAntiHorario] },
        },
      ],
    };
    const corrigida = corrigirOrientacao(malha);
    const anel = corrigida.features[0].geometry.coordinates[0] as [number, number][];
    expect(areaDoAnel(anel)).toBeLessThan(0);
  });

  it("e pura: aplicar duas vezes na mesma malha da o mesmo resultado que aplicar uma vez", () => {
    const malha = {
      type: "FeatureCollection" as const,
      features: [
        {
          type: "Feature" as const,
          properties: { codarea: "51" },
          geometry: { type: "Polygon" as const, coordinates: [quadradoAntiHorario] },
        },
      ],
    };
    // Duas chamadas independentes sobre a mesma malha (como duas montagens de
    // um componente lendo de um cache compartilhado), nao uma encadeada na
    // saida da outra.
    const primeira = corrigirOrientacao(malha);
    const segunda = corrigirOrientacao(malha);
    const anelPrimeira = primeira.features[0].geometry.coordinates[0] as [number, number][];
    const anelSegunda = segunda.features[0].geometry.coordinates[0] as [number, number][];
    expect(areaDoAnel(anelPrimeira)).toBeLessThan(0);
    expect(areaDoAnel(anelSegunda)).toBeLessThan(0);

    // O argumento original nao foi mutado por nenhuma das duas chamadas.
    expect(areaDoAnel(malha.features[0].geometry.coordinates[0] as [number, number][])).toBeGreaterThan(0);
    expect(malha.features[0].geometry.coordinates[0]).toEqual(quadradoAntiHorario);
  });
});

describe("escala de cor", () => {
  it("vai do claro ao escuro conforme o valor", () => {
    const baixo = escalaVerde(10, 100);
    const alto = escalaVerde(100, 100);
    expect(baixo).not.toBe(alto);
  });

  it("usa cinza quando nao ha valor", () => {
    expect(escalaVerde(null, 100)).toBe("#e7e5e4");
  });

  it("nao pinta de cinza um zero verdadeiro quando o maximo da selecao e zero", () => {
    expect(escalaVerde(0, 0)).not.toBe("#e7e5e4");
    expect(escalaVerde(0, 0)).toBe(VERDE_MAPA[0]);
  });

  it("trava a razao por baixo para valores negativos", () => {
    expect(escalaVerde(-10, 100)).toBe(escalaVerde(0, 100));
  });

  it("trava a razao por cima para valores acima do maximo", () => {
    expect(escalaVerde(150, 100)).toBe(escalaVerde(100, 100));
  });
});

describe("malha real do IBGE (public/data/uf_br.geojson)", () => {
  const caminho = join(process.cwd(), "public/data/uf_br.geojson");
  const bruta = JSON.parse(readFileSync(caminho, "utf-8")) as MalhaUF;
  const malha = corrigirOrientacao(bruta);

  it("tem as 27 feicoes das unidades da federacao", () => {
    expect(malha.features).toHaveLength(27);
  });

  it("tem codarea distinto em cada feicao", () => {
    const codigos = malha.features.map((feicao) => feicao.properties.codarea);
    expect(new Set(codigos).size).toBe(27);
  });

  it("projeta 27 caminhos nao vazios, distintos e nao degenerados", () => {
    const projecao = geoMercator().fitSize([640, 640], malha as never);
    const desenho = geoPath(projecao);
    const caminhos = malha.features.map((feicao) => desenho(feicao as never) ?? "");

    expect(caminhos).toHaveLength(27);
    for (const d of caminhos) {
      expect(d).not.toBe("");
      // Um retangulo degenerado tem poucos comandos SVG; um contorno estadual
      // de verdade tem muitos.
      const comandos = d.match(/[MLZ]/g) ?? [];
      expect(comandos.length).toBeGreaterThan(4);
    }
    expect(new Set(caminhos).size).toBe(27);
  });

  it("o anel externo da primeira feicao tem area negativa apos a correcao", () => {
    const geometria = malha.features[0].geometry;
    const anel = (
      geometria.type === "Polygon" ? geometria.coordinates[0] : geometria.coordinates[0][0]
    ) as [number, number][];
    expect(areaDoAnel(anel)).toBeLessThan(0);
  });
});
