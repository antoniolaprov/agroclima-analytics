"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { PALETA } from "@/src/lib/cores";

export type Filtros = { ufs: string[]; culturas: string[]; anoIni: number; anoFim: number };

export const MAX_UFS = PALETA.length;

function lista(valor: string): string[] {
  return valor.split(",").map((item) => item.trim()).filter(Boolean);
}

// So aceita numero finito; um parametro invalido ou truncado na URL
// (?ano_ini=abc) cai no padrao em vez de virar NaN e esvaziar a pagina.
function anoValido(valor: string | null, padrao: number): number {
  if (valor === null) return padrao;
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : padrao;
}

// Parametro ausente cai no padrao; parametro presente e vazio e uma escolha
// do leitor (desmarcou tudo) e deve continuar vazio.
export function lerFiltros(parametros: URLSearchParams, padrao: Filtros): Filtros {
  const ufs = parametros.has("ufs") ? lista(parametros.get("ufs") ?? "") : padrao.ufs;
  const culturas = parametros.has("culturas") ? lista(parametros.get("culturas") ?? "") : padrao.culturas;
  return {
    ufs: ufs.slice(0, MAX_UFS),
    culturas,
    anoIni: anoValido(parametros.get("ano_ini"), padrao.anoIni),
    anoFim: anoValido(parametros.get("ano_fim"), padrao.anoFim),
  };
}

// `atuais` preserva os parametros que nao sao filtros, como a escolha de eixo
// da pagina de Safra: montar a query do zero apagaria essa escolha no primeiro
// clique em qualquer filtro.
export function montarQuery(filtros: Filtros, atuais?: URLSearchParams): string {
  const parametros = new URLSearchParams(atuais);
  parametros.set("ufs", filtros.ufs.join(","));
  parametros.set("culturas", filtros.culturas.join(","));
  parametros.set("ano_ini", String(filtros.anoIni));
  parametros.set("ano_fim", String(filtros.anoFim));
  return parametros.toString();
}

export function useFiltros(padrao: Filtros) {
  const parametros = useSearchParams();
  const rota = useRouter();
  const caminho = usePathname();

  // padrao pode chegar como literal novo a cada render; memoizar pelo
  // conteudo (nao pela referencia) evita recomputo e efeitos em laco nos
  // consumidores que dependem de filtros.
  const chavePadrao = JSON.stringify(padrao);
  const filtros = useMemo(
    () => lerFiltros(new URLSearchParams(parametros.toString()), padrao),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chavePadrao ja representa o conteudo de padrao
    [parametros, chavePadrao],
  );

  const definir = useCallback(
    (parcial: Partial<Filtros>) => {
      const novos = { ...filtros, ...parcial };
      novos.ufs = novos.ufs.slice(0, MAX_UFS);
      const query = montarQuery(novos, new URLSearchParams(parametros.toString()));
      rota.replace(`${caminho}?${query}`, { scroll: false });
    },
    [filtros, parametros, rota, caminho],
  );

  return { filtros, definir };
}
