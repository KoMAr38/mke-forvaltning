-- De seks regionene i rapporten har eiendomsforvaltning i alt og 121 for hvert år 2020-2025.
-- Fanger et brudd i kommunebroen (30xx -> 31xx) eller et manglende Østfold-år.
with forventet as (
    select r.region_id, a.aar, f.funksjon_kode
    from {{ ref('dim_region') }} r
    cross join {{ ref('dim_aar') }} a
    cross join (values ('FGK6a'), ('121')) f(funksjon_kode)
    where r.i_utvalg
)
select fv.*
from forventet fv
left join {{ ref('fact_eiendom') }} e using (region_id, aar, funksjon_kode)
where e.netto_per_innbygger is null
