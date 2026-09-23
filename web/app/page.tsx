import { Home } from "@/src/paginas/Home";
import { carregarClimaSafra, carregarMeta, carregarSafra } from "@/src/lib/dados";

export default function Pagina() {
  return <Home safra={carregarSafra()} climaSafra={carregarClimaSafra()} meta={carregarMeta()} />;
}
