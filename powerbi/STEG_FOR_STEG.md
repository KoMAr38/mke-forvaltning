# Power BI – byggelogg

Denne filen trengs ikke for å bruke prosjektet; det står i `START_HER.md`.
Den er en logg over hvordan modellen og rapporten ble bygd, og hva som ikke
virket på første forsøk.

---

## 1. Filene

| Mappe | Innhold |
|---|---|
| `MKE_Eiendomsforvaltning.pbip` | Det som åpnes i Desktop. Peker på rapporten |
| `MKE_Eiendomsforvaltning.SemanticModel/definition/` | Modellen som TMDL: én fil per tabell, `relationships.tmdl`, `expressions.tmdl` (parameteren `MartMappe` og funksjonen `fnLesCsv`) og `cultures/nb-NO.tmdl` |
| `MKE_Eiendomsforvaltning.Report/definition/` | Rapporten som PBIR: én mappe per side og én `visual.json` per visual, 92 i alt |
| `MKE_Eiendomsforvaltning.Report/StaticResources/` | Temaet `Nordlys-mke` og ett bakgrunnsbilde per side |

Modellen og rapporten er ikke skrevet for hånd. `src/powerbi/lag_modell.py`
skriver TMDL, `lag_bilder.py` tegner bakgrunnsbildene med Pillow og
`lag_rapport.py` skriver PBIR. Koordinatene til kort og paneler står ett sted,
i `src/powerbi/layout.py`, så bakgrunnen og visualene alltid ligger likt.
`3_LAG_RAPPORT.bat` kjører alle tre.

`.pbi/localSettings.json` og `.pbi/cache.abf` (dataene) er utelatt fra git.
Første gang rapporten åpnes, er den derfor tom til du trykker **Refresh**.

---

## 2. Parameter og spørringer

| Navn | Type | Verdi |
|---|---|---|
| `MartMappe` | Text | `C:\prosjekt\mke-forvaltning\data\mart\` |

`fnLesCsv(Filnavn)` leser én CSV fra `MartMappe` (UTF-8, komma som
skilletegn) og bruker første rad som overskrifter. Hver tabell velger
kolonnene den trenger og setter typene med kulturen `"en-US"`, fordi CSV-ene
har punktum som desimaltegn:

```
let
    Kilde = fnLesCsv("fact_eiendom.csv"),
    Kolonner = Table.SelectColumns(Kilde, {"region_id", "aar", "funksjon_kode", ...}),
    Typer = Table.TransformColumnTypes(Kolonner, {{"region_id", type text}, {"aar", Int64.Type}, ...}, "en-US")
in
    Typer
```

All logikk ligger i dbt. Power Query leser bare filene.

---

## 3. Modell

### Tabeller

| Tabell | Rader | Rolle |
|---|---|---|
| `dim_region` | 15 | De tolv kommunene i Østfold, KOSTRA-gruppe 11, Østfold og landet, med farge, sortering og kartkoordinater |
| `dim_aar` | 6 | 2020–2025 |
| `dim_funksjon` | 9 | 121, de seks formålsbyggene og aggregatene FGK6 og FGK6a, merket med `Er aggregat` |
| `fact_eiendom` | 810 | Tabell 12559: netto, korrigert brutto og brutto, per innbygger og per m² |
| `fact_art` | 3 010 | Tabell 12367: beløp per art, med lønn, pensjon og arbeidsgiveravgift merket som personal |
| `fact_fdv` | 630 | Tabell 12905 og 11906: energi, renhold, drift og vedlikehold per m², og arealet |
| `fact_mke_aarsverk` | 4 | Årsverk i MKEiendom 2022–2025 |
| `_Mål` | – | 65 mål i ni visningsmapper |

Ti relasjoner, alle mange-til-én med filter én vei. Faktatabellene kobles på
region, år og funksjon; `fact_mke_aarsverk` bare på år. Tallkolonnene i
faktatabellene er skjult, så rapporten og den som utforsker modellen, går
gjennom målene.

### Mål

**Kroner summerer bare funksjonene.** FGK6 og FGK6a ligger i samme kolonne
som funksjonene de består av. Kronemålene filtrerer bort aggregatene, så
ingenting telles to ganger:

```
Korrigerte brutto (mill.) =
DIVIDE (
    CALCULATE ( SUM ( fact_eiendom[korr_brutto_1000kr] ), KEEPFILTERS ( dim_funksjon[Er aggregat] = FALSE () ) ),
    1000
)
```

**Per innbygger og per m² er SSBs egne tall**, bortsett fra Østfold
2020–2023, som dbt regner ut fra kommunene. De kan ikke summeres over
regioner eller år, så målene viser verdien bare når én region og ett år er
valgt, og er tomme ellers. Formålsbygg per innbygger er FGK6a minus 121, fordi
SSB ikke publiserer FGK6 per innbygger.

**Endring mot året før** finner året i filteret og trekker fra året før:

```
Endring mot året før (mill.) =
VAR _Aar = SELECTEDVALUE ( dim_aar[År] )
RETURN
    IF ( NOT ISBLANK ( _Aar ),
        [Korrigerte brutto (mill.)] - CALCULATE ( [Korrigerte brutto (mill.)], dim_aar[År] = _Aar - 1 ) )
