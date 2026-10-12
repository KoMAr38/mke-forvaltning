-- Artsgruppene i fact_art summerer til korrigerte brutto driftsutgifter (AGD4).
-- Summen holdes mot tabell 12559, en annen SSB-tabell enn den artene kommer fra.
-- Landet er unntatt: landsraden for 2024 skiller seg mellom de to tabellene med under
-- 0,01 prosent i sum og under 0,02 prosent per funksjon (ulik publiseringsdato hos
-- SSB). Landet brukes ikke i rapporten.
with art as (
    select region_id, aar, funksjon_kode, sum(belop_1000kr) as sum_art
    from {{ ref('fact_art') }} group by all
)
select a.*, e.korr_brutto_1000kr
from art a
join {{ ref('fact_eiendom') }} e using (region_id, aar, funksjon_kode)
where abs(a.sum_art - e.korr_brutto_1000kr) > 0.5
  and a.region_id <> 'EAK'
