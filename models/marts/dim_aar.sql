select aar, aar::varchar as aar_tekst, (aar = max(aar) over ()) as er_siste_aar
from range(2020, 2026) t(aar)
