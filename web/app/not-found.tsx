import Link from "next/link";

const PAGINAS = [
  { href: "/", texto: "Início", descricao: "o que os dados mostram" },
  { href: "/clima", texto: "Clima", descricao: "temperatura, chuva e anomalia por estado" },
  { href: "/safra", texto: "Safra", descricao: "produção, rendimento e o cruzamento com o clima" },
];

export default function NaoEncontrada() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-24">
      <h1 className="font-serif text-4xl text-stone-900">Página não encontrada</h1>
      <p className="mt-4 max-w-2xl text-stone-600">
        O endereço que você abriu não existe neste site. São três páginas:
      </p>
      <ul className="mt-8 space-y-3">
        {PAGINAS.map((pagina) => (
          <li key={pagina.href}>
            <Link href={pagina.href} className="font-medium text-stone-900 underline">
              {pagina.texto}
            </Link>
            <span className="text-stone-600"> — {pagina.descricao}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
