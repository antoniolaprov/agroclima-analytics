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

export function montarQuery(filtros: Filtros): string {
  const parametros = new URLSearchParams({
    ufs: filtros.ufs.join(","),
    culturas: filtros.culturas.join(","),
    ano_ini: String(filtros.anoIni),
    ano_fim: String(filtros.anoFim),
  });
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
      rota.replace(`${caminho}?${montarQuery(novos)}`, { scroll: false });
    },
    [filtros, rota, caminho],
  );

  return { filtros, definir };
}
