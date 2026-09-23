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
  it("renderiza linha, barras e dispersao sem quebrar", () => {
    const { container: c1 } = render(<Linha dados={dados} x="competencia" series={series} />);
    expect(c1.querySelector("svg")).toBeTruthy();

    const { container: c2 } = render(<Barras dados={dados} x="competencia" series={series} />);
    expect(c2.querySelector("svg")).toBeTruthy();

    const grupos = [{ nome: "MT", cor: "#2a78d6", pontos: [{ x: 1066, y: 3109 }] }];
    const { container: c3 } = render(
      <Dispersao grupos={grupos} rotuloX="Chuva (mm)" rotuloY="Rendimento (kg/ha)" />,
    );
    expect(c3.querySelector("svg")).toBeTruthy();
  });
});
