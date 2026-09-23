import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
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
    expect(container.querySelectorAll("svg").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("avisa quando a selecao nao tem dados", () => {
    render(<Clima linhas={[]} meta={metaExemplo} />);
    expect(screen.getByText(/Sem dados para os filtros/)).toBeInTheDocument();
  });
});
