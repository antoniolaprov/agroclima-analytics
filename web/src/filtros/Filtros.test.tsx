import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Filtros } from "./Filtros";

const anos = [2022, 2023, 2024, 2025, 2026];
const ufsDisponiveis = ["MT", "PR", "RS", "GO", "BA", "SP", "MG", "SC", "PA"];

describe("Filtros", () => {
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
});
