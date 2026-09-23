import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { LinhaClima } from "@/src/lib/dados";
import { climaExemplo, metaExemplo } from "@/src/teste/exemplos";
import { Clima } from "./Clima";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("ufs=MT,RS&ano_ini=2024&ano_fim=2024"),
  usePathname: () => "/clima",
  useRouter: () => ({ replace: vi.fn() }),
}));

describe("pagina de Clima", () => {
  it("desenha os tres graficos e a tabela", () => {
    const { container } = render(<Clima linhas={climaExemplo} meta={metaExemplo} />);
    expect(screen.getByRole("heading", { name: /Clima/ })).toBeInTheDocument();
    expect(screen.getByText(/Temperatura média/)).toBeInTheDocument();
    expect(screen.getByText(/Precipitação mensal/)).toBeInTheDocument();
    expect(screen.getByText(/Anomalia de temperatura/)).toBeInTheDocument();
    // climaExemplo tem MT e RS (duas UFs selecionadas) e a pagina desenha tres
    // graficos: grade e eixos aparecem mesmo sem dado, entao contar <svg> nao
    // prova que a curva existe. Conta as curvas de verdade e exige "d" preenchido.
    const curvas = container.querySelectorAll("path.recharts-line-curve");
    expect(curvas.length).toBe(6);
    curvas.forEach((curva) => {
      expect(curva.getAttribute("d")).toBeTruthy();
    });
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("avisa quando a selecao nao tem dados", () => {
    render(<Clima linhas={[]} meta={metaExemplo} />);
    expect(screen.getByText(/Sem dados para os filtros/)).toBeInTheDocument();
  });

  it("buraco de chuva no meio da serie parte a curva em vez de emendar", () => {
    // MT sem chuva em fevereiro (mes do meio); RS com a serie completa para
    // servir de controle. Dado montado aqui, nao em src/teste/exemplos.ts.
    const linhas: LinhaClima[] = [
      { uf: "MT", ano: 2024, mes: 1, temp_media: 26.4, temp_media_movel_3m: 26.1, precipitacao: 263, anomalia_temp: 0.9, dias_sem_chuva: 0, n_estacoes: 34 },
      { uf: "MT", ano: 2024, mes: 2, temp_media: 26.0, temp_media_movel_3m: 26.2, precipitacao: null, anomalia_temp: 0.4, dias_sem_chuva: 1, n_estacoes: 34 },
      { uf: "MT", ano: 2024, mes: 3, temp_media: 25.8, temp_media_movel_3m: 26.0, precipitacao: 210, anomalia_temp: 0.3, dias_sem_chuva: 2, n_estacoes: 34 },
      { uf: "RS", ano: 2024, mes: 1, temp_media: 24.8, temp_media_movel_3m: 24.5, precipitacao: 138, anomalia_temp: -0.3, dias_sem_chuva: 10, n_estacoes: 43 },
      { uf: "RS", ano: 2024, mes: 2, temp_media: 24.1, temp_media_movel_3m: 24.4, precipitacao: 150, anomalia_temp: 0.2, dias_sem_chuva: 8, n_estacoes: 43 },
      { uf: "RS", ano: 2024, mes: 3, temp_media: 24.3, temp_media_movel_3m: 24.3, precipitacao: 160, anomalia_temp: 0.1, dias_sem_chuva: 6, n_estacoes: 43 },
    ];
    render(<Clima linhas={linhas} meta={metaExemplo} />);
    const secaoChuva = screen.getByText(/Precipitação mensal/).closest("section");
    expect(secaoChuva).not.toBeNull();
    // MT e a primeira UF em filtros.ufs (vem de "ufs=MT,RS" na URL), entao
    // recebe a primeira cor da paleta.
    const curvaMt = secaoChuva!.querySelector('path.recharts-line-curve[stroke="#2a78d6"]');
    expect(curvaMt).not.toBeNull();
    const d = curvaMt!.getAttribute("d") ?? "";
    const comandosDeMovimento = d.match(/M/g) ?? [];
    expect(comandosDeMovimento.length).toBeGreaterThan(1);

    // RS nao tem buraco: a curva de controle fica inteira, um unico comando de movimento.
    const curvaRs = secaoChuva!.querySelector('path.recharts-line-curve[stroke="#eb6834"]');
    expect(curvaRs).not.toBeNull();
    const dRs = curvaRs!.getAttribute("d") ?? "";
    expect((dRs.match(/M/g) ?? []).length).toBe(1);
  });
});
