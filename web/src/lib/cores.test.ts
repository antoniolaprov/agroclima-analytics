import { describe, expect, it } from "vitest";
import { atribuir, PALETA } from "./cores";

describe("cores por UF", () => {
  it("da uma cor distinta para cada UF", () => {
    const mapa = atribuir(["MT", "PR", "RS"], {});
    expect(new Set(Object.values(mapa)).size).toBe(3);
  });

  it("nao repinta as outras quando uma UF sai", () => {
    const atribuidas = {};
    const antes = atribuir(["MT", "PR", "RS"], atribuidas);
    const depois = atribuir(["PR", "RS"], atribuidas);
    expect(depois).toEqual({ PR: antes.PR, RS: antes.RS });
  });

  it("da a cor liberada para a UF nova", () => {
    const atribuidas = {};
    const antes = atribuir(["MT", "PR", "RS"], atribuidas);
    const depois = atribuir(["PR", "RS", "GO"], atribuidas);
    expect(depois.GO).toBe(antes.MT);
  });

  it("tem oito cores", () => {
    expect(PALETA).toHaveLength(8);
    expect(new Set(PALETA).size).toBe(8);
  });
});
