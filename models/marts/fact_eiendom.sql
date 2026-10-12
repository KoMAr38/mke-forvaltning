-- Hovedtallene per region, år og funksjon. Artene ligger som kolonner, ikke som
-- en dimensjon, så netto, korrigert brutto og brutto aldri kan summeres sammen.
-- FGK6 og FGK6a er aggregater og ligger i samme kolonne som delene; er_aggregat i
-- dim_funksjon skiller dem. Østfold 2020-2023 er beregnet fra kommunene (kilde).
with ssb as (
    select
        region_id, aar, funksjon_kode,
        max(case when art_kode = 'AGD2'  then belop_1000kr  end) as netto_1000kr,
        max(case when art_kode = 'AGD4'  then belop_1000kr  end) as korr_brutto_1000kr,
        max(case when art_kode = 'AGD10' then belop_1000kr  end) as brutto_1000kr,
        max(case when art_kode = 'AGD2'  then per_innbygger end) as netto_per_innbygger,
        max(case when art_kode = 'AGD4'  then per_kvm       end) as korr_brutto_per_kvm,
        'SSB' as kilde
    from {{ ref('stg_hovedokonomi') }}
    group by all
),
ostfold as (
    select region_id, aar, funksjon_kode, netto_1000kr, korr_brutto_1000kr, brutto_1000kr,
           netto_per_innbygger, korr_brutto_per_kvm,
           'Beregnet fra de tolv kommunene' as kilde
    from {{ ref('int_ostfold_beregnet') }}
    where aar < 2024
),
alle as (
    select * from ssb
    union all
    select * from ostfold
)
-- NB: For 221, 222 og 261 er SSBs per-innbygger-tall per innbygger i målgruppen
-- (barn 1-5 år, innbyggere 6-15 år, innbyggere 80 år og over), ikke per innbygger.
-- innbyggere: 31.12 i regnskapsåret (tabell 06913), for kommunene og Østfold. Tomt for
-- KOSTRA-gruppen og landet. Brukes til å regne et avvik per innbygger om til kroner.
select
    a.*,
    coalesce(b.innbyggere, o.innbyggere) as innbyggere
from alle a
left join {{ ref('stg_befolkning') }} b
  on b.region_id = a.region_id and b.aar = a.aar
left join (select distinct aar, innbyggere from {{ ref('int_ostfold_beregnet') }}) o
  on a.region_id = 'EKA31' and o.aar = a.aar
where a.netto_1000kr is not null or a.korr_brutto_1000kr is not null
