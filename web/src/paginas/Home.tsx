"use client";

import { useMemo, useState } from "react";
import { Dispersao } from "@/src/graficos/Dispersao";
import { MapaUF } from "@/src/graficos/MapaUF";
import { Secao } from "@/src/layout/Secao";
import { correlacao } from "@/src/lib/correlacao";
import type { LinhaClimaSafra, LinhaSafra, Meta } from "@/src/lib/dados";
import {
  producaoPorCodigoUf, safrasMaisSecas, siglaPorCodigoUf, ultimoAno,
} from "@/src/lib/destaques";
import {
  cultura as nomeCultura, inteiro, numero, porExtensoFeminino,
} from "@/src/lib/formato";

const DESTAQUE = ["MT", "PR", "RS"];
const COR_RESTANTE = "#a8a29e";
const COR_SECA = "#e34948";

function pares(linhas: LinhaClimaSafra[]): [number, number][] {
  return linhas
    .filter((linha) => linha.precip_ciclo !== null && linha.rendimento !== null)
    .map((linha) => [linha.precip_ciclo as number, linha.rendimento as number]);
}

// Junta nomes do jeito que se fala em portugues, com "e" antes do ultimo;
// mantem a frase gramatical com um, dois ou tres nomes.
function listaEstados(estados: string[]): string {
  if (estados.length <= 1) return estados.join("");
  return `${estados.slice(0, -1).join(", ")} e ${estados[estados.length - 1]}`;
}

function pontos(linhas: LinhaClimaSafra[]): { x: number; y: number }[] {
  return pares(linhas).map(([x, y]) => ({ x, y }));
}

