import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Barras } from "./Barras";
import { Dispersao } from "./Dispersao";
import { Linha } from "./Linha";

const dados = [
  { competencia: "2024-01", MT: 26.4, RS: 24.8 },
  { competencia: "2024-02", MT: 26.0, RS: 24.1 },
];
const series = [
  { chave: "MT", nome: "MT", cor: "#2a78d6" },
  { chave: "RS", nome: "RS", cor: "#eb6834" },
];

describe("graficos", () => {
  it("Linha desenha uma curva por serie, com geometria de verdade", () => {
    const { container } = render(<Linha dados={dados} x="competencia" series={series} />);
    const curvas = container.querySelectorAll("path.recharts-line-curve");
    expect(curvas.length).toBe(series.length);
    curvas.forEach((curva) => {
      expect(curva.getAttribute("d")).toBeTruthy();
    });
  });

  it("Linha nao desenha nada sem dados", () => {
    const { container } = render(<Linha dados={[]} x="competencia" series={series} />);
    expect(container.querySelectorAll("path.recharts-line-curve").length).toBe(0);
  });

  it("Barras desenha um retangulo por linha de dado e por serie", () => {
    const { container } = render(<Barras dados={dados} x="competencia" series={series} />);
    const retangulos = container.querySelectorAll("path.recharts-rectangle");
    expect(retangulos.length).toBe(dados.length * series.length);
  });

  it("Barras nao desenha nada sem dados", () => {
    const { container } = render(<Barras dados={[]} x="competencia" series={series} />);
    expect(container.querySelectorAll("path.recharts-rectangle").length).toBe(0);
  });

  it("Dispersao desenha um ponto por par x/y recebido", () => {
    const grupos = [
      { nome: "MT", cor: "#2a78d6", pontos: [{ x: 1066, y: 3109 }, { x: 1200, y: 3300 }] },
      { nome: "RS", cor: "#eb6834", pontos: [{ x: 900, y: 2800 }] },
    ];
    const totalPontos = grupos.reduce((soma, grupo) => soma + grupo.pontos.length, 0);
    const { container } = render(
      <Dispersao grupos={grupos} rotuloX="Chuva (mm)" rotuloY="Rendimento (kg/ha)" />,
    );
    expect(container.querySelectorAll(".recharts-scatter-symbol").length).toBe(totalPontos);
  });

  it("Dispersao nao desenha nada sem pontos", () => {
    const grupos = [{ nome: "MT", cor: "#2a78d6", pontos: [] }];
    const { container } = render(
      <Dispersao grupos={grupos} rotuloX="Chuva (mm)" rotuloY="Rendimento (kg/ha)" />,
    );
    expect(container.querySelectorAll(".recharts-scatter-symbol").length).toBe(0);
  });
});
