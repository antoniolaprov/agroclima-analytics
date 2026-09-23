import { describe, expect, it } from "vitest";
import { atribuir, PALETA, VERDE_MAPA } from "./cores";

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

  it("e idempotente para o mesmo conjunto de UFs", () => {
    const atribuidas = {};
    const primeira = atribuir(["MT", "PR", "RS"], atribuidas);
    const segunda = atribuir(["MT", "PR", "RS"], atribuidas);
    expect(segunda).toEqual(primeira);
  });

  it("nao muda as cores ja atribuidas quando a ordem das UFs muda", () => {
    const atribuidas = {};
    const antes = atribuir(["MT", "PR", "RS"], atribuidas);
    const depois = atribuir(["RS", "MT", "PR"], atribuidas);
    expect(depois.MT).toBe(antes.MT);
    expect(depois.PR).toBe(antes.PR);
    expect(depois.RS).toBe(antes.RS);
  });
});

describe("verde do mapa", () => {
  it("usa os extremos da escala Greens do ColorBrewer", () => {
    expect(VERDE_MAPA[0]).toBe("#f7fcf5");
    expect(VERDE_MAPA[1]).toBe("#00441b");
    expect(VERDE_MAPA[0]).not.toBe(VERDE_MAPA[1]);
  });
});
