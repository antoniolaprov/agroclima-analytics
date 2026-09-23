import { describe, expect, it } from "vitest";
import { inteiro, numero } from "./formato";

describe("numero", () => {
  it("usa o formato brasileiro", () => {
    expect(inteiro(85127196)).toBe("85.127.196");
    expect(numero(3349.4)).toBe("3.349");
    expect(numero(0.8765, 2)).toBe("0,88");
    expect(numero(-1234.5, 1)).toBe("-1.234,5");
  });

  it("mostra traco quando nao ha valor", () => {
    expect(numero(null)).toBe("-");
    expect(numero(Number.NaN)).toBe("-");
    expect(inteiro(null)).toBe("-");
  });
});
