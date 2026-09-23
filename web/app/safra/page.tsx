import { Suspense } from "react";
import { Safra } from "@/src/paginas/Safra";
import { carregarClimaSafra, carregarMeta, carregarSafra } from "@/src/lib/dados";

export default function PaginaSafra() {
  return (
    <Suspense>
      <Safra safra={carregarSafra()} climaSafra={carregarClimaSafra()} meta={carregarMeta()} />
    </Suspense>
  );
}
