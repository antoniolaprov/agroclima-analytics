-- stg_clima_diario nao deve descartar leituras horarias validas so porque a
-- estacao correspondente e filtrada por stg_estacoes (situacao != 'Operante'
-- ou fim_operacao preenchido). A004 fica de fora de stg_estacoes; ainda assim
-- seu historico horario (20 horas em 2026-01-01, acima do corte de 18)
-- precisa aparecer em stg_clima_diario.
-- O teste falha (retorna linha) se o dia esperado nao estiver presente.
select 1 as estacao_ausente
where not exists (
    select 1
    from {{ ref('stg_clima_diario') }}
    where cd_estacao = 'A004'
      and data = date '2026-01-01'
)
