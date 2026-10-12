-- Samme oppbygging for FDV-tabellen (12905). Kroner per m² her bruker EID areal.
with kommuner as (
    select region_id from {{ ref('region') }} where region_type = 'kommune'
)
select
    'EKA31' as region_id,
    f.aar,
    f.funksjon_kode,
    f.art_kode,
    sum(f.belop_1000kr)                                          as belop_1000kr,
    round(sum(f.belop_1000kr) * 1000 / max(a.areal_eid), 1)      as per_kvm
from {{ ref('stg_fdv') }} f
join (
    select aar, funksjon_kode, sum(areal_eid) as areal_eid
    from {{ ref('stg_areal') }}
    where region_id in (select region_id from kommuner)
    group by all
) a on a.aar = f.aar and a.funksjon_kode = f.funksjon_kode
where f.region_id in (select region_id from kommuner)
group by all
