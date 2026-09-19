-- temp_media_movel_3m nao deve calcular a media movel de 3 meses somando um
-- mes que nao e cronologicamente adjacente. MG pula junho/2023 no seed de
-- desenvolvimento (scripts/seed_bronze_dev.py); sem uma guarda por indice de
-- mes, julho/2023 encontraria abril/2023 como "2 meses atras" (as 2 linhas
-- fisicas anteriores) e a media incluiria um mes fora da janela real de 3
-- meses. O teste falha (retorna linha) se a media movel de julho/2023 nao
-- bater com a media de maio+julho, os unicos meses dentro do alcance real.
with alvo as (
    select uf, ano, mes, temp_media_movel_3m
    from {{ ref('gold_clima_uf_mensal') }}
    where uf = 'MG' and ano = 2023 and mes = 7
),

vizinhos as (
    select avg(temp_media) as media_esperada
    from {{ ref('gold_clima_uf_mensal') }}
    where uf = 'MG' and ((ano = 2023 and mes = 5) or (ano = 2023 and mes = 7))
)

select a.uf, a.ano, a.mes, a.temp_media_movel_3m, v.media_esperada
from alvo a
cross join vizinhos v
where abs(a.temp_media_movel_3m - v.media_esperada) > 0.001
