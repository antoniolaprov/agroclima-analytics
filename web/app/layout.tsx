import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import { Cabecalho } from "@/src/layout/Cabecalho";
import { Rodape } from "@/src/layout/Rodape";
import { carregarMeta } from "@/src/lib/dados";
import "./globals.css";

const serif = Fraunces({ subsets: ["latin"], variable: "--fonte-serif" });
const sans = Inter({ subsets: ["latin"], variable: "--fonte-sans" });

export const metadata: Metadata = {
  title: "AgroClima Analytics",
  description: "Como chuva e temperatura se relacionam com a produtividade agrícola, por estado.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const meta = carregarMeta();
  return (
    <html lang="pt-BR" className={`${serif.variable} ${sans.variable}`}>
      <body className="bg-[#fbfbf9] font-sans text-stone-800 antialiased">
        <Cabecalho />
        <main>{children}</main>
        <Rodape meta={meta} />
      </body>
    </html>
  );
}
