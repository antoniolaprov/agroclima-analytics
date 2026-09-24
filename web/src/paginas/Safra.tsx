"use client";

import { useMemo, useRef, useState } from "react";
import { Filtros } from "@/src/filtros/Filtros";
import { useFiltros } from "@/src/filtros/useFiltros";
import { Barras } from "@/src/graficos/Barras";
import { Dispersao } from "@/src/graficos/Dispersao";
import { Linha } from "@/src/graficos/Linha";
import { atribuir } from "@/src/lib/cores";
import { correlacao } from "@/src/lib/correlacao";
import type { LinhaClimaSafra, LinhaSafra, Meta } from "@/src/lib/dados";
import { cultura as nomeCultura, inteiro, numero } from "@/src/lib/formato";

const EIXOS = {
  precip_ciclo: "Chuva acumulada no ciclo (mm)",
  temp_media_ciclo: "Temperatura média no ciclo (°C)",
} as const;

type Eixo = keyof typeof EIXOS;

function pivotarPorAno(linhas: LinhaSafra[], campo: keyof LinhaSafra) {
  const porAno = new Map<number, Record<string, string | number | null>>();
  for (const linha of linhas) {
    const registro = porAno.get(linha.ano) ?? { ano: linha.ano };
    registro[linha.uf] = linha[campo] as number | null;
    porAno.set(linha.ano, registro);
  }
  return [...porAno.values()].sort((a, b) => Number(a.ano) - Number(b.ano));
}

export function Safra({
  safra, climaSafra, meta,
}: {
  safra: LinhaSafra[];
  climaSafra: LinhaClimaSafra[];
  meta: Meta;
}) {
  const atribuidas = useRef<Record<string, string>>({});
  const [eixo, setEixo] = useState<Eixo>("precip_ciclo");
  const { filtros, definir } = useFiltros({
    ufs: ["MT", "PR", "RS"],
    // soja e a cultura com serie cheia nos tres estados padrao; abrir em
    // meta.culturas[0] (cafe, por ordem alfabetica) deixa RS e PR quase vazios.
    culturas: meta.culturas.includes("soja") ? ["soja"] : meta.culturas.slice(0, 1),
    // O cruzamento clima x safra so existe no intervalo de anos_clima, mas
    // cabe inteiro em qualquer janela que comece antes disso: abrir em
    // anos_clima[0] nao ajuda o cruzamento e corta a maior parte dos anos da
    // PAM nos graficos de producao e rendimento, que sao o assunto principal
    // da pagina.
    anoIni: meta.anos_safra[0],
    anoFim: meta.anos_safra[meta.anos_safra.length - 1],
  });

  const cultura = filtros.culturas[0];
  const selecionadas = useMemo(
    () =>
      safra.filter(
        (linha) =>
          filtros.ufs.includes(linha.uf) &&
          linha.cultura === cultura &&
          linha.ano >= filtros.anoIni &&
          linha.ano <= filtros.anoFim,
      ),
    [safra, filtros, cultura],
  );

  const cruzamento = useMemo(
    () =>
      climaSafra.filter(
        (linha) =>
          filtros.ufs.includes(linha.uf) &&
          linha.cultura === cultura &&
          linha.ano >= filtros.anoIni &&
          linha.ano <= filtros.anoFim,
      ),
    [climaSafra, filtros, cultura],
  );

  const cores = atribuir(filtros.ufs, atribuidas.current);
  const series = filtros.ufs.map((uf) => ({ chave: uf, nome: uf, cor: cores[uf] }));

  const grupos = filtros.ufs
    .map((uf) => ({
      nome: uf,
      cor: cores[uf],
      pontos: cruzamento
        .filter((linha) => linha.uf === uf && linha[eixo] !== null && linha.rendimento !== null)
        .map((linha) => ({ x: linha[eixo] as number, y: linha.rendimento as number })),
    }))
    .filter((grupo) => grupo.pontos.length > 0);

  const r = correlacao(grupos.flatMap((grupo) => grupo.pontos.map((ponto) => [ponto.x, ponto.y] as [number, number])));
  const totalPontos = grupos.reduce((soma, grupo) => soma + grupo.pontos.length, 0);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="font-serif text-4xl text-stone-900">Safra</h1>
      <div className="mt-6">
        <Filtros
          filtros={filtros}
          definir={definir}
          ufsDisponiveis={meta.ufs}
          culturasDisponiveis={meta.culturas}
          anos={meta.anos_safra}
        />
      </div>

      {selecionadas.length === 0 ? (
        <p className="mt-10 text-stone-600">Sem dados para os filtros selecionados.</p>
      ) : (
        <div className="mt-10 space-y-12">
          <section>
            <h2 className="font-serif text-2xl">Produção por ano (t)</h2>
            <Linha
              dados={pivotarPorAno(selecionadas, "producao")}
              x="ano"
              series={series}
              rotuloY="t"
              casas={0}
              larguraEixoY={88}
            />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Rendimento (kg/ha)</h2>
            <Linha dados={pivotarPorAno(selecionadas, "rendimento")} x="ano" series={series} rotuloY="kg/ha" casas={0} />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Variação anual da produção (%)</h2>
            <p className="text-sm text-stone-500">Sem barra quando falta o ano anterior para aquele estado.</p>
            <Barras dados={pivotarPorAno(selecionadas, "var_producao_aa")} x="ano" series={series} rotuloY="%" casas={1} linhaZero />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Clima e safra</h2>
            <div className="mt-2 flex gap-2 text-sm">
              {(Object.keys(EIXOS) as Eixo[]).map((opcao) => (
                <button
                  key={opcao}
                  type="button"
                  onClick={() => setEixo(opcao)}
                  aria-pressed={eixo === opcao}
                  className={`rounded-full border px-3 py-1 ${
                    eixo === opcao ? "border-stone-900 bg-stone-900 text-white" : "border-stone-300 text-stone-600"
                  }`}
                >
                  {EIXOS[opcao]}
                </button>
              ))}
            </div>
            {grupos.length === 0 ? (
              <p className="mt-6 text-stone-600">Nenhuma safra com ciclo completo nesta seleção.</p>
            ) : (
              <>
                <Dispersao grupos={grupos} rotuloX={EIXOS[eixo]} rotuloY="Rendimento (kg/ha)" />
                <p className="mt-4 text-stone-700">
                  Correlação (r): <strong>{r === null ? "-" : numero(r, 2)}</strong>
                </p>
                <p className="text-sm text-stone-500">
                  {inteiro(totalPontos)} safras de {nomeCultura(cultura).toLocaleLowerCase("pt-BR")} nos estados
                  selecionados. Cada ponto é um estado num ano; com poucos anos por estado, a correlação descreve a
                  amostra e não prova causa. Os estados entram num único conjunto de pontos, então boa parte de um r
                  alto pode vir da diferença entre estados, e não da variação dentro de cada um.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
