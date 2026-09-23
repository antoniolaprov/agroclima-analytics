"use client";

import { useMemo, useRef } from "react";
import { Filtros } from "@/src/filtros/Filtros";
import { useFiltros } from "@/src/filtros/useFiltros";
import { Linha } from "@/src/graficos/Linha";
import { atribuir } from "@/src/lib/cores";
import type { LinhaClima, Meta } from "@/src/lib/dados";
import { numero } from "@/src/lib/formato";

const CHAVE_MES = (linha: LinhaClima) => `${linha.ano}-${String(linha.mes).padStart(2, "0")}`;

function pivotar(linhas: LinhaClima[], campo: keyof LinhaClima) {
  const porMes = new Map<string, Record<string, string | number | null>>();
  for (const linha of linhas) {
    const chave = CHAVE_MES(linha);
    const registro = porMes.get(chave) ?? { competencia: chave };
    registro[linha.uf] = linha[campo] as number | null;
    porMes.set(chave, registro);
  }
  return [...porMes.values()].sort((a, b) => String(a.competencia).localeCompare(String(b.competencia)));
}

export function Clima({ linhas, meta }: { linhas: LinhaClima[]; meta: Meta }) {
  const atribuidas = useRef<Record<string, string>>({});
  const { filtros, definir } = useFiltros({
    ufs: ["MT", "PR", "RS"],
    culturas: meta.culturas.slice(0, 1),
    anoIni: meta.anos_clima[0],
    anoFim: meta.anos_clima[meta.anos_clima.length - 1],
  });

  const selecionadas = useMemo(
    () =>
      linhas.filter(
        (linha) =>
          filtros.ufs.includes(linha.uf) && linha.ano >= filtros.anoIni && linha.ano <= filtros.anoFim,
      ),
    [linhas, filtros],
  );

  const cores = atribuir(filtros.ufs, atribuidas.current);
  const series = filtros.ufs.map((uf) => ({ chave: uf, nome: uf, cor: cores[uf] }));

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="font-serif text-4xl text-stone-900">Clima</h1>
      <div className="mt-6">
        <Filtros
          filtros={filtros}
          definir={definir}
          ufsDisponiveis={meta.ufs}
          culturasDisponiveis={meta.culturas}
          anos={meta.anos_clima}
          comCultura={false}
        />
      </div>

      {selecionadas.length === 0 ? (
        <p className="mt-10 text-stone-600">Sem dados para os filtros selecionados.</p>
      ) : (
        <div className="mt-10 space-y-12">
          <section>
            <h2 className="font-serif text-2xl">Temperatura média (°C)</h2>
            <Linha dados={pivotar(selecionadas, "temp_media")} x="competencia" series={series} rotuloY="°C" />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Precipitação mensal (mm)</h2>
            <p className="text-sm text-stone-500">Média entre as estações de cada estado.</p>
            <Linha dados={pivotar(selecionadas, "precipitacao")} x="competencia" series={series} rotuloY="mm" casas={0} />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Anomalia de temperatura (°C)</h2>
            <p className="text-sm text-stone-500">
              Diferença para a média do mesmo mês no período carregado, não para uma normal de 30 anos.
            </p>
            <Linha dados={pivotar(selecionadas, "anomalia_temp")} x="competencia" series={series} rotuloY="°C" />
          </section>

          <section>
            <h2 className="font-serif text-2xl">Tabela</h2>
            <p className="text-sm text-stone-500">
              A coluna Estações mostra quantas estações contribuíram para cada mês.
            </p>
            <div className="mt-4 max-h-96 overflow-auto rounded-lg border border-stone-200">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-stone-50 text-left text-stone-600">
                  <tr>
                    <th className="px-3 py-2">UF</th>
                    <th className="px-3 py-2">Mês</th>
                    <th className="px-3 py-2">Temp. média</th>
                    <th className="px-3 py-2">Chuva (mm)</th>
                    <th className="px-3 py-2">Dias secos</th>
                    <th className="px-3 py-2">Estações</th>
                  </tr>
                </thead>
                <tbody>
                  {selecionadas.map((linha) => (
                    <tr key={`${linha.uf}-${CHAVE_MES(linha)}`} className="border-t border-stone-100">
                      <td className="px-3 py-1.5">{linha.uf}</td>
                      <td className="px-3 py-1.5">{CHAVE_MES(linha)}</td>
                      <td className="px-3 py-1.5">{numero(linha.temp_media, 1)}</td>
                      <td className="px-3 py-1.5">{numero(linha.precipitacao, 0)}</td>
                      <td className="px-3 py-1.5">{numero(linha.dias_sem_chuva, 0)}</td>
                      <td className="px-3 py-1.5">{linha.n_estacoes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
