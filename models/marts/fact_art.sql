-- Korrigerte brutto driftsutgifter (AGD4) brutt ned på art, kommunekonsern.
-- Fire arter er egne grupper: lønn (fratrukket sykelønnsrefusjon), pensjon,
-- arbeidsgiveravgift og kjøp av varer og tjenester. Resten (overføringer, kjøp som
-- erstatter egenproduksjon, merverdiavgift, internt fordelte utgifter m.m.) samles i én
-- rest, slik at gruppene alltid summerer til AGD4. Testen assert_art_lik_hovedtabell
-- holder summen mot tabell 12559.
with d as (
    select * from {{ ref('stg_detaljregnskap') }} where belop_1000kr is not null
),
deler as (
    select d.region_id, d.aar, d.funksjon_kode, g.art_gruppe, g.er_personal, g.sortering,
           d.belop_1000kr
    from d join {{ ref('art_gruppe') }} g on g.art_kode = d.art_kode
),
agd4 as (
    select region_id, aar, funksjon_kode, belop_1000kr as agd4
    from d where art_kode = 'AGD4'
),
rest as (
    select a.region_id, a.aar, a.funksjon_kode,
           'Annet og internt fordelt' as art_gruppe, false as er_personal, 99 as sortering,
           a.agd4 - coalesce(sum(p.belop_1000kr), 0) as belop_1000kr
    from agd4 a
    left join deler p using (region_id, aar, funksjon_kode)
    group by a.region_id, a.aar, a.funksjon_kode, a.agd4
)
select region_id, aar, funksjon_kode, art_gruppe, er_personal::boolean as er_personal, sortering, belop_1000kr
from deler
where (region_id, aar, funksjon_kode) in (select (region_id, aar, funksjon_kode) from agd4)
union all
select * from rest
