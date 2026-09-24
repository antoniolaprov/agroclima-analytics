import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NaoEncontrada from "@/app/not-found";

describe("pagina de endereco inexistente", () => {
  it("fala portugues e oferece o caminho de volta", () => {
    render(<NaoEncontrada />);
    // O 404 padrao do Next e em ingles numa pagina com lang="pt-BR".
    expect(screen.getByRole("heading", { name: "Página não encontrada" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Início" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Clima" })).toHaveAttribute("href", "/clima");
    expect(screen.getByRole("link", { name: "Safra" })).toHaveAttribute("href", "/safra");
  });
});
