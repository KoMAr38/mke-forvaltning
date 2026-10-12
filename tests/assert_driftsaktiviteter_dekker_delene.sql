{{ config(severity = 'warn') }}
-- Driftsaktiviteter (AGD39) skal inneholde energi (AG1) og renhold (AGD38).
-- Kommuner som fører renhold eller energi utenfor driftsaktivitetene, bryter regelen.
-- Advarsel, ikke feil: det er kildedata, og drift ellers blir da negativ for den raden.
select region_id, aar, funksjon_kode, driftsaktiviteter_1000kr, energi_1000kr, renhold_1000kr
from {{ ref('fact_fdv') }}
where driftsaktiviteter_1000kr + 1 < energi_1000kr + renhold_1000kr
