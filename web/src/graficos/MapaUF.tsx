"use client";

import { geoMercator, geoPath } from "d3-geo";
import { useEffect, useMemo, useState } from "react";
import { numero } from "@/src/lib/formato";
import { corrigirOrientacao, escalaVerde, SEM_DADO, type MalhaUF } from "./mapa";

export function MapaUF({
  valores,
  rotulo,
  casas = 0,
}: {
  valores: Record<string, number | null>;
  rotulo: string;
  casas?: number;
}) {
  const [malha, setMalha] = useState<MalhaUF | null>(null);
  const [focada, setFocada] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/uf_br.geojson")
      .then((resposta) => resposta.json())
      .then((bruta: MalhaUF) => setMalha(corrigirOrientacao(bruta)));
  }, []);

  const maximo = useMemo(
    () => Math.max(0, ...Object.values(valores).map((valor) => valor ?? 0)),
    [valores],
  );

  const caminhos = useMemo(() => {
    if (!malha) return [];
    const projecao = geoMercator().fitSize([640, 640], malha as never);
    const desenho = geoPath(projecao);
    return malha.features.map((feicao) => ({
      codigo: feicao.properties.codarea,
      d: desenho(feicao as never) ?? "",
    }));
  }, [malha]);

  if (!malha) {
    return <div className="h-[520px] animate-pulse rounded-lg bg-stone-100" aria-hidden />;
  }

  return (
    <figure className="relative">
      <svg viewBox="0 0 640 640" className="w-full" role="img" aria-label={`Mapa: ${rotulo}`}>
        {caminhos.map((caminho) => (
          <path
            key={caminho.codigo}
            d={caminho.d}
            fill={escalaVerde(valores[caminho.codigo] ?? null, maximo)}
            stroke="#fbfbf9"
            strokeWidth={0.8}
            onMouseEnter={() => setFocada(caminho.codigo)}
            onMouseLeave={() => setFocada(null)}
          />
        ))}
      </svg>
      <figcaption className="mt-2 text-sm text-stone-600">
        {focada
          ? `${focada}: ${numero(valores[focada] ?? null, casas)}`
          : rotulo}
      </figcaption>
      <div className="mt-2 flex items-center gap-2 text-xs text-stone-500">
        <span>{numero(0, casas)}</span>
        <div
          className="h-2 w-40 rounded"
          style={{ background: `linear-gradient(to right, ${escalaVerde(0, 1)}, ${escalaVerde(1, 1)})` }}
        />
        <span>{numero(maximo, casas)}</span>
        <span className="ml-3 inline-flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded" style={{ background: SEM_DADO }} />
          sem dado
        </span>
      </div>
    </figure>
  );
}
