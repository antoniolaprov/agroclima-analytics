import type { ReactNode } from "react";

export function Secao({
  titulo,
  descricao,
  children,
}: {
  titulo?: string;
  descricao?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      {titulo ? <h2 className="font-serif text-3xl text-stone-900">{titulo}</h2> : null}
      {descricao ? <div className="mt-3 max-w-2xl text-stone-600">{descricao}</div> : null}
      <div className="mt-8">{children}</div>
    </section>
  );
}
