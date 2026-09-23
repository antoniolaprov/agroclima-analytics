import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Meta } from "@/src/lib/dados";
import { Rodape } from "./Rodape";

const meta: Meta = {
  gerado_em: "2026-09-22T12:00:00+00:00",
  ufs: ["MT"],
  culturas: ["soja"],
  anos: [1974, 2026],
  anos_clima: [2022, 2023, 2024, 2025, 2026],
  anos_safra: [1974, 1975, 2024, 2025],
  linhas_por_arquivo: { clima: 1, safra: 1, clima_safra: 1 },
  fontes: [{ nome: "INMET", url: "https://portal.inmet.gov.br/dadoshistoricos" }],
};

describe("Rodape", () => {
  it("mostra as faixas de clima e de safra separadamente", () => {
    render(<Rodape meta={meta} />);
    expect(screen.getByText(/2022 a 2026/)).toBeInTheDocument();
    expect(screen.getByText(/1974 a 2025/)).toBeInTheDocument();
  });

  it("nao junta as duas faixas em uma so", () => {
    render(<Rodape meta={meta} />);
    expect(screen.queryByText(/1974 a 2026/)).not.toBeInTheDocument();
  });

  it("lista as fontes", () => {
    render(<Rodape meta={meta} />);
    expect(screen.getByRole("link", { name: "INMET" })).toHaveAttribute(
      "href",
      "https://portal.inmet.gov.br/dadoshistoricos",
    );
  });
});
