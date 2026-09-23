"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { PALETA } from "@/src/lib/cores";

export type Filtros = { ufs: string[]; culturas: string[]; anoIni: number; anoFim: number };

export const MAX_UFS = PALETA.length;

function lista(valor: string | null): string[] | null {
  if (!valor) return null;
  const itens = valor.split(",").map((item) => item.trim()).filter(Boolean);
  return itens.length ? itens : null;
}

// So aceita numero finito; um parametro invalido ou truncado na URL
// (?ano_ini=abc) cai no padrao em vez de virar NaN e esvaziar a pagina.
function anoValido(valor: string | null, padrao: number): number {
  if (valor === null) return padrao;
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : padrao;
}

export function lerFiltros(parametros: URLSearchParams, padrao: Filtros): Filtros {
  const ufs = lista(parametros.get("ufs")) ?? padrao.ufs;
  return {
    ufs: ufs.slice(0, MAX_UFS),
    culturas: lista(parametros.get("culturas")) ?? padrao.culturas,
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

  const filtros = useMemo(() => lerFiltros(new URLSearchParams(parametros.toString()), padrao), [parametros, padrao]);

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
