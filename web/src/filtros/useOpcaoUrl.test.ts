import { describe, expect, it } from "vitest";
import { lerOpcao, montarQueryOpcao } from "./useOpcaoUrl";

const EIXOS = ["precip_ciclo", "temp_media_ciclo"] as const;

describe("opcao de visualizacao na URL", () => {
  it("le a opcao do parametro", () => {
    const parametros = new URLSearchParams("eixo=temp_media_ciclo");
    expect(lerOpcao(parametros, "eixo", EIXOS, "precip_ciclo")).toBe("temp_media_ciclo");
  });

  it("cai no padrao quando nao ha parametro", () => {
    expect(lerOpcao(new URLSearchParams(""), "eixo", EIXOS, "precip_ciclo")).toBe("precip_ciclo");
  });

  it("cai no padrao quando a opcao nao existe", () => {
    // Link antigo ou URL editada a mao: melhor abrir no padrao do que
    // procurar uma coluna que a tabela nao tem.
    const parametros = new URLSearchParams("eixo=umidade");
    expect(lerOpcao(parametros, "eixo", EIXOS, "precip_ciclo")).toBe("precip_ciclo");
  });

  it("escreve a opcao sem apagar os filtros que ja estao na URL", () => {
    const parametros = new URLSearchParams("ufs=MT%2CPR&culturas=soja&ano_ini=1974&ano_fim=2025");
    const query = montarQueryOpcao(parametros, "eixo", "temp_media_ciclo");
    const depois = new URLSearchParams(query);
    expect(depois.get("ufs")).toBe("MT,PR");
    expect(depois.get("culturas")).toBe("soja");
    expect(depois.get("ano_ini")).toBe("1974");
    expect(depois.get("ano_fim")).toBe("2025");
    expect(depois.get("eixo")).toBe("temp_media_ciclo");
  });

  it("troca a opcao ja escrita em vez de acrescentar outra", () => {
    const parametros = new URLSearchParams("eixo=precip_ciclo");
    const query = montarQueryOpcao(parametros, "eixo", "temp_media_ciclo");
    expect(new URLSearchParams(query).getAll("eixo")).toEqual(["temp_media_ciclo"]);
  });
});
