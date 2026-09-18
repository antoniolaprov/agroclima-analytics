select
    cd_estacao,
    upper(trim(uf))    as uf,
    nome,
    latitude,
    longitude,
    altitude
from {{ source('bronze', 'estacoes') }}
where situacao = 'Operante'
  and fim_operacao is null
