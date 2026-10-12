-- Kontrolltallene i README, alle 18 cellene i tabellen. Endrer SSB tallene, feiler
-- testen, og README må oppdateres.
with k(maal, region_id, aar, forventet) as (
    values
        ('eiendom_per_innbygger', '3103',  2025, 5666.0),
        ('eiendom_per_innbygger', 'EKG11', 2025, 6268.4),
        ('eiendom_per_innbygger', 'EKA31', 2025, 5836.2),
        ('f121_per_innbygger',    '3103',  2025,  692.7),
        ('f121_per_innbygger',    'EKG11', 2025,  336.1),
        ('f121_per_innbygger',    'EKA31', 2025,  420.4),
        ('f121_per_innbygger',    '3103',  2024,  432.0),
        ('f121_per_innbygger',    'EKG11', 2024,  300.5),
        ('f121_per_innbygger',    'EKA31', 2024,  407.1),
        ('formaalsbygg_per_kvm',  '3103',  2025, 1475.7),
        ('formaalsbygg_per_kvm',  'EKG11', 2025, 1508.8),
        ('formaalsbygg_per_kvm',  'EKA31', 2025, 1343.1),
        ('energi_per_kvm',        '3103',  2025,  137.4),
        ('energi_per_kvm',        'EKG11', 2025,  145.8),
        ('energi_per_kvm',        'EKA31', 2025,  156.9),
        ('vedlikehold_per_kvm',   '3103',  2025,  267.5),
        ('vedlikehold_per_kvm',   'EKG11', 2025,  163.8),
        ('vedlikehold_per_kvm',   'EKA31', 2025,  113.0)
),
faktisk as (
    select 'eiendom_per_innbygger' as maal, region_id, aar, netto_per_innbygger as verdi
    from {{ ref('fact_eiendom') }} where funksjon_kode = 'FGK6a'
    union all
    select 'f121_per_innbygger', region_id, aar, netto_per_innbygger
    from {{ ref('fact_eiendom') }} where funksjon_kode = '121'
    union all
    select 'formaalsbygg_per_kvm', region_id, aar, korr_brutto_per_kvm
    from {{ ref('fact_eiendom') }} where funksjon_kode = 'FGK6'
    union all
    select 'energi_per_kvm', region_id, aar, energi_per_kvm
    from {{ ref('fact_fdv') }} where funksjon_kode = 'FGK6'
    union all
    select 'vedlikehold_per_kvm', region_id, aar, vedlikehold_per_kvm
    from {{ ref('fact_fdv') }} where funksjon_kode = 'FGK6'
)
select k.*, f.verdi
from k
left join faktisk f using (maal, region_id, aar)
where f.verdi is null or round(f.verdi, 1) <> k.forventet
