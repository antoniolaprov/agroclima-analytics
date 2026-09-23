import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Cabecalho } from "./Cabecalho";

describe("Cabecalho", () => {
  it("leva as tres paginas", () => {
    render(<Cabecalho />);
    expect(screen.getByRole("link", { name: "Início" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Clima" })).toHaveAttribute("href", "/clima");
    expect(screen.getByRole("link", { name: "Safra" })).toHaveAttribute("href", "/safra");
  });
});
