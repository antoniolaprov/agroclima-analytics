# AgroClima Web — Design

Data: 2026-09-22

## 1. Objetivo

Um site público, estático, que conta o que o AgroClima Analytics descobriu e
deixa quem quiser explorar os dados. Hoje o projeto só pode ser visto por quem
clona o repositório e sobe o Docker; o site resolve isso com um link.

Dois públicos, nessa ordem:

1. Quem abre por dois minutos e precisa entender o projeto e sair com boa
   impressão — a home resolve isso sozinha.
2. Quem quer investigar — as páginas de Clima e Safra, com filtros.

O dashboard Streamlit continua no repositório como ferramenta de análise
local. O site não o substitui: o README explica o papel de cada um.

## 2. Escopo

**Dentro do escopo:**

- Home narrativa em rolagem, com seis blocos
- Página de Clima e página de Safra, com filtros e estado na URL
- Mapa coroplético das 27 UFs, desenhado em SVG
- Exportação dos dados agregados do DuckDB para JSON versionado
- Site em português, estático, publicado na Vercel

**Fora do escopo:**

- Backend, banco servido ou API
- Autenticação e qualquer estado por usuário
- Tema escuro
- Internacionalização
- Substituir o dashboard Streamlit

## 3. Arquitetura

```
warehouse.duckdb  ──scripts/exportar_web.py──►  web/public/data/*.json
                                                        │
                                              Next.js (output: export)
                                                        │
                                                   Vercel (estático)
```

Next.js com App Router e exportação estática (`output: 'export'`). Estático
porque o site passa a rodar igual na Vercel, no GitHub Pages ou aberto
localmente, sem depender de servidor. Não há SSR nem rotas de API: todo dado
é arquivo.

### 3.1 Contrato dos dados

`scripts/exportar_web.py` lê o `warehouse.duckdb` e escreve em
`web/public/data/`:

| Arquivo | Colunas |
|---|---|
| `clima.json` | `uf`, `ano`, `mes`, `temp_media`, `temp_media_movel_3m`, `precipitacao`, `anomalia_temp`, `dias_sem_chuva`, `n_estacoes` |
| `safra.json` | `uf`, `uf_codigo`, `cultura`, `ano`, `producao`, `rendimento`, `area_colhida`, `var_producao_aa` |
| `clima_safra.json` | `uf`, `cultura`, `ano`, `rendimento`, `precip_ciclo`, `temp_media_ciclo`, `n_estacoes` |
| `meta.json` | `gerado_em`, `anos`, `anos_clima`, `anos_safra`, `ufs`, `culturas`, `linhas_por_arquivo`, `fontes` |

Regras do export:

- Só as colunas da tabela acima. As Gold têm mais colunas; o site não usa.
- Arredondamento: uma casa decimal para temperatura e anomalia, zero casas
  para chuva, produção, área e rendimento, duas para variação percentual.
- `null` é preservado como `null` (chuva de mês incompleto, variação sem ano
  anterior). O site trata ausência explicitamente, nunca substitui por zero.
- A malha `dashboard/assets/uf_br.geojson` é copiada para
  `web/public/data/uf_br.geojson`. Uma fonte, dois consumidores; o arquivo não
  é duplicado à mão no repositório.

`uf_codigo` existe porque o mapa casa pelo código IBGE (`codarea` da malha),
não pela sigla. `anos_clima` e `anos_safra` são listas separadas porque a série
da PAM tem 52 anos e a do clima tem 5: um único campo `anos` faria o seletor de
período da página de Clima oferecer 1974 e responder "sem dados".

Tamanho real do extrato: 1,19 MB crus, dos quais `safra.json` sozinho ocupa
753 KB por causa dos 52 anos da PAM. A estimativa inicial de 600 KB contava só
a janela do clima. Servido com gzip, o que chega ao navegador é 22 KB na página
de Clima e 99 KB na home e na de Safra, mais 103 KB de JavaScript
compartilhado.

**Os JSON são versionados.** É o que permite publicar sem servidor: a Vercel
publica o que está no repositório. O `meta.json` traz `gerado_em`, exibido no
rodapé, para ninguém confundir o extrato com dado ao vivo.

O `data/` com Bronze e DuckDB continua fora do git.

### 3.2 Integração com o pipeline

- `make exportar-web` roda o script.
- `src/pipeline.py` chama o export ao final de `main()`, depois do `dbt
  build`, mas isso é um passo local: a DAG do Airflow chama só `rodar_dbt`,
  nunca `main()`, então o export nunca roda dentro do container. Atualizar os
  JSON é uma execução manual, feita por quem mantém o projeto, via `make
  exportar-web` ou `python -m src.pipeline`, antes de publicar.
- O commit dos JSON é manual e deliberado: publicar é decisão de quem
  mantém, não efeito colateral de um agendamento.

## 4. Páginas

### 4.1 Home

Rolagem com seis blocos:

1. **Abertura** — título, a pergunta do projeto em uma linha, período coberto.
2. **O Brasil que planta** — mapa coroplético em largura total, seletor
   discreto de cultura, duas ou três frases com os números do ano mais recente.
3. **Quando falta chuva** — o caso do Rio Grande do Sul: nas safras 2022/23 e
   2024/25 o ciclo teve 540 e 660 mm e a produtividade caiu ao menor patamar
   da amostra. Um gráfico, com esses pontos destacados.
4. **Mas não é só chuva** — dispersão com todas as UFs, mostrando que a
   correlação de 0,88 da seleção padrão vira 0,10 no país inteiro.
