-- FGK6a = 121 + FGK6, og FGK6 = de seks formålsbyggene, på netto og korrigert brutto.
-- I tillegg: de sju funksjonene = FGK6a på korrigert brutto, som er det kronemålene
-- i Power BI summerer. Fanger dobbelttelling hvis aggregatene en dag summeres sammen
-- med delene.
with f as (select * from {{ ref('fact_eiendom') }}),
del as (
    select region_id, aar,
        sum(case when funksjon_kode in ('121', 'FGK6') then netto_1000kr end)                                       as netto_121_fgk6,
        sum(case when funksjon_kode in ('130','221','222','261','381','386') then korr_brutto_1000kr end)          as korr_bygg,
        sum(case when funksjon_kode in ('121','130','221','222','261','381','386') then korr_brutto_1000kr end)    as korr_sju,
        max(case when funksjon_kode = 'FGK6a' then netto_1000kr end)                                               as netto_fgk6a,
        max(case when funksjon_kode = 'FGK6'  then korr_brutto_1000kr end)                                         as korr_fgk6,
        max(case when funksjon_kode = 'FGK6a' then korr_brutto_1000kr end)                                         as korr_fgk6a
    from f group by all
)
select * from del
where abs(netto_121_fgk6 - netto_fgk6a) > 1
   or abs(korr_bygg - korr_fgk6) > 1
   or abs(korr_sju - korr_fgk6a) > 1