```

Fossefallet per funksjon bruker dette målet. Fossefallet per art bruker
`Endring art (mill.)`, som er bygd likt på `fact_art`. Fordi artene summerer
til korrigerte brutto, ender begge på samme total.

**Kortene** henter Moss og gruppen med et fast filter på regionen, for
eksempel `CALCULATE ( [Energi kr per m²], dim_region[region_id] = "3103" )`.
Linjen under tallet er et skjult tekstmål med retning, prosent og gruppens
tall i én tekst, så den stemmer for hvert år som velges.

**Kontrollene** står på Metode-siden og skal være 0: de sju funksjonene mot
SSBs FGK6a, og summen over artene (tabell 12367) mot korrigerte brutto
(tabell 12559). Den andre kontrollen sammenligner to ulike SSB-tabeller som
skal gi samme tall.

---

## 4. Rapporten

- **Fire sider i 1920 × 1080** med *Fit to page*: Oversikt, Funksjon 121,
  Bygg og energi og Metode.
- **Temaet `Nordlys-mke`** bygger på Fluent 2: mørk bakgrunn, og hver region
  har samme farge på alle sider. Moss er turkis, KOSTRA-gruppe 11 gull,
  Østfold indigo. Fargene kommer fra `seeds/region.csv`. I de to
  stolpediagrammene på Oversikt er nabobyene grå, så de tre som sammenlignes
  skiller seg ut. Moss har tykkest linje (4 px), gruppen og fylket 3 px,
  nabobyene 2 px.
- **Bakgrunnsbilder per side.** Paneler, sidemeny, ikoner og rammene rundt
  kortene er tegnet i ett bilde per side (`bg-*.png`), og visualene ligger
  oppå med gjennomsiktig bakgrunn. Bildet er satt som sidebakgrunn og ikke
  som *wallpaper*, ellers mangler det i PDF-en.
- **Sidemenyen** er fire knapper med sidenavigasjon lagt over ikonene i
  bakgrunnsbildet.
- **Årsvelgeren** er en knappeslicer, synkronisert mellom Oversikt og Bygg og
  energi. Linjediagrammene på de to sidene har interaksjonen *None* fra
  sliceren, så de viser alle årene.
- **Funksjon 121 er låst til 2025.** Kortene og fossefallene har et
  visualfilter på `dim_aar[År] = 2025`, og bakgrunnen viser «Fast periode
  2024 → 2025» der årsvelgeren står på de andre sidene.
- **Fossefallene** viser endringen fra 2024 til 2025, det ene per art og det
  andre per funksjon. Idrettsbygg står med −0,0. Endringen var −47 000 kr, og
  stolpen er beholdt så alle seks byggene er med.
- **Personal og årsverk** er et kombinert diagram: søylene er
  personalkostnadene på 121 og byggene, linjen årsverkene i MKEiendom på
  sekundæraksen.
- **Norsk tallformat.** `report.json` har `"locale": "nb-NO"` og
  `"defaultDisplayUnitsToNone": true`.
- **Bildene i README** kommer fra **File → Export → Export to PDF** i Desktop
  (`docs/rapport.pdf`). PDF-siden er 1476 × 846 punkt med hvit marg. Hver side
  er gjort om til PNG med `pdftoppm` på 200 dpi, margen er skåret bort og
  bildet skalert til 1600 × 900. Skjermbilder fra Desktop blir bleke på en
  HDR-skjerm, så de er ikke brukt. Desktop legger PDF-en i
  `%TEMP%\Power BI Desktop\print-job-<guid>\`.

### Kartet på Oversikt

Kartet er et punktdiagram, ikke et kartvisual. Kommunegrensene fra
Kartverket er tegnet i bakgrunnsbildet, i en rute på 444 × 620 piksler.
Punktdiagrammet ligger i samme rute. Slik treffer punktene kommunene:

1. Aksene har faste grenser, de samme som kartet ble tegnet med:
   x 5,37–6,075 og y 58,83–59,815.
2. X er lengdegraden ganget med cos(59,3°), y er breddegraden. Da får en
   kilometer øst–vest og en kilometer nord–sør samme lengde på kartet.
3. Hvert punkt står i tyngdepunktet til kommunens største sammenhengende
   flate (`Kart X` og `Kart Y` i `dim_region`).

Størrelsen er eiendomsforvaltning per innbygger. Målet `Farge kart` gir Moss
turkis. Kommuner som bruker mer enn Moss, blir rosa, og de som bruker mindre,
blir indigo. Kommunenavnene er tegnet i bakgrunnen, hver med sin egen
forskyvning, så de ikke havner under punktene.

---

## 5. Kontroll i Desktop

- PBIR-mappen er validert mot skjemaene for PBIR: 0 feil og 0 advarsler.
- Rapporten er åpnet i Desktop, oppdatert og gått gjennom side for side.
  Påstandene i overskriftene er kontrollert mot dataene for alle seks år.
- Kontrolltallene i README er sjekket med DAX-spørringer mot modellen i
  Desktop. Målene gir de samme tallene som dbt, og begge kontrollmålene er 0.

---

## 6. Det som ikke virket på første forsøk

1. **K og M i kortene.** Kortene viste «6K» i stedet for 5 666, og «19.0
   mill.» med punktum. Løst med `locale` og `defaultDisplayUnitsToNone` i
   `report.json`, og med « kr» og « mill. kr» i formatstrengene.
2. **Rullefelt i stolpediagrammet.** Seks regioner med to mål hver ble for
   høyt for panelet, og Halden forsvant under et rullefelt. Nå er det to små
   diagrammer med ett mål hver: 121 og formålsbyggene.
3. **For store bobler på kartet.** I full størrelse dekket boblene
   kommunenavnene og hverandre. Boblestørrelse −20 (*Markers* i
   Format-ruten) passet, og navnene ble flyttet i bakgrunnsbildet.
4. **Årsverkene i det kombinerte diagrammet.** Tallene på årsverkslinjen
   hadde desimaler, og noen ble skjult bak søylene. Nå er søylene klynget og
   aksene låst (0–160 mill. kr og 0–66 årsverk), så linjen ligger over
   søylene. Tallene på linjen har null desimaler og står over punktene.
5. **Overskrifter som bare stemte for ett år.** Overskriftene på Funksjon
   121 handler om 2025-regnskapet og ble feil når et annet år var valgt.
   Siden mistet årsvelgeren og fikk fast periode, se avsnitt 4. På Bygg og
   energi lå Moss 8,2 % over gruppen per m² i 2020, så overskriften der sier
   nå «siden 2021».
6. **Mål ingen brukte.** Etter endringene over lå ni mål igjen som verken en
   visual eller et annet mål brukte. De er fjernet, og modellen har 65 mål.
   Tre grunnmål uten visual er beholdt for den som vil utforske modellen:
   121 i kroner og per m², og formålsbyggene i kroner.

---

## Kilder

- Microsoft Learn: [Power BI Desktop project semantic model folder](https://learn.microsoft.com/power-bi/developer/projects/projects-dataset) (TMDL)
- Microsoft Learn: [Power BI Desktop project report folder](https://learn.microsoft.com/power-bi/developer/projects/projects-report) (PBIR)
- Microsoft Learn: [Change how visuals interact in a Power BI report](https://learn.microsoft.com/power-bi/create-reports/service-reports-visual-interactions)
- Microsoft Learn: [Export Power BI reports to PDF](https://learn.microsoft.com/power-bi/collaborate-share/end-user-pdf)
- Fabric Community: [PDF Export temporary folder](https://community.fabric.microsoft.com/t5/Desktop/PDF-Export-temporary-folder/m-p/3142296)
