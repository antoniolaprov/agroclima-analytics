"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

// Uma escolha de visualizacao, nao um filtro: nao recorta o dado, so decide o
// que o grafico mostra. Fica fora de `Filtros` para nao aparecer como
// parametro morto nas paginas que nao tem essa escolha, que foi o que
// aconteceu quando a de Clima carregava `culturas` sem filtrar por cultura.

export function lerOpcao<T extends string>(
  parametros: URLSearchParams,
  chave: string,
  opcoes: readonly T[],
  padrao: T,
): T {
  const valor = parametros.get(chave);
  return opcoes.includes(valor as T) ? (valor as T) : padrao;
}

export function montarQueryOpcao(parametros: URLSearchParams, chave: string, valor: string): string {
  const novos = new URLSearchParams(parametros);
  novos.set(chave, valor);
  return novos.toString();
}

export function useOpcaoUrl<T extends string>(chave: string, opcoes: readonly T[], padrao: T) {
  const parametros = useSearchParams();
  const rota = useRouter();
  const caminho = usePathname();

  const valor = useMemo(
    () => lerOpcao(new URLSearchParams(parametros.toString()), chave, opcoes, padrao),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- opcoes costuma chegar como literal; a lista em si nao muda
    [parametros, chave, padrao],
  );

  const definir = useCallback(
    (novo: T) => {
      const query = montarQueryOpcao(new URLSearchParams(parametros.toString()), chave, novo);
      rota.replace(`${caminho}?${query}`, { scroll: false });
    },
    [parametros, chave, rota, caminho],
  );

  return [valor, definir] as const;
}
