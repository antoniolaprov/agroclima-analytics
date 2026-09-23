import { describe, expect, it } from "vitest";
import { areaDoAnel, corrigirOrientacao, escalaVerde } from "./mapa";

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
});
