import { describe, expect, it } from "vitest";
import type { LinhaClimaSafra } from "./dados";
import {
  producaoPorCodigoUf, safrasMaisSecas, siglaPorCodigoUf, ultimoAno,
} from "./destaques";
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

  it("indexa a sigla pelo mesmo codigo IBGE usado pelo mapa", () => {
    const mapa = siglaPorCodigoUf(safraExemplo);
    expect(mapa["51"]).toBe("MT");
    expect(mapa["43"]).toBe("RS");
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

  it("devolve o que tem quando ha menos linhas do que o n pedido", () => {
    const linhas: LinhaClimaSafra[] = [
      { uf: "RS", cultura: "soja", ano: 2023, rendimento: 1912, precip_ciclo: 540, temp_media_ciclo: 21.9, n_estacoes: 43 },
    ];
    const secas = safrasMaisSecas(linhas, 2);
    expect(secas.map((linha) => linha.ano)).toEqual([2023]);
  });

  it("em empate de chuva, devolve resultado estavel e do tamanho certo", () => {
    const linhas: LinhaClimaSafra[] = [
      { uf: "RS", cultura: "soja", ano: 2022, rendimento: 1800, precip_ciclo: 700, temp_media_ciclo: 21.5, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2023, rendimento: 1912, precip_ciclo: 700, temp_media_ciclo: 21.9, n_estacoes: 43 },
      { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.7, n_estacoes: 43 },
    ];
    const secas = safrasMaisSecas(linhas, 2);
    expect(secas).toHaveLength(2);
    expect(secas.map((linha) => linha.ano)).toEqual([2022, 2023]);
  });
});
