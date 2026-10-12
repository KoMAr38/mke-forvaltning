-- 12905 Forvaltning, drift og vedlikehold. Kroner per m² her bruker EID areal.
select
    b.region_id,
    r."Tid"::int                    as aar,
    r."KOKfunksjon0000"             as funksjon_kode,
    r."KOKart0000"                  as art_kode,
    max(case when r.statistikkvariabel = 'KOSbelop0000'       then try_cast(r.verdi as double) end) as belop_1000kr,
    max(case when r.statistikkvariabel = 'KOSbelopperkvm0000' then try_cast(r.verdi as double) end) as per_kvm
from {{ raw('fdv') }} r
join {{ ref('kommune_bro') }} b
  on b.ssb_kode = r."KOKkommuneregion0000"
 and r."Tid"::int between b.fra_aar and b.til_aar
group by all