5. **Como isso é feito** — diagrama do pipeline, tecnologias, links para o
   repositório e para `docs/design.md`.
6. **Rodapé** — fontes, `gerado_em` e link para as limitações conhecidas.

O bloco 4 não é opcional: é o que impede o site de vender uma conclusão que
os dados não sustentam.

### 4.2 Clima

Filtros de UF (até 8, o tamanho da paleta) e período. Temperatura com média
móvel, chuva mensal, anomalia de temperatura. Tabela ao final com
`n_estacoes` visível.

### 4.3 Safra

Filtros de UF e cultura. Produção, rendimento, variação anual e, na mesma
página, o cruzamento clima × safra com a dispersão e o coeficiente de
correlação.

O cruzamento fica aqui, e não em página própria como no Streamlit, porque
depende dos mesmos filtros (UF e cultura): separá-lo obrigaria a refazer a
seleção numa terceira tela.

### 4.4 Navegação

Cabeçalho fixo com Início, Clima e Safra. No celular os gráficos empilham e
os filtros ficam num painel recolhível.

## 5. Sistema visual

Tailwind com shadcn/ui. Tipografia em dois níveis: serifada nos títulos da
home, sem serifa em interface e rótulos de gráfico. Fundo claro, muito espaço
em branco, verde apenas nos dados.

**As cores dos dados são as mesmas do Streamlit**: a paleta categórica de oito
posições já validada para daltonismo, e o verde sequencial no mapa. Os dois
dashboards passam a ter a mesma identidade, e um estado tem a mesma cor nos
dois. A paleta é revalidada contra o fundo do site, que não é branco puro.

Regra que vem do dashboard e continua valendo: **a cor segue o estado, não a
posição na seleção**. Tirar uma UF do filtro não repinta as outras.

## 6. Componentes

| Módulo | Responsabilidade |
|---|---|
| `lib/dados.ts` | Carrega os JSON e expõe os tipos TypeScript de cada tabela |
| `lib/formato.ts` | Números no padrão brasileiro, mesma regra de `dashboard/graficos.py` |
| `lib/cores.ts` | Paleta e atribuição estável por UF |
| `graficos/Linha.tsx`, `Barras.tsx`, `Dispersao.tsx` | Invólucros sobre Recharts com eixos, tooltip e legenda padronizados |
| `graficos/MapaUF.tsx` | Mapa em SVG com `d3-geo` |
| `filtros/` | UF, cultura e período, com o estado na URL |
| `layout/` | Cabeçalho, rodapé e a casca das seções |

O estado dos filtros vive na URL (`searchParams`): uma seleção vira link
compartilhável sem nenhum armazenamento.

**Mapa.** Recharts não faz mapas. O coroplético é SVG desenhado com `d3-geo`
a partir da malha do IBGE. A malha segue a RFC 7946, com anel externo em
sentido anti-horário, e `d3-geo` espera o contrário: sem inverter os anéis, o
mapa inteiro é pintado. O mesmo problema já apareceu no dashboard Streamlit e
está resolvido lá em `dashboard/views/overview.py`.

## 7. Testes

- **Vitest e Testing Library** para a lógica: formatação, atribuição de cores,
  filtros e a geração dos caminhos do mapa — inclusive um teste sobre a
  orientação dos anéis, que é onde mora o bug conhecido.
- **Um teste de renderização por página**, com JSON de exemplo, garantindo que
  nenhuma página quebra. No Streamlit uma página quebrava e nenhum teste via,
  porque o teste só abria a página inicial.
- **Teste Python do script de export**, no estilo dos existentes: fixture
  pequena, diretório temporário, conferindo colunas, arredondamento e
  preservação de `null`.
- **Conferência visual no navegador**, página por página, antes de publicar.
  Teste verde não garante tela correta; no Streamlit o mapa passou nos testes
  e apareceu errado na tela.

## 8. Deploy

`next build` com `output: 'export'` gera HTML estático. Na Vercel, o projeto
aponta para o diretório `web/`.

Conectar o repositório à Vercel exige login na conta do autor e não é feito
por quem implementa. O fluxo é: implementação pronta e build verificado
localmente, o autor conecta o projeto, e a URL resultante entra no README e na
descrição do repositório no GitHub.

## 9. Impacto no que já existe

- `.gitignore`: `node_modules/`, `.next/`, `web/out/`
- `README.md`: seção sobre o site, deixando claro que ele é a vitrine pública
  e o Streamlit é a ferramenta de análise local
- `docs/design.md`: referência a este documento
- `Makefile`: alvos `exportar-web`, `web-dev` e `web-build`
- `src/pipeline.py`: chamada do export ao final

Nada do pipeline, do dbt ou do dashboard muda de comportamento.

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Orientação dos anéis da malha quebra o mapa | Teste sobre a orientação, e a correção já conhecida do Streamlit |
| JSON versionado desatualizar em relação ao warehouse | `make exportar-web` refaz o extrato antes de publicar; `gerado_em` no rodapé mostra a idade do extrato |
| Paleta perder contraste no fundo editorial | Revalidar a paleta contra o fundo novo antes de aplicar |
| Crescimento do JSON com mais anos de dados | Colunas enxutas e arredondamento; a cada ano entram ~300 linhas de clima e ~1.400 de safra |
| Páginas pesadas: os dados entram no HTML pré-renderizado, então a home e a de Safra têm ~930 KB crus cada | Comprimidas são 99 KB, dentro do aceitável. Se a safra dobrar de tamanho, o caminho é a página de Safra buscar o JSON em tempo de execução em vez de recebê-lo como prop |
