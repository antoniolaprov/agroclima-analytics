"use client";

import { useEffect, useState } from "react";
import { cultura as nomeCultura } from "@/src/lib/formato";
import { MAX_UFS, type Filtros as TipoFiltros } from "./useFiltros";

// Tela grande o bastante pra nao precisar recolher o painel; mesmo ponto de
// corte do breakpoint "lg" do Tailwind, pra CSS e JS concordarem.
const TELA_GRANDE = "(min-width: 1024px)";

// O resumo aparece no botao mesmo com o painel fechado, pra quem le nao
// precisar abrir o painel so pra saber o que esta selecionado.
function resumoFiltros(filtros: TipoFiltros, comCultura: boolean): string {
  const estados = filtros.ufs.length > 0 ? filtros.ufs.join(", ") : "nenhum estado";
  const periodo = `${filtros.anoIni} a ${filtros.anoFim}`;
  if (!comCultura) return `${estados}, ${periodo}`;
  const culturaTexto = filtros.culturas[0] ? nomeCultura(filtros.culturas[0]) : "nenhuma cultura";
  return `${estados}, ${culturaTexto}, ${periodo}`;
}

export function Filtros({
  filtros, definir, ufsDisponiveis, culturasDisponiveis, anos, comCultura = true,
}: {
  filtros: TipoFiltros;
  definir: (parcial: Partial<TipoFiltros>) => void;
  ufsDisponiveis: string[];
  culturasDisponiveis: string[];
  anos: number[];
  comCultura?: boolean;
}) {
  const limiteAtingido = filtros.ufs.length >= MAX_UFS;
  // Comeca aberto: sem JS ou antes do efeito rodar, mostra tudo (igual a tela
  // grande); o efeito recolhe se a tela for pequena.
  const [aberto, setAberto] = useState(true);

  useEffect(() => {
    const consulta = window.matchMedia(TELA_GRANDE);
    const aplicar = () => setAberto(consulta.matches);
    aplicar();
    consulta.addEventListener("change", aplicar);
    return () => consulta.removeEventListener("change", aplicar);
  }, []);

  function alternarUf(uf: string) {
    const selecionadas = filtros.ufs.includes(uf)
      ? filtros.ufs.filter((item) => item !== uf)
      : [...filtros.ufs, uf].slice(0, MAX_UFS);
    definir({ ufs: selecionadas });
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white/70 p-4">
      <button
        type="button"
        onClick={() => setAberto((valor) => !valor)}
        aria-expanded={aberto}
        className="flex w-full items-center justify-between gap-2 text-left lg:hidden"
      >
        <span className="text-sm text-stone-600">Filtros: {resumoFiltros(filtros, comCultura)}</span>
        <span aria-hidden="true" className="text-stone-400">{aberto ? "▲" : "▼"}</span>
      </button>

      {aberto ? (
        <div className="mt-4 lg:mt-0">
          <p className="text-xs uppercase tracking-wide text-stone-500">Estados (até {MAX_UFS})</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {ufsDisponiveis.map((uf) => {
              const ativa = filtros.ufs.includes(uf);
              const desabilitada = !ativa && limiteAtingido;
              return (
                <button
                  key={uf}
                  type="button"
                  onClick={() => alternarUf(uf)}
                  disabled={desabilitada}
                  title={desabilitada ? `Limite de ${MAX_UFS} estados atingido, desmarque um para trocar` : undefined}
                  aria-pressed={ativa}
                  className={`rounded-full border px-3 py-1 text-sm ${
                    ativa
                      ? "border-stone-900 bg-stone-900 text-white"
                      : desabilitada
                        ? "border-stone-200 text-stone-300"
                        : "border-stone-300 text-stone-600 hover:border-stone-500"
                  }`}
                >
                  {uf}
                </button>
              );
            })}
          </div>

          {comCultura ? (
            <>
              <p className="mt-4 text-xs uppercase tracking-wide text-stone-500">Cultura</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {culturasDisponiveis.map((cultura) => (
                  <button
                    key={cultura}
                    type="button"
                    onClick={() => definir({ culturas: [cultura] })}
                    aria-pressed={filtros.culturas[0] === cultura}
                    className={`rounded-full border px-3 py-1 text-sm ${
                      filtros.culturas[0] === cultura
                        ? "border-stone-900 bg-stone-900 text-white"
                        : "border-stone-300 text-stone-600 hover:border-stone-500"
                    }`}
                  >
                    {nomeCultura(cultura)}
                  </button>
                ))}
              </div>
            </>
          ) : null}

          <p className="mt-4 text-xs uppercase tracking-wide text-stone-500">Período</p>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <select
              className="rounded border border-stone-300 px-2 py-1"
              value={filtros.anoIni}
              onChange={(evento) => {
                const anoIni = Number(evento.target.value);
                definir(anoIni > filtros.anoFim ? { anoIni, anoFim: anoIni } : { anoIni });
              }}
              aria-label="Ano inicial"
            >
              {anos.map((ano) => <option key={ano} value={ano}>{ano}</option>)}
            </select>
            <span className="text-stone-400">até</span>
            <select
              className="rounded border border-stone-300 px-2 py-1"
              value={filtros.anoFim}
              onChange={(evento) => {
                const anoFim = Number(evento.target.value);
                definir(anoFim < filtros.anoIni ? { anoFim, anoIni: anoFim } : { anoFim });
              }}
              aria-label="Ano final"
            >
              {anos.map((ano) => <option key={ano} value={ano}>{ano}</option>)}
            </select>
          </div>
        </div>
      ) : null}
    </div>
  );
}
