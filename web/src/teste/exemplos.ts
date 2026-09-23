import type { LinhaClima, LinhaClimaSafra, LinhaSafra, Meta } from "@/src/lib/dados";

export const climaExemplo: LinhaClima[] = [
  { uf: "MT", ano: 2024, mes: 1, temp_media: 26.4, temp_media_movel_3m: 26.1, precipitacao: 263, anomalia_temp: 0.9, dias_sem_chuva: 0, n_estacoes: 34 },
  { uf: "MT", ano: 2024, mes: 2, temp_media: 26.0, temp_media_movel_3m: 26.2, precipitacao: 219, anomalia_temp: 0.4, dias_sem_chuva: 1, n_estacoes: 34 },
  { uf: "RS", ano: 2024, mes: 1, temp_media: 24.8, temp_media_movel_3m: 24.5, precipitacao: 138, anomalia_temp: -0.3, dias_sem_chuva: 10, n_estacoes: 43 },
  { uf: "RS", ano: 2024, mes: 2, temp_media: 24.1, temp_media_movel_3m: 24.4, precipitacao: 150, anomalia_temp: 0.2, dias_sem_chuva: 8, n_estacoes: 43 },
];

export const safraExemplo: LinhaSafra[] = [
  { uf: "MT", uf_codigo: "51", cultura: "soja", ano: 2024, producao: 38396410, rendimento: 3109, area_colhida: 12350000, var_producao_aa: null },
  { uf: "MT", uf_codigo: "51", cultura: "soja", ano: 2025, producao: 50175032, rendimento: 3923, area_colhida: 12790000, var_producao_aa: 30.68 },
  { uf: "RS", uf_codigo: "43", cultura: "soja", ano: 2024, producao: 18247609, rendimento: 2806, area_colhida: 6500000, var_producao_aa: null },
  { uf: "RS", uf_codigo: "43", cultura: "soja", ano: 2025, producao: 13000000, rendimento: 2012, area_colhida: 6460000, var_producao_aa: -28.76 },
];

export const climaSafraExemplo: LinhaClimaSafra[] = [
  { uf: "MT", cultura: "soja", ano: 2024, rendimento: 3109, precip_ciclo: 1066, temp_media_ciclo: 25.9, n_estacoes: 34 },
  { uf: "MT", cultura: "soja", ano: 2025, rendimento: 3923, precip_ciclo: 1349, temp_media_ciclo: 25.6, n_estacoes: 34 },
  { uf: "RS", cultura: "soja", ano: 2024, rendimento: 2806, precip_ciclo: 1150, temp_media_ciclo: 21.4, n_estacoes: 43 },
  { uf: "RS", cultura: "soja", ano: 2025, rendimento: 2012, precip_ciclo: 660, temp_media_ciclo: 21.1, n_estacoes: 43 },
];

export const metaExemplo: Meta = {
  gerado_em: "2026-09-22T12:00:00+00:00",
  ufs: ["MT", "RS"],
  culturas: ["soja"],
  anos: [2024, 2025],
  anos_clima: [2024, 2025],
  anos_safra: [2024, 2025],
  linhas_por_arquivo: { clima: 4, safra: 4, clima_safra: 4 },
  fontes: [{ nome: "INMET", url: "https://portal.inmet.gov.br/dadoshistoricos" }],
};
