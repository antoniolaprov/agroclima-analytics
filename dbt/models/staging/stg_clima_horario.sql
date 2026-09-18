select
    cd_estacao,
    upper(trim(uf)) as uf,
    cast(data as date) as data,
    hora_utc,
    precipitacao,
    temperatura,
    temperatura_max,
    temperatura_min,
    umidade,
    vento_velocidade
from {{ source('bronze', 'clima_horario') }}
