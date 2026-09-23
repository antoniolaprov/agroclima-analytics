import { describe, expect, it } from "vitest";
import { inteiro, numero, porExtenso } from "./formato";

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

describe("porExtenso", () => {
  it("escreve de um a dez por extenso", () => {
    expect(porExtenso(1)).toBe("um");
    expect(porExtenso(2)).toBe("dois");
    expect(porExtenso(3)).toBe("três");
    expect(porExtenso(10)).toBe("dez");
  });

  it("cai no algarismo acima de dez", () => {
    expect(porExtenso(11)).toBe("11");
    expect(porExtenso(24)).toBe("24");
  });
});
