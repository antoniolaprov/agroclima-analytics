import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LinhaClimaSafra } from "@/src/lib/dados";
import { climaSafraExemplo, metaExemplo, safraExemplo } from "@/src/teste/exemplos";
import { Safra } from "./Safra";

// A PAM tem decadas de historico e o clima so alguns anos; um meta onde as
// duas listas divergem e o unico jeito de pegar a regressao de abrir a pagina
// em anos_clima[0] em vez de anos_safra[0].
const metaPeriodoAmplo = {
  ...metaExemplo,
  anos_safra: [1974, 2024, 2025],
  anos_clima: [2024, 2025],
};

// Mutavel porque alguns testes precisam de outra URL; o beforeEach devolve a
// selecao de sempre para a ordem dos testes nao importar.
const QUERY_PADRAO = "ufs=MT,RS&culturas=soja&ano_ini=2024&ano_fim=2025";
let query = QUERY_PADRAO;

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(query),
  usePathname: () => "/safra",
  useRouter: () => ({ replace: vi.fn() }),
}));

describe("pagina de Safra", () => {
  beforeEach(() => {
    query = QUERY_PADRAO;
  });

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

  it("mantem a dispersao desenhada quando faltam pontos para a correlacao", () => {
    const climaSafraDoisPontos: LinhaClimaSafra[] = [
      { uf: "MT", cultura: "soja", ano: 2024, rendimento: 3109, precip_ciclo: 1066, temp_media_ciclo: 25.9, n_estacoes: 34 },
      { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.4, n_estacoes: 43 },
    ];
    const { container } = render(
      <Safra safra={safraExemplo} climaSafra={climaSafraDoisPontos} meta={metaExemplo} />,
    );
    const paragrafoCorrelacao = screen.getByText(/Correlação \(r\):/);
    expect(paragrafoCorrelacao.querySelector("strong")).toHaveTextContent("-");
    const pontos = container.querySelectorAll(".recharts-scatter-symbol");
    expect(pontos.length).toBe(climaSafraDoisPontos.length);
  });

  it("abre com o periodo inteiro da safra, nao so o do cruzamento com clima", () => {
    query = "";
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaPeriodoAmplo} />);
    const anoInicial = screen.getByLabelText("Ano inicial") as HTMLSelectElement;
    const anoFinal = screen.getByLabelText("Ano final") as HTMLSelectElement;
    expect(Number(anoInicial.value)).toBe(metaPeriodoAmplo.anos_safra[0]);
    expect(Number(anoFinal.value)).toBe(
      metaPeriodoAmplo.anos_safra[metaPeriodoAmplo.anos_safra.length - 1],
    );
  });
  it("abre no eixo que veio da URL", () => {
    query = `${QUERY_PADRAO}&eixo=temp_media_ciclo`;
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("button", { name: /Temperatura média no ciclo/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /Chuva acumulada no ciclo/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    // O rotulo do eixo X da dispersao acompanha a escolha, senao o link
    // reabriria com o botao certo e o grafico errado.
    expect(screen.getAllByText("Temperatura média no ciclo (°C)").length).toBeGreaterThan(1);
  });

  it("abre em chuva quando a URL nao diz qual eixo", () => {
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("button", { name: /Chuva acumulada no ciclo/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("ignora um eixo que nao existe e abre no padrao", () => {
    query = `${QUERY_PADRAO}&eixo=umidade`;
    render(<Safra safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("button", { name: /Chuva acumulada no ciclo/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
