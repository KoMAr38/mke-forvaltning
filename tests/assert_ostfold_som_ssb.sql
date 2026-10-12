-- Østfold 2020-2023 er bygget opp av kommunene. Samme beregning for 2024-2025, da SSB
-- selv publiserer fylket, må gi SSBs tall. Tillatt avvik: 1 kr per innbygger (SSB bruker
-- et befolkningstall som avviker med rundt 30 personer fra tabell 06913 for 2025)
-- og 0,1 kr per m² (avrunding).
select b.aar, b.funksjon_kode,
       b.netto_per_innbygger, s.netto_per_innbygger as ssb_innb,
       b.korr_brutto_per_kvm, s.korr_brutto_per_kvm as ssb_kvm
from {{ ref('int_ostfold_beregnet') }} b
join {{ ref('fact_eiendom') }} s
  on s.region_id = 'EKA31' and s.aar = b.aar and s.funksjon_kode = b.funksjon_kode and s.kilde = 'SSB'
where b.aar >= 2024
  and (   (b.funksjon_kode in ('121', '130', '381', '386', 'FGK6a')
           and abs(b.netto_per_innbygger - s.netto_per_innbygger) > 1)
       or abs(b.korr_brutto_per_kvm - s.korr_brutto_per_kvm) > 0.1)
