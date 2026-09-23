import { Suspense } from "react";
import { Clima } from "@/src/paginas/Clima";
import { carregarClima, carregarMeta } from "@/src/lib/dados";

export default function PaginaClima() {
  return (
    <Suspense>
      <Clima linhas={carregarClima()} meta={carregarMeta()} />
    </Suspense>
  );
}
