-- 12559 Hovedøkonomi. Én rad per region, år, funksjon og art med tre målinger side om side.
-- Gamle 30xx-nummer (2020-2023) føres til dagens 31xx-nummer via kommune_bro.
select
    b.region_id,
    r."Tid"::int                                   as aar,
    r."KOKfunksjon0000"                            as funksjon_kode,
    r."KOKart0000"                                 as art_kode,
    max(case when r.statistikkvariabel = 'KOSbelop0000'         then try_cast(r.verdi as double) end) as belop_1000kr,
    max(case when r.statistikkvariabel = 'KOSbelopperinnby0000' then try_cast(r.verdi as double) end) as per_innbygger,
    max(case when r.statistikkvariabel = 'KOSbelopperkvm0000'   then try_cast(r.verdi as double) end) as per_kvm
from {{ raw('hovedokonomi') }} r
join {{ ref('kommune_bro') }} b
  on b.ssb_kode = r."KOKkommuneregion0000"
 and r."Tid"::int between b.fra_aar and b.til_aar
group by all
