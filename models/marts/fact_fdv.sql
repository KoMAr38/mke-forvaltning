-- Forvaltning, drift og vedlikehold per region, år og funksjon (tabell 12905).
-- Driftsaktiviteter (AGD39) inneholder energi og renhold. Drift ellers er resten.
-- Kroner per m² bruker eid areal, som hos SSB. Østfold 2020-2023 er beregnet.
with f as (
    select region_id, aar, funksjon_kode, art_kode, belop_1000kr, per_kvm, 'SSB' as kilde
    from {{ ref('stg_fdv') }}
    union all
    select region_id, aar, funksjon_kode, art_kode, belop_1000kr, per_kvm, 'Beregnet fra de tolv kommunene'
    from {{ ref('int_ostfold_fdv_beregnet') }}
    where aar < 2024
),
bred as (
    select
        region_id, aar, funksjon_kode, max(kilde) as kilde,
        max(case when art_kode = 'AG1'   then belop_1000kr end) as energi_1000kr,
        max(case when art_kode = 'AGD38' then belop_1000kr end) as renhold_1000kr,
        max(case when art_kode = 'AGD39' then belop_1000kr end) as driftsaktiviteter_1000kr,
        max(case when art_kode = 'AGD36' then belop_1000kr end) as vedlikehold_1000kr,
        max(case when art_kode = 'AGD8'  then belop_1000kr end) as fdv_eide_bygg_1000kr,
        max(case when art_kode = 'AG1'   then per_kvm end)      as energi_per_kvm,
        max(case when art_kode = 'AGD38' then per_kvm end)      as renhold_per_kvm,
        max(case when art_kode = 'AGD39' then per_kvm end)      as driftsaktiviteter_per_kvm,
        max(case when art_kode = 'AGD36' then per_kvm end)      as vedlikehold_per_kvm,
        max(case when art_kode = 'AGD8'  then per_kvm end)      as fdv_eide_bygg_per_kvm
    from f
    group by all
)
select
    b.*,
    b.driftsaktiviteter_per_kvm - b.energi_per_kvm - b.renhold_per_kvm as drift_ellers_per_kvm,
    a.areal_eid, a.areal_leid, a.areal_samlet
from bred b
left join (
    select * from {{ ref('stg_areal') }}
    union all
    select 'EKA31', aar, funksjon_kode, sum(areal_eid), sum(areal_leid), sum(areal_samlet)
    from {{ ref('stg_areal') }}
    where aar < 2024 and region_id in (select region_id from {{ ref('region') }} where region_type = 'kommune')
    group by all
) a using (region_id, aar, funksjon_kode)
where b.energi_1000kr is not null or b.fdv_eide_bygg_1000kr is not null
