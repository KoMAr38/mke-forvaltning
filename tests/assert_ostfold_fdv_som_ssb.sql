-- Samme kontroll for FDV-tabellen: beregnet Østfold mot SSBs EKA31, 2024-2025.
select b.*, s.per_kvm as ssb
from {{ ref('int_ostfold_fdv_beregnet') }} b
join {{ ref('stg_fdv') }} s
  on s.region_id = 'EKA31' and s.aar = b.aar and s.funksjon_kode = b.funksjon_kode and s.art_kode = b.art_kode
where b.aar >= 2024 and abs(b.per_kvm - s.per_kvm) > 0.1
