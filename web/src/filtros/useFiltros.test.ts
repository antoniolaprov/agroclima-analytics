import { describe, expect, it } from "vitest";
import { lerFiltros, montarQuery } from "./useFiltros";

describe("filtros na URL", () => {
  it("le a selecao dos parametros", () => {
    const filtros = lerFiltros(new URLSearchParams("ufs=MT,PR&culturas=soja&ano_ini=2023&ano_fim=2025"), {
      ufs: ["MT"], culturas: ["soja"], anoIni: 2022, anoFim: 2026,
    });
    expect(filtros).toEqual({ ufs: ["MT", "PR"], culturas: ["soja"], anoIni: 2023, anoFim: 2025 });
  });

  it("cai no padrao quando nao ha parametro", () => {
    const padrao = { ufs: ["MT", "PR", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    expect(lerFiltros(new URLSearchParams(""), padrao)).toEqual(padrao);
  });

  it("limita a selecao a oito UFs", () => {
    const padrao = { ufs: ["MT"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const muitas = "AC,AL,AP,AM,BA,CE,DF,ES,GO";
    expect(lerFiltros(new URLSearchParams(`ufs=${muitas}`), padrao).ufs).toHaveLength(8);
  });

  it("monta a query de volta", () => {
    const query = montarQuery({ ufs: ["MT", "PR"], culturas: ["soja"], anoIni: 2023, anoFim: 2025 });
    expect(query).toBe("ufs=MT%2CPR&culturas=soja&ano_ini=2023&ano_fim=2025");
  });

  it("cai no ano padrao quando o parametro nao e numero", () => {
    const padrao = { ufs: ["MT"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const filtros = lerFiltros(new URLSearchParams("ano_ini=abc&ano_fim=2025"), padrao);
    expect(filtros.anoIni).toBe(2022);
    expect(filtros.anoFim).toBe(2025);
  });

  it("mantem selecao vazia quando o parametro esta presente e vazio", () => {
    const padrao = { ufs: ["MT", "PR", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const filtros = lerFiltros(new URLSearchParams("ufs="), padrao);
    expect(filtros.ufs).toEqual([]);
  });

  it("faz o percurso de ida e volta preservando listas vazias", () => {
    const padrao = { ufs: ["MT", "PR", "RS"], culturas: ["soja"], anoIni: 2022, anoFim: 2026 };
    const original = { ufs: [], culturas: [], anoIni: 2023, anoFim: 2025 };
    const query = montarQuery(original);
    const filtros = lerFiltros(new URLSearchParams(query), padrao);
    expect(filtros).toEqual(original);
  });
});
