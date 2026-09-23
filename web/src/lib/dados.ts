import fs from "node:fs";
import path from "node:path";

export type LinhaClima = {
  uf: string;
  ano: number;
  mes: number;
  temp_media: number | null;
  temp_media_movel_3m: number | null;
  precipitacao: number | null;
  anomalia_temp: number | null;
  dias_sem_chuva: number | null;
  n_estacoes: number;
};

export type LinhaSafra = {
  uf: string;
  uf_codigo: string;
  cultura: string;
  ano: number;
  producao: number | null;
  rendimento: number | null;
  area_colhida: number | null;
  var_producao_aa: number | null;
};

export type LinhaClimaSafra = {
  uf: string;
  cultura: string;
  ano: number;
  rendimento: number | null;
  precip_ciclo: number | null;
  temp_media_ciclo: number | null;
  n_estacoes: number;
};

export type Meta = {
  gerado_em: string;
  ufs: string[];
  culturas: string[];
  anos: number[];
  anos_clima: number[];
  anos_safra: number[];
  linhas_por_arquivo: Record<string, number>;
  fontes: { nome: string; url: string }[];
};

// Leitura em tempo de build: os componentes de servidor chamam estas funcoes e
// passam o resultado como props. O site e estatico, entao nao ha busca em runtime.
function ler<T>(arquivo: string): T {
  const caminho = path.join(process.cwd(), "public", "data", arquivo);
  return JSON.parse(fs.readFileSync(caminho, "utf-8")) as T;
}

export const carregarClima = () => ler<LinhaClima[]>("clima.json");
export const carregarSafra = () => ler<LinhaSafra[]>("safra.json");
export const carregarClimaSafra = () => ler<LinhaClimaSafra[]>("clima_safra.json");
export const carregarMeta = () => ler<Meta>("meta.json");
