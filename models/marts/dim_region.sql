-- kart_x/kart_y: tyngdepunktet til kommunens største sammenhengende flate, i grader,
-- lengdegrad skalert med cos(59,3°) slik at kartet ikke blir strukket. Grenser: Kartverket via robhop/fylker-og-kommuner, CC BY 4.0.
select region_id, region_navn, region_type, i_utvalg::boolean as i_utvalg, sortering, farge,
       kart_x, kart_y
from {{ ref('region') }}
