# AgroClima Analytics — Modelo de anomalia de rendimento

Data: 2026-11-03

## 1. Pergunta

A página Clima x Safra mostra a correlação entre a chuva do ciclo e o
rendimento. A correlação descreve a amostra, mas não responde a pergunta que
interessa a quem planeja: **dado o clima observado até agora no ciclo, quanto
a safra vai render em relação ao esperado?** O modelo responde isso por
estado e cultura, meses antes de o IBGE publicar a PAM (a PAM de um ano sai
em setembro do ano seguinte).

## 2. Alvo

O rendimento cru é dominado pela tendência tecnológica. Soja em MT rende hoje
quase o dobro do que rendia nos anos 90; um modelo que acertasse só essa
tendência teria R² alto e não diria nada sobre clima. O alvo é a anomalia:

```
anomalia(t) = log(rendimento(t)) - tendência(t)
```

`tendência(t)` é uma reta ajustada no log do rendimento dos 15 anos
anteriores a `t` (mínimo de 8). A janela anda com o ano, então a tendência de
2010 não vê nada depois de 2009. O jeito mais comum, ajustar uma curva na
série inteira e subtrair, usa o rendimento de 2025 para definir a anomalia de
2010 e invalida a validação temporal.

Em log, a anomalia é aproximadamente a variação percentual: −0,10 é uma safra
cerca de 10% abaixo do esperado.

## 3. Variáveis

O ciclo de cada cultura (`dbt/seeds/ciclo_cultura.csv`) é dividido em três
fases de mesmo tamanho. Para cada fase observada:

| variável | o que é |
|---|---|
| `chuva_fN` | chuva acumulada (mm) |
| `chuva_rel_fN` | chuva em relação à normal da UF naqueles meses (−0,3 = 30% abaixo) |
| `temp_fN`, `tmax_fN` | temperatura média e máxima |
| `anom_temp_fN` | temperatura menos a normal |
| `secos_fN` | dias com chuva média da UF abaixo de 1 mm |

Mais os mesmos agregados no ciclo observado (`*_total`), o pior mês em relação
à normal (`pior_mes_rel`, para veranicos que a soma dilui), a anomalia da
safra anterior, a cultura e a UF.

As normais usam só os anos anteriores (mínimo de 5). As anomalias de
`gold_clima_uf_mensal` usam a janela inteira e por isso não entram no modelo.

**Fora de propósito:** a área colhida e a área plantada do ano. As duas saem
na mesma publicação da PAM que o rendimento, e a área colhida cai justamente
nas safras que quebram. Usá-las seria prever o rendimento com um número que
só existe depois dele.

## 4. Horizonte

`horizonte = 1, 2 ou 3` é o número de fases já observadas. O treino gera um
modelo por horizonte (`modelo_h1`, `modelo_h2`, `modelo_h3`), e `prever`
usa, para cada safra ainda não publicada, o maior horizonte que o clima
disponível permite. A comparação entre horizontes responde quando, no ciclo,
o clima passa a dizer alguma coisa sobre a safra.

## 5. Validação

Rolling origin por ano: para cada ano de teste `Y`, treino com as safras de
anos `< Y`, previsão das de `Y`. Os cinco primeiros anos com clima completo
ficam só para treino.

Um k-fold embaralhado colocaria safras de 2020 no treino de um modelo
avaliado em 2015. Pior: o clima de um ano é compartilhado por estados
vizinhos (o mesmo El Niño seca o Sul inteiro), então um k-fold por linha
deixaria o modelo ver o "mesmo" evento no treino e no teste.

Métricas:

- **skill** = 1 − MSE / MSE da tendência. Zero é empatar com "a safra segue a
  reta"; negativo é piorar a previsão ingênua.
- **IC 95% do skill** por bootstrap de anos inteiros (2.000 reamostragens).
  Reamostrar linhas soltas ignoraria a correlação entre os erros de um mesmo
  ano e daria um intervalo estreito demais.
- **MAE (kg/ha) e MAPE**, com o rendimento reconstruído por
  `exp(tendência + previsão)`.
- **recall de quebras**: das safras mais de 10% abaixo da tendência, quantas o
  modelo previu pelo menos 5% abaixo.

## 6. Experimentos

Todos sobre as mesmas safras e os mesmos anos de teste:

| experimento | para que serve |
|---|---|
| `tendencia` | referência do skill |
| `persistencia` | repetir a safra anterior: baseline ingênuo comum |
| `ridge` | quanto do sinal é linear |
| `lgbm_sem_clima` | ablação: o que sobra sem clima (UF, cultura, safra anterior) |
| `lgbm_so_clima` | ablação: só clima |
| `lgbm_completo` | modelo final |
| `lgbm_h1`, `lgbm_h2` | o mesmo modelo com 1/3 e 2/3 do ciclo observado |

Os hiperparâmetros do LightGBM são fixos e conservadores (profundidade 4, 25
amostras por folha, perda Huber). Com cerca de dois mil exemplos, uma busca de
hiperparâmetros dentro da validação temporal sobreajustaria a própria
validação. A perda Huber reduz o peso das poucas safras com anomalias
extremas, algumas das quais podem ser erro de registro na PAM.

Os dados sintéticos dos testes (`tests/conftest.py`) têm um efeito conhecido:
a anomalia depende só da chuva da fase 2. Os testes conferem que o pipeline
recupera isso — skill positivo no modelo completo e no horizonte 2, nulo sem
clima e no horizonte 1, e `chuva_rel_f2` no topo dos valores SHAP.

## 7. Manutenção

- O Airflow roda `treinar_modelo` e `prever_safras` depois do dbt. O treino
  calcula um hash das tabelas de entrada e só roda se elas mudaram desde a
  versão atual.
- Cada treino grava uma versão em `data/modelos/<versão>/` com os modelos,
  métricas, previsões do backtest, figuras, relatório e model card.
- **Portão de promoção:** a versão nova só substitui `data/modelos/atual/` se
  o skill não cair mais de 0,02 em relação à atual. Uma PAM com problema ou
  uma mudança de código não troca um modelo bom por um pior sem ninguém ver.
- Com `mlflow-skinny` instalado, cada treino vira um run no MLflow
  (`data/mlruns`, ou `MLFLOW_TRACKING_URI`), com um run filho por experimento.
  `make mlflow` abre a interface.
- `make publicar-hf REPO=usuario/nome` sobe a versão atual para o Hugging Face
  Hub, com o model card gerado no treino.

## 8. Limitações

- Uma safra por estado e ano: a amostra é pequena e os anos de teste são
  poucos. O intervalo do skill é o número a olhar, não o ponto.
- A média estadual da chuva esconde diferenças grandes dentro do estado (o
  oeste e o leste do PR, o norte e o sul de MG), e a média não é ponderada
  pela área plantada.
- A cobertura de estações automáticas do INMET no começo dos anos 2000 era
  bem menor que hoje. Os primeiros anos de cada estado se apoiam em poucas
  estações, e alguns estados só entram na tabela anos depois de 2001
  (`n_estacoes_min` fica na tabela para conferir).
- O modelo não sabe de irrigação, preço, pragas nem mudança de área. A cana e
  o café respondem a clima de mais de um ciclo (o café tem bienalidade), o que
  as três fases de um ciclo não capturam.
- A tendência linear se ajusta mal a séries que mudaram de patamar, como o
  milho segunda safra no Centro-Oeste.
