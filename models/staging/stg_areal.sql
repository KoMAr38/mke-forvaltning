-- 11906 Areal. samlet = eid + leid, ligger i samme kolonne i kilden.
select
    b.region_id,
    r."Tid"::int                    as aar,
    r."KOKfunksjon0000"             as funksjon_kode,
    max(case when r."KOKeieform0000" = 'eid'    then try_cast(r.verdi as double) end) as areal_eid,
    max(case when r."KOKeieform0000" = 'leid'   then try_cast(r.verdi as double) end) as areal_leid,
    max(case when r."KOKeieform0000" = 'samlet' then try_cast(r.verdi as double) end) as areal_samlet
from {{ raw('areal') }} r
join {{ ref('kommune_bro') }} b
  on b.ssb_kode = r."KOKkommuneregion0000"
 and r."Tid"::int between b.fra_aar and b.til_aar
group by all
