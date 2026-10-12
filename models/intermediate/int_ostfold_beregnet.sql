-- Østfold fylke finnes som KOSTRA-region først fra 2024 (2020-2023 lå kommunene i Viken).
-- Her bygges fylket opp av de tolv kommunene for alle år, slik SSB gjør det:
-- sum kroner delt på sum innbyggere eller sum areal.
-- 2024-2025 brukes bare til testen mot SSBs egne EKA31-tall (assert_ostfold_som_ssb).
with kommuner as (
    select region_id from {{ ref('region') }} where region_type = 'kommune'
),
hoved as (
    select aar, funksjon_kode,
           sum(case when art_kode = 'AGD2'  then belop_1000kr end) as netto_1000kr,
           sum(case when art_kode = 'AGD4'  then belop_1000kr end) as korr_brutto_1000kr,
           sum(case when art_kode = 'AGD10' then belop_1000kr end) as brutto_1000kr
    from {{ ref('stg_hovedokonomi') }}
    where region_id in (select region_id from kommuner)
    group by all
),
innb as (
    select aar, sum(innbyggere) as innbyggere
    from {{ ref('stg_befolkning') }}
    where region_id in (select region_id from kommuner)
    group by all
),
areal as (
    select aar, funksjon_kode,
           sum(areal_eid) as areal_eid, sum(areal_samlet) as areal_samlet
    from {{ ref('stg_areal') }}
    where region_id in (select region_id from kommuner)
    group by all
)
select
    'EKA31'                as region_id,
    h.aar,
    h.funksjon_kode,
    h.netto_1000kr,
    h.korr_brutto_1000kr,
    h.brutto_1000kr,
    i.innbyggere,
    -- 121 og aggregatene måles mot formålsbyggenes samlede areal, som hos SSB
    coalesce(a.areal_samlet, af.areal_samlet)                        as areal_samlet,
    round(h.netto_1000kr * 1000 / i.innbyggere, 1)                   as netto_per_innbygger,
    round(h.korr_brutto_1000kr * 1000 / coalesce(a.areal_samlet, af.areal_samlet), 1) as korr_brutto_per_kvm
from hoved h
join innb i using (aar)
left join areal a  on a.aar = h.aar and a.funksjon_kode = h.funksjon_kode
left join areal af on af.aar = h.aar and af.funksjon_kode = 'FGK6'
