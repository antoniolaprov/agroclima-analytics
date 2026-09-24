import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Filtros } from "./Filtros";

const anos = [2022, 2023, 2024, 2025, 2026];
const ufsDisponiveis = ["MT", "PR", "RS", "GO", "BA", "SP", "MG", "SC", "PA"];

function simularTelaPequena() {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  }));
}

describe("Filtros", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("em tela pequena comeca recolhido, com o resumo da selecao no botao", () => {
    simularTelaPequena();
    const filtros = { ufs: ["MT", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    render(
      <Filtros
        filtros={filtros}
        definir={vi.fn()}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    const botao = screen.getByRole("button", { name: /MT, RS/ });
    expect(botao).toHaveAttribute("aria-expanded", "false");
    expect(botao).toHaveTextContent("Soja");
    expect(screen.queryByText(/Estados \(até/)).not.toBeInTheDocument();
  });

  it("ao clicar no botao recolhido, expande e mostra os filtros", () => {
    simularTelaPequena();
    const filtros = { ufs: ["MT", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const { getByRole, getByText } = render(
      <Filtros
        filtros={filtros}
        definir={vi.fn()}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    const botao = getByRole("button", { name: /MT, RS/ });
    fireEvent.click(botao);
    expect(botao).toHaveAttribute("aria-expanded", "true");
    expect(getByText(/Estados \(até/)).toBeInTheDocument();
  });

  it("em tela grande ja comeca aberto, sem precisar clicar", () => {
    const filtros = { ufs: ["MT", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    render(
      <Filtros
        filtros={filtros}
        definir={vi.fn()}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    expect(screen.getByText(/Estados \(até/)).toBeInTheDocument();
  });


  it("desabilita UF nao selecionada quando o limite de oito e atingido", () => {
    const oito = ufsDisponiveis.slice(0, 8);
    const filtros = { ufs: oito, culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const { getByRole } = render(
      <Filtros
        filtros={filtros}
        definir={vi.fn()}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    const naoSelecionada = getByRole("button", { name: ufsDisponiveis[8] });
    const selecionada = getByRole("button", { name: oito[0] });
    expect(naoSelecionada).toBeDisabled();
    expect(selecionada).not.toBeDisabled();
  });

  it("explica no title por que a UF esta desabilitada", () => {
    const oito = ufsDisponiveis.slice(0, 8);
    const filtros = { ufs: oito, culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const { getByRole } = render(
      <Filtros
        filtros={filtros}
        definir={vi.fn()}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    const naoSelecionada = getByRole("button", { name: ufsDisponiveis[8] });
    const selecionada = getByRole("button", { name: oito[0] });
    expect(naoSelecionada).toHaveAttribute("title", expect.stringContaining("8"));
    expect(selecionada).not.toHaveAttribute("title");
  });

  it("ao escolher inicio depois do fim, leva o fim junto", () => {
    const filtros = { ufs: ["MT"], culturas: ["soja"], anoIni: 2022, anoFim: 2024 };
    const definir = vi.fn();
    const { getByLabelText } = render(
      <Filtros
        filtros={filtros}
        definir={definir}
        ufsDisponiveis={ufsDisponiveis}
        culturasDisponiveis={["soja"]}
        anos={anos}
      />,
    );
    fireEvent.change(getByLabelText("Ano inicial"), { target: { value: "2026" } });
    expect(definir).toHaveBeenCalledWith({ anoIni: 2026, anoFim: 2026 });
  });
});
