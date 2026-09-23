import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { climaSafraExemplo, metaExemplo, safraExemplo } from "@/src/teste/exemplos";
import { Safra } from "./Safra";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("ufs=MT,RS&culturas=soja&ano_ini=2024&ano_fim=2025"),
  usePathname: () => "/safra",
  useRouter: () => ({ replace: vi.fn() }),
}));

describe("pagina de Safra", () => {
  it("mostra producao, rendimento, variacao e o cruzamento", () => {
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("heading", { name: /Safra/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Produção por ano/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Rendimento/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Variação anual/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Clima e safra/ })).toBeInTheDocument();
  });

  it("desenha as curvas de producao e de rendimento, uma por UF selecionada", () => {
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    const secaoProducao = screen.getByRole("heading", { name: /Produção por ano/ }).closest("section");
    const secaoRendimento = screen.getByRole("heading", { name: /Rendimento/ }).closest("section");
    expect(secaoProducao).not.toBeNull();
    expect(secaoRendimento).not.toBeNull();

    const curvasProducao = secaoProducao!.querySelectorAll("path.recharts-line-curve");
    expect(curvasProducao.length).toBe(2);
    curvasProducao.forEach((curva) => expect(curva.getAttribute("d")).toBeTruthy());

    const curvasRendimento = secaoRendimento!.querySelectorAll("path.recharts-line-curve");
    expect(curvasRendimento.length).toBe(2);
    curvasRendimento.forEach((curva) => expect(curva.getAttribute("d")).toBeTruthy());
  });

  it("desenha exatamente duas barras de variacao anual, sem barra para o ano sem historico anterior", () => {
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    const secaoVariacao = screen.getByRole("heading", { name: /Variação anual/ }).closest("section");
    expect(secaoVariacao).not.toBeNull();
    // safraExemplo tem var_producao_aa nulo em 2024 para as duas UFs; so 2025
    // tem valor para as duas, entao o grafico deve ter exatamente duas barras.
    const retangulos = secaoVariacao!.querySelectorAll("path.recharts-rectangle");
    expect(retangulos.length).toBe(2);
  });

  it("desenha um ponto por safra do cruzamento clima x safra", () => {
    const { container } = render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    const pontos = container.querySelectorAll(".recharts-scatter-symbol");
    expect(pontos.length).toBe(climaSafraExemplo.length);
  });

  it("mostra a correlacao com o tamanho da amostra", () => {
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByText(/4 safras/)).toBeInTheDocument();
  });
});
