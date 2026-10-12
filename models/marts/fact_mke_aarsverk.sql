-- Årsverk i MKEiendom per 31.12, fra Moss kommunes årsrapporter (tabellen «Oversikt årsverk»).
-- Ledige stillinger og lærlinger er ikke med. Viser at bemanningen var stabil da lønnen på 121 økte.
select aar, aarsverk, kilde from {{ ref('mke_aarsverk') }}
where aar between 2020 and 2025
