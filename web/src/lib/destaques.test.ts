import { describe, expect, it } from "vitest";
import type { LinhaClimaSafra } from "./dados";
import { producaoPorCodigoUf, safrasMaisSecas, ultimoAno } from "./destaques";
import { safraExemplo } from "@/src/teste/exemplos";

describe("destaques da home", () => {
  it("acha o ultimo ano", () => {
    expect(ultimoAno(safraExemplo)).toBe(2025);
  });

  it("indexa a producao pelo codigo IBGE, que e o que o mapa usa", () => {
    const mapa = producaoPorCodigoUf(safraExemplo, "soja", 2025);
    expect(mapa["51"]).toBe(50175032);
    expect(mapa["43"]).toBe(13000000);
  });

  it("acha as safras mais secas do ciclo, da mais seca pra menos seca", () => {
    const rs: LinhaClimaSafra[] = [
      { uf: "RS", cultura: "soja", ano: 2023, rendimento: 1912, precip_ciclo: 540, temp_media_ciclo: 21.9, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.7, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2025, rendimento: 2012, precip_ciclo: 660, temp_media_ciclo: 22.3, n_estacoes: 40 },
    ];
    const secas = safrasMaisSecas(rs, 2);
    expect(secas.map((linha) => linha.ano)).toEqual([2023, 2025]);
  });

  it("ignora linhas sem chuva registrada no ciclo", () => {
    const linhas: LinhaClimaSafra[] = [
      { uf: "RS", cultura: "soja", ano: 2023, rendimento: 1912, precip_ciclo: null, temp_media_ciclo: 21.9, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.7, n_estacoes: 43 },
    ];
    const secas = safrasMaisSecas(linhas, 2);
    expect(secas.map((linha) => linha.ano)).toEqual([2024]);
  });
});