export function Home({
  safra, climaSafra, meta,
}: {
  safra: LinhaSafra[];
  climaSafra: LinhaClimaSafra[];
  meta: Meta;
}) {
  const [cultura, setCultura] = useState(
    // soja e a cultura com o caso do RS (bloco 3) na amostra; abrir em
    // meta.culturas[0] (cafe, por ordem alfabetica) deixaria esse bloco vazio.
    meta.culturas.includes("soja") ? "soja" : meta.culturas[0],
  );
  const ano = useMemo(
    () => ultimoAno(safra.filter((linha) => linha.cultura === cultura)),
    [safra, cultura],
  );
  const valores = useMemo(
    () => producaoPorCodigoUf(safra, cultura, ano),
    [safra, cultura, ano],
  );
  const siglas = useMemo(() => siglaPorCodigoUf(safra), [safra]);

  const doAno = safra.filter((linha) => linha.cultura === cultura && linha.ano === ano);
  const comProducao = doAno.filter(
    (linha): linha is LinhaSafra & { producao: number } => linha.producao !== null,
  );
  const producaoTotal = comProducao.reduce((soma, linha) => soma + linha.producao, 0);
  const lider = comProducao.reduce<(LinhaSafra & { producao: number }) | null>(
    (maior, linha) => (maior === null || linha.producao > maior.producao ? linha : maior),
    null,
  );

  const rsCruzamento = climaSafra.filter((linha) => linha.uf === "RS" && linha.cultura === cultura);
  const rsSecas = safrasMaisSecas(rsCruzamento, 2);
  const anosSecos = new Set(rsSecas.map((linha) => linha.ano));
  const rsRestante = rsCruzamento.filter((linha) => !anosSecos.has(linha.ano));
  const gruposRs = [
    { nome: "Demais safras", cor: COR_RESTANTE, pontos: pontos(rsRestante) },
    { nome: "Safras mais secas", cor: COR_SECA, pontos: pontos(rsSecas) },
  ].filter((grupo) => grupo.pontos.length > 0);

  const doPais = climaSafra.filter((linha) => linha.cultura === cultura);
  // So entra na frase e na legenda o estado de DESTAQUE que realmente tem
  // pelo menos um ponto cruzado para a cultura escolhida; nomear um estado
  // sem dado venderia uma amostra que ele nao integra.
  const estadosDestaque = DESTAQUE.filter((uf) =>
    doPais.some((linha) => linha.uf === uf && linha.precip_ciclo !== null && linha.rendimento !== null),
  );
  const daSelecao = doPais.filter((linha) => estadosDestaque.includes(linha.uf));
  const rSelecao = correlacao(pares(daSelecao));
  const rPais = correlacao(pares(doPais));
  const nomeSelecao = listaEstados(estadosDestaque);
  // A direcao da mudanca depende da cultura: na soja a relacao desaba fora da
  // selecao, no milho ela e mais forte no pais. Comparar as forcas evita que a
  // frase afirme uma queda que nao aconteceu.
  const enfraqueceNoPais =
    rSelecao !== null && rPais !== null && Math.abs(rSelecao) > Math.abs(rPais);
  const gruposPais = [
    { nome: "Todos os estados", cor: COR_RESTANTE, pontos: pontos(doPais) },
    { nome: nomeSelecao, cor: "#2a78d6", pontos: pontos(daSelecao) },
  ].filter((grupo) => grupo.pontos.length > 0);

  return (
    <div>
      <section className="mx-auto max-w-6xl px-6 pb-8 pt-20">
        <h1 className="max-w-3xl font-serif text-5xl leading-tight text-stone-900">
          Como a chuva aparece na produtividade agrícola brasileira
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-stone-600">
          Clima horário das estações do INMET e safras do IBGE, cruzados por estado
          entre {meta.anos_clima[0]} e {meta.anos_clima[meta.anos_clima.length - 1]}.
        </p>
      </section>

      <Secao
        titulo="O Brasil que planta"
        descricao={
          lider ? (
            <p>
              Em {ano}, o país colheu {inteiro(producaoTotal)} toneladas de{" "}
              {nomeCultura(cultura).toLocaleLowerCase("pt-BR")}, soma que não cobre todos os estados.{" "}
              {lider.uf} respondeu por {inteiro(lider.producao)} delas, com rendimento de{" "}
              {inteiro(lider.rendimento)} kg/ha.
            </p>
          ) : null
        }
      >
        <div className="mb-4 flex gap-2 text-sm">
          {meta.culturas.map((opcao) => (
            <button
              key={opcao}
              type="button"
              onClick={() => setCultura(opcao)}
              aria-pressed={cultura === opcao}
              className={`rounded-full border px-3 py-1 ${
                cultura === opcao ? "border-stone-900 bg-stone-900 text-white" : "border-stone-300 text-stone-600"
              }`}
            >
              {nomeCultura(opcao)}
            </button>
          ))}
        </div>
        <MapaUF
          valores={valores}
          siglas={siglas}
          rotulo={`Produção de ${nomeCultura(cultura).toLocaleLowerCase("pt-BR")} em ${ano} (t)`}
        />
      </Secao>

      <Secao
        titulo="Quando falta chuva"
        descricao={
          rsSecas.length > 0 ? (
            <p>
              O Rio Grande do Sul entra nesta amostra com apenas {porExtensoFeminino(rsCruzamento.length)} safras de{" "}
              {nomeCultura(cultura).toLocaleLowerCase("pt-BR")} cruzadas com o clima — poucos pontos,
              mas o padrão aparece: as {porExtensoFeminino(rsSecas.length)} mais secas do ciclo,{" "}
              {rsSecas.map((linha) => `${linha.ano} (${inteiro(linha.precip_ciclo)} mm)`).join(" e ")},
              também tiveram o pior rendimento,{" "}
              {rsSecas.map((linha) => `${inteiro(linha.rendimento)} kg/ha`).join(" e ")}.
            </p>
          ) : (
            <p>
              Não há safras cruzadas do Rio Grande do Sul para{" "}
              {nomeCultura(cultura).toLocaleLowerCase("pt-BR")}.
            </p>
          )
        }
      >
        <Dispersao grupos={gruposRs} rotuloX="Chuva acumulada no ciclo (mm)" rotuloY="Rendimento (kg/ha)" />
      </Secao>

      <Secao
        titulo="Mas não é só chuva"
        descricao={
          estadosDestaque.length > 0 ? (
            <p>
              Com {nomeSelecao}, a correlação entre chuva do ciclo e rendimento é de{" "}
              <strong>{rSelecao === null ? "-" : numero(rSelecao, 2)}</strong>. Com todos os estados que
              plantam {nomeCultura(cultura).toLocaleLowerCase("pt-BR")}, vai para{" "}
              <strong>{rPais === null ? "-" : numero(rPais, 2)}</strong>:{" "}
              {enfraqueceNoPais
                ? "a relação enfraquece fora da seleção."
                : "a relação não enfraquece fora da seleção."}{" "}
              Secas fortes aparecem nos dados, mas a chuva total do ciclo sozinha não explica o rendimento no país: irrigação,
              distribuição da chuva ao longo do ciclo e manejo pesam, e o projeto não mede essas
              variáveis.
            </p>
          ) : (
            <p>
              Nenhum dos estados da seleção padrão tem safras de{" "}
              {nomeCultura(cultura).toLocaleLowerCase("pt-BR")} cruzadas com o clima. Com todos os
              estados que plantam {nomeCultura(cultura).toLocaleLowerCase("pt-BR")}, a correlação
              entre chuva do ciclo e rendimento é de{" "}
              <strong>{rPais === null ? "-" : numero(rPais, 2)}</strong>. Secas fortes aparecem nos
              dados, mas a chuva total do ciclo sozinha não explica o rendimento no país: irrigação,
              distribuição da chuva ao longo do ciclo e manejo pesam, e o projeto não mede essas
              variáveis.
            </p>
          )
        }
      >
        <Dispersao grupos={gruposPais} rotuloX="Chuva acumulada no ciclo (mm)" rotuloY="Rendimento (kg/ha)" />
      </Secao>

      <Secao
        titulo="Como isso é feito"
        descricao={
          <p>
            Python busca os dados nas APIs e grava Parquet. O dbt, sobre DuckDB, limpa, agrega e testa
            em camadas Bronze, Silver e Gold. O Airflow roda tudo todo dia às 6h. Este site consome um
            extrato estático dessas tabelas.
          </p>
        }
      >
        <ol className="grid gap-3 text-sm text-stone-700 sm:grid-cols-4">
          {["INMET e IBGE", "Bronze (Parquet)", "Silver e Gold (dbt)", "Site estático"].map((etapa, indice) => (
            <li key={etapa} className="rounded-lg border border-stone-200 bg-white/70 p-4">
              <span className="block text-xs text-stone-400">{indice + 1}</span>
              {etapa}
            </li>
          ))}
        </ol>
        <p className="mt-6 flex gap-4 text-sm">
          <a className="underline" href="https://github.com/antoniolaprov/agroclima-analytics">
            Código no GitHub
          </a>
          <a
            className="underline"
            href="https://github.com/antoniolaprov/agroclima-analytics/blob/main/docs/design.md"
          >
            Documento de design
          </a>
        </p>
      </Secao>
    </div>
  );
}
