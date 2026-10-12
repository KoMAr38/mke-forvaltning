# Start her

## Krav

- Python 3.11 eller nyere, og `pip install -r requirements.txt`
- Power BI Desktop fra 2026. Prosjektet er lagret som PBIP med TMDL og PBIR.
  I eldre versjoner må preview-innstillingene for PBIP, TMDL og PBIR være slått
  på under **File → Options and settings → Options → Preview features**.
- Prosjektet forventes å ligge i `C:\prosjekt\mke-forvaltning\`

## Kjøre pipelinen

| Fil | Gjør | Tid |
|---|---|---|
| `1_HENT.bat` | Henter fem SSB-tabeller til `data/raw/ssb/` | ~15 s |
| `2_BYGG.bat` | `dbt seed`, `dbt run`, `dbt test` og eksport til `data/mart/` | ~30 s |
| `3_LAG_RAPPORT.bat` | Skriver modellen, bakgrunnsbildene og rapporten på nytt fra `src/powerbi/`. Trengs bare hvis du endrer koden der | ~15 s |

Forventet sluttlinje fra `dbt test` i `2_BYGG.bat`:

```
Done. PASS=30 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=30
```

`data/raw/ssb/` og `data/mart/` ligger i repoet, så rapporten kan åpnes uten
å kjøre noe. `1_HENT.bat` overskriver råfilene med ferske tall. Reviderer SSB
tallene, feiler `assert_kontrolltall`, og README må oppdateres.

`3_LAG_RAPPORT.bat` overskriver det som er lagret fra Power BI Desktop. Lukk
Desktop før du kjører den.

## Åpne i Power BI

1. Åpne `powerbi\MKE_Eiendomsforvaltning.pbip`
2. Ligger prosjektet et annet sted enn `C:\prosjekt\mke-forvaltning\`:
   **Home → Transform data → Edit parameters** og sett `MartMappe` til full
   sti med `\` på slutten, for eksempel `D:\kode\mke-forvaltning\data\mart\`
3. **Home → Refresh**

Årsvelgeren øverst til høyre på Oversikt og Bygg og energi står på 2025.
Siden Funksjon 121 viser alltid endringen fra 2024 til 2025. Tidslinjene
viser alltid 2020–2025.

Uten Power BI kan rapporten leses i `docs/rapport.pdf`.
