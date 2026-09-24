import type { Meta } from "@/src/lib/dados";

export function Rodape({ meta }: { meta: Meta }) {
  const gerado = new Date(meta.gerado_em).toLocaleDateString("pt-BR");
  const climaInicio = meta.anos_clima[0];
  const climaFim = meta.anos_clima[meta.anos_clima.length - 1];
  const safraInicio = meta.anos_safra[0];
  const safraFim = meta.anos_safra[meta.anos_safra.length - 1];
  return (
    <footer className="mt-24 border-t border-stone-200 bg-white/60">
      <div className="mx-auto max-w-6xl px-6 py-10 text-sm text-stone-600">
        <p>
          Clima de {climaInicio} a {climaFim}, safra de {safraInicio} a {safraFim}, extraídos em {gerado}.
        </p>
        <ul className="mt-3 flex flex-wrap gap-4">
          {meta.fontes.map((fonte) => (
            <li key={fonte.url}>
              <a className="underline hover:text-stone-900" href={fonte.url}>
                {fonte.nome}
              </a>
            </li>
          ))}
          <li>
            <a
              className="underline hover:text-stone-900"
              href="https://github.com/antoniolaprov/agroclima-analytics#limitacoes-conhecidas"
            >
              Limitações conhecidas
            </a>
          </li>
        </ul>
      </div>
    </footer>
  );
}
