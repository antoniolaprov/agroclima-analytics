import { describe, expect, it } from "vitest";
import { carregarClima, carregarClimaSafra, carregarMeta, carregarSafra } from "./dados";

describe("carregamento dos extratos", () => {
  it("le clima com as colunas do contrato", () => {
    const linhas = carregarClima();
    expect(linhas.length).toBeGreaterThan(0);
    expect(Object.keys(linhas[0]).sort()).toEqual(
      ["ano", "anomalia_temp", "dias_sem_chuva", "mes", "n_estacoes", "precipitacao", "temp_media", "temp_media_movel_3m", "uf"],
    );
  });

  it("le safra e clima_safra", () => {
    const safra = carregarSafra();
    expect(safra.length).toBeGreaterThan(0);
    expect(safra[0].uf_codigo).toMatch(/^\d{2}$/);
    expect(carregarClimaSafra().length).toBeGreaterThan(0);
  });

  it("le o meta com a data de geracao", () => {
    const meta = carregarMeta();
    expect(meta.gerado_em).toMatch(/^\d{4}-\d{2}-\d{2}/);
    expect(meta.ufs.length).toBe(27);
    expect(meta.culturas).toContain("soja");
  });

  it("le os tres recortes de anos do meta", () => {
    const meta = carregarMeta();
    expect(meta.anos_clima[0]).toBe(2022);
    expect(meta.anos_safra[0]).toBe(1974);
    expect(meta.anos_clima.length).toBeLessThan(meta.anos_safra.length);
  });
});
