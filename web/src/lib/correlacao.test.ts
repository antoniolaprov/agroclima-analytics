import { describe, expect, it } from "vitest";
import { correlacao } from "./correlacao";

describe("correlacao", () => {
  it("da 1 para relacao linear crescente", () => {
    expect(correlacao([[1, 2], [2, 4], [3, 6]])).toBeCloseTo(1, 6);
  });

  it("da -1 para relacao linear decrescente", () => {
    expect(correlacao([[1, 6], [2, 4], [3, 2]])).toBeCloseTo(-1, 6);
  });

  it("devolve null com menos de tres pontos", () => {
    expect(correlacao([[1, 2], [2, 4]])).toBeNull();
  });

  it("devolve null quando um dos eixos e constante", () => {
    expect(correlacao([[1, 5], [2, 5], [3, 5]])).toBeNull();
  });
});
