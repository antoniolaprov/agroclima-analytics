import Link from "next/link";

const PAGINAS = [
  { href: "/", texto: "Inicio" },
  { href: "/clima", texto: "Clima" },
  { href: "/safra", texto: "Safra" },
];

export function Cabecalho() {
  return (
    <header className="sticky top-0 z-20 border-b border-stone-200 bg-[#fbfbf9]/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-serif text-lg tracking-tight text-stone-900">
          AgroClima
        </Link>
        <ul className="flex gap-6 text-sm text-stone-600">
          {PAGINAS.map((pagina) => (
            <li key={pagina.href}>
              <Link href={pagina.href} className="hover:text-stone-900">
                {pagina.texto}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
