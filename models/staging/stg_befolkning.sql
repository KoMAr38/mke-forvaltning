-- 06913 Befolkning 1. januar. KOSTRA deler på innbyggere 31.12 i regnskapsåret,
-- altså 1. januar året etter. aar her er derfor regnskapsåret.
-- Nullverdier betyr at nummeret ikke fantes den datoen og forkastes.
select
    b.region_id,
    r."Tid"::int - 1                as aar,
    try_cast(r.verdi as double)     as innbyggere
from {{ raw('befolkning') }} r
join {{ ref('kommune_bro') }} b
  on b.ssb_kode = r."Region"
 and r."Tid"::int between b.fra_aar and b.til_aar   -- nummeret som gjaldt på tellingsdatoen
where try_cast(r.verdi as double) > 0
