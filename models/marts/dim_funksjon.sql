select funksjon_kode, funksjon_navn, funksjon_kort, funksjon_gruppe, er_aggregat::boolean as er_aggregat, sortering
from {{ ref('funksjon') }}
