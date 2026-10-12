-- 12367 Detaljregnskap, kommunekonsern (MKE er et KF og ligger i konsernet).
select
    b.region_id,
    r."Tid"::int                    as aar,
    r."KOKfunksjon0000"             as funksjon_kode,
    r."KOKart0000"                  as art_kode,
    r."KOKart0000_tekst"            as art_navn,
    try_cast(r.verdi as double)     as belop_1000kr
from {{ raw('detaljregnskap') }} r
join {{ ref('kommune_bro') }} b
  on b.ssb_kode = r."KOKkommuneregion0000"
 and r."Tid"::int between b.fra_aar and b.til_aar
where r."KOKregnskapsomfa0000" = 'A'
