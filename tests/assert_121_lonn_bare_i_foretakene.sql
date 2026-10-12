-- Kommunekassen i Moss har ingen lønn på funksjon 121 i 2024 og 2025. Lønnen der ligger
-- i foretakene (MKEiendom), så økningen på 121 er foretakets egen føring.
-- Tallet står i README og på metodesiden; endrer SSB det, feiler testen.
select r."Tid" as aar, r.verdi
from {{ raw('detaljregnskap') }} r
where r."KOKkommuneregion0000" = '3103'
  and r."KOKregnskapsomfa0000" = 'B'
  and r."KOKfunksjon0000" = '121'
  and r."KOKart0000" = 'AG16'
  and r."Tid" in ('2024', '2025')
  and coalesce(try_cast(r.verdi as double), -1) <> 0
