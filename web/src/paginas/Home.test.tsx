import fs from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { MalhaUF } from "@/src/graficos/mapa";
import type { LinhaClimaSafra } from "@/src/lib/dados";
import { climaSafraExemplo, metaExemplo, safraExemplo } from "@/src/teste/exemplos";
import { Home } from "./Home";

// O MapaUF busca a malha por fetch num efeito; em jsdom nao ha servidor, entao
// cada teste recebe um fetch falso que devolve a malha real lida do disco.
const malha: MalhaUF = JSON.parse(
  fs.readFileSync(path.join(process.cwd(), "public", "data", "uf_br.geojson"), "utf-8"),
);

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ json: () => Promise.resolve(malha) }),
  );
});

describe("home", () => {
  it("tem os blocos da narrativa", async () => {
    render(<Home safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/O Brasil que planta/)).toBeInTheDocument();
    expect(screen.getByText(/Quando falta chuva/)).toBeInTheDocument();
    expect(screen.getByText(/não é só chuva/i)).toBeInTheDocument();
    expect(screen.getByText(/Como isso é feito/)).toBeInTheDocument();
    await screen.findByRole("img");
  });

  it("nao afirma queda quando a relacao e mais forte no pais do que na selecao", async () => {
    // MT e PR (da selecao padrao) com relacao fraca; os demais estados com
    // relacao forte. A frase precisa acompanhar o dado, nao repetir o caso da
    // soja, onde a correlacao desaba fora da selecao.
    const cruzamento: LinhaClimaSafra[] = [
      { uf: "MT", cultura: "soja", ano: 2022, rendimento: 3000, precip_ciclo: 800, temp_media_ciclo: 25, n_estacoes: 3 },
      { uf: "MT", cultura: "soja", ano: 2023, rendimento: 2990, precip_ciclo: 1200, temp_media_ciclo: 25, n_estacoes: 3 },
      { uf: "PR", cultura: "soja", ano: 2022, rendimento: 3010, precip_ciclo: 900, temp_media_ciclo: 22, n_estacoes: 3 },
      { uf: "PR", cultura: "soja", ano: 2023, rendimento: 3005, precip_ciclo: 1100, temp_media_ciclo: 22, n_estacoes: 3 },
      { uf: "GO", cultura: "soja", ano: 2022, rendimento: 1000, precip_ciclo: 400, temp_media_ciclo: 24, n_estacoes: 3 },
      { uf: "GO", cultura: "soja", ano: 2023, rendimento: 2000, precip_ciclo: 800, temp_media_ciclo: 24, n_estacoes: 3 },
      { uf: "BA", cultura: "soja", ano: 2022, rendimento: 3000, precip_ciclo: 1200, temp_media_ciclo: 26, n_estacoes: 3 },
      { uf: "BA", cultura: "soja", ano: 2023, rendimento: 4000, precip_ciclo: 1600, temp_media_ciclo: 26, n_estacoes: 3 },
    ];
    render(<Home safra={safraExemplo} climaSafra={cruzamento} meta={metaExemplo} />);
    expect(screen.getByText(/não enfraquece fora da seleção/)).toBeInTheDocument();
    await screen.findByRole("img");
  });

  it("afirma queda quando a relacao da selecao e a mais forte", async () => {
    const cruzamento: LinhaClimaSafra[] = [
      { uf: "MT", cultura: "soja", ano: 2022, rendimento: 1000, precip_ciclo: 400, temp_media_ciclo: 25, n_estacoes: 3 },
      { uf: "MT", cultura: "soja", ano: 2023, rendimento: 2000, precip_ciclo: 800, temp_media_ciclo: 25, n_estacoes: 3 },
      { uf: "PR", cultura: "soja", ano: 2022, rendimento: 3000, precip_ciclo: 1200, temp_media_ciclo: 22, n_estacoes: 3 },
      { uf: "PR", cultura: "soja", ano: 2023, rendimento: 4000, precip_ciclo: 1600, temp_media_ciclo: 22, n_estacoes: 3 },
      { uf: "GO", cultura: "soja", ano: 2022, rendimento: 4000, precip_ciclo: 400, temp_media_ciclo: 24, n_estacoes: 3 },
      { uf: "GO", cultura: "soja", ano: 2023, rendimento: 1000, precip_ciclo: 1600, temp_media_ciclo: 24, n_estacoes: 3 },
    ];
    render(<Home safra={safraExemplo} climaSafra={cruzamento} meta={metaExemplo} />);
    expect(screen.getByText(/relação enfraquece fora da seleção/)).toBeInTheDocument();
    await screen.findByRole("img");
  });

  it("mostra a correlacao do pais inteiro junto com a da selecao", async () => {
    render(<Home safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    // "Todos os estados" tambem aparece na legenda do grafico; a frase busca o
    // texto completo pra nao colidir com o rotulo do grupo.
    expect(screen.getByText(/todos os estados que plantam/i)).toBeInTheDocument();
    await screen.findByRole("img");
  });

  it("desenha as 27 UFs no mapa sem pintar tudo de uma cor so", async () => {
    render(<Home safra={safraExemplo} climaSafra={climaSafraExemplo} meta={metaExemplo} />);
    const mapa = await screen.findByRole("img");
    const caminhos = mapa.querySelectorAll("path");
    expect(caminhos.length).toBe(27);
    caminhos.forEach((caminho) => expect(caminho.getAttribute("d")).toBeTruthy());
    const cores = new Set([...caminhos].map((caminho) => caminho.getAttribute("fill")));
    expect(cores.size).toBeGreaterThan(1);
  });

  it("no bloco do RS, destaca as safras mais secas separadas do resto", async () => {
    // Mesmos tres pontos do caso real (docs/design-web.md, bloco 3): 2023 e
    // 2025 sao os ciclos secos: 540mm e 660mm, contra 1150mm de 2024.
    const climaSafraRs: LinhaClimaSafra[] = [
      { uf: "RS", cultura: "soja", ano: 2023, rendimento: 1912, precip_ciclo: 540, temp_media_ciclo: 21.9, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.7, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2025, rendimento: 2012, precip_ciclo: 660, temp_media_ciclo: 22.3, n_estacoes: 40 },
    ];
    render(<Home safra={safraExemplo} climaSafra={climaSafraRs} meta={metaExemplo} />);
    await screen.findByRole("img");

    expect(screen.getByText(/três safras/)).toBeInTheDocument();

    const secaoRs = screen.getByText(/Quando falta chuva/).closest("section");
    expect(secaoRs).not.toBeNull();
    const pontos = secaoRs!.querySelectorAll(".recharts-scatter-symbol");
    expect(pontos.length).toBe(3);
    // A cor de preenchimento fica no <path class="recharts-symbols"> interno,
    // nao no <g class="recharts-scatter-symbol"> que o envolve; a legenda usa
    // a mesma classe pro icone, entao o seletor exige o ponto de verdade como
    // ancestral pra nao contar o icone da legenda junto.
    const secos = secaoRs!.querySelectorAll('.recharts-scatter-symbol .recharts-symbols[fill="#e34948"]');
    const restantes = secaoRs!.querySelectorAll('.recharts-scatter-symbol .recharts-symbols[fill="#a8a29e"]');
    expect(secos.length).toBe(2);
    expect(restantes.length).toBe(1);
  });

  it("no bloco da correlacao, nao nomeia um estado da selecao sem cruzamento para a cultura", async () => {
    // PR nao tem nenhuma linha para "cafe" nesta amostra; so MT e RS
    // contribuem pontos, entao so eles podem aparecer na frase da selecao.
    const climaSafraSemPr: LinhaClimaSafra[] = [
      { uf: "MT", cultura: "cafe", ano: 2023, rendimento: 1800, precip_ciclo: 900, temp_media_ciclo: 22.1, n_estacoes: 20 },
      { uf: "MT", cultura: "cafe", ano: 2024, rendimento: 1900, precip_ciclo: 950, temp_media_ciclo: 22.4, n_estacoes: 20 },
      { uf: "MT", cultura: "cafe", ano: 2025, rendimento: 2000, precip_ciclo: 1000, temp_media_ciclo: 22.0, n_estacoes: 20 },
      { uf: "RS", cultura: "cafe", ano: 2023, rendimento: 1500, precip_ciclo: 800, temp_media_ciclo: 18.5, n_estacoes: 15 },
      { uf: "RS", cultura: "cafe", ano: 2024, rendimento: 1600, precip_ciclo: 850, temp_media_ciclo: 18.9, n_estacoes: 15 },
      { uf: "RS", cultura: "cafe", ano: 2025, rendimento: 1700, precip_ciclo: 900, temp_media_ciclo: 18.2, n_estacoes: 15 },
    ];
    render(
      <Home
        safra={safraExemplo}
        climaSafra={climaSafraSemPr}
        meta={{ ...metaExemplo, culturas: ["cafe"] }}
      />,
    );
    await screen.findByRole("img");

    const secaoCorrelacao = screen.getByText(/não é só chuva/i).closest("section");
    expect(secaoCorrelacao).not.toBeNull();
    expect(secaoCorrelacao).toHaveTextContent(/Com MT e RS,/);
    expect(secaoCorrelacao!.textContent).not.toMatch(/\bPR\b/);
  });
});
