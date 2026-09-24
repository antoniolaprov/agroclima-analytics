# Site do AgroClima Analytics

Site estatico em Next.js que mostra os resultados do pipeline. Nao ha backend
nem banco: os dados vem de `public/data`, um extrato das tabelas Gold gerado por
`python scripts/exportar_web.py` na raiz do repositorio e versionado junto com o
codigo.

```
npm install
npm run dev      # http://localhost:3000
npm test         # vitest
npm run build    # gera out/
```

Para atualizar os dados depois de rodar o pipeline:

```
cd .. && make exportar-web
```

O export nao roda sozinho na execucao diaria do Airflow. Publicar e uma decisao
de quem mantem, entao os JSON so mudam quando alguem roda o comando e commita o
resultado.

## Estrutura

- `app/` - rotas do App Router; cada pagina so carrega os JSON e passa como prop
- `src/paginas/` - os componentes de cada pagina, que e onde mora a logica
- `src/graficos/` - involucros sobre Recharts e o mapa em SVG com `d3-geo`
- `src/filtros/` - selecao de UF, cultura e periodo, com o estado na URL
- `src/layout/` - cabecalho, rodape e a casca das secoes
- `src/lib/` - carga dos dados, formatacao, paleta e calculos
- `public/data/` - o extrato versionado, mais a malha das UFs do IBGE

## Notas

**A malha do IBGE segue a RFC 7946**, com o anel externo em sentido
anti-horario, e o `d3-geo` espera o contrario: sem inverter os aneis o mapa
inteiro e pintado de uma cor so. A inversao esta em `src/graficos/mapa.ts` e
`mapa.test.ts` a cobre contra o arquivo real, nao contra um poligono de exemplo.

**Teste verde nao garante tela certa.** Os graficos do Recharts desenham grade e
eixos mesmo sem dado nenhum, entao os testes afirmam geometria (quantas curvas,
quantas barras, `d` preenchido) e nao a presenca de um `<svg>`. Antes de
publicar, abra as tres paginas no navegador.

**`null` e ausencia e nunca vira zero.** Chuva de mes incompleto e variacao sem
ano anterior chegam como `null`; a curva fica partida, a barra nao aparece e o
mapa pinta cinza, que e diferente do verde mais claro.
