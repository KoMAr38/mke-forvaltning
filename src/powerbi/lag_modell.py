"""
Skriver den semantiske modellen (TMDL) til powerbi/MKE_Eiendomsforvaltning.SemanticModel.

Modellen er skrevet som kode, ikke klikket fram i Desktop, slik at den kan
leses i en diff. lineageTag er uuid5 av objektnavnet, så de er like fra kjøring
til kjøring og Desktop ser ikke nye objekter hver gang skriptet kjøres.
"""
import json
import uuid
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
NAVN = "MKE_Eiendomsforvaltning"
SM = ROT / "powerbi" / f"{NAVN}.SemanticModel"
NS = uuid.UUID("6c1f6a52-1b0e-4c55-9d1b-5e1f3e4a0b21")


def tag(*deler):
    return str(uuid.uuid5(NS, "/".join(deler)))


def q(navn):
    """Sitert TMDL-navn når det trengs."""
    enkelt = navn.replace("_", "").isalnum() and not navn[0].isdigit()
    return navn if enkelt else "'" + navn.replace("'", "''") + "'"


def kolonne(tabell, navn, kilde, typ, *, skjult=False, fmt=None, beskrivelse=None,
            sorter=None, kategori=None):
    linjer = []
    if beskrivelse:
        linjer.append(f"\t/// {beskrivelse}")
    linjer.append(f"\tcolumn {q(navn)}")
    linjer.append(f"\t\tdataType: {typ}")
    if skjult:
        linjer.append("\t\tisHidden")
    if fmt:
        linjer.append(f"\t\tformatString: {fmt}")
    linjer.append(f"\t\tlineageTag: {tag(tabell, 'kol', navn)}")
    if kategori:
        linjer.append(f"\t\tdataCategory: {kategori}")
    linjer.append("\t\tsummarizeBy: none")
    linjer.append(f"\t\tsourceColumn: {kilde}")
    if sorter:
        linjer.append(f"\t\tsortByColumn: {q(sorter)}")
    return "\n".join(linjer) + "\n"


M_TYPE = {"string": "type text", "int64": "Int64.Type", "double": "type number", "boolean": "type logical"}


def tabell(navn, beskrivelse, fil, kolonner, skjult=False):
    """kolonner: liste av dict(navn, kilde, typ, ...)."""
    ut = [f"/// {beskrivelse}", f"table {q(navn)}"]
    if skjult:
        ut.append("\tisHidden")
    ut.append(f"\tlineageTag: {tag(navn)}")
    ut.append("")
    for k in kolonner:
        k = dict(k)
        ut.append(kolonne(navn, k.pop("navn"), k.pop("kilde"), k.pop("typ"), **k))
    kilder = ", ".join(f'"{k["kilde"]}"' for k in kolonner)
    typer = ", ".join(f'{{"{k["kilde"]}", {M_TYPE[k["typ"]]}}}' for k in kolonner)
    ut.append(f"""\tpartition {q(navn)} = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Kilde = fnLesCsv("{fil}"),
\t\t\t\t    Kolonner = Table.SelectColumns(Kilde, {{{kilder}}}),
\t\t\t\t    Typer = Table.TransformColumnTypes(Kolonner, {{{typer}}}, "en-US")
\t\t\t\tin
\t\t\t\t    Typer
""")
    return "\n".join(ut)


# --------------------------------------------------------------------------- tabeller

TABELLER = {
    "dim_region": tabell(
        "dim_region",
        "Kommunene i Østfold, KOSTRA-gruppe 11, Østfold fylke og landet. region_id er dagens nummer; 2020-2023-tallene under 30xx er ført over i dbt.",
        "dim_region.csv",
        [
            dict(navn="region_id", kilde="region_id", typ="string", skjult=True),
            dict(navn="Region", kilde="region_navn", typ="string", sorter="Sortering",
                 beskrivelse="Kommune, KOSTRA-gruppe, fylke eller landet."),
            dict(navn="Regiontype", kilde="region_type", typ="string"),
            dict(navn="I utvalget", kilde="i_utvalg", typ="boolean",
                 beskrivelse="De seks regionene rapporten sammenligner: Moss, KOSTRA-gruppe 11, Østfold, Sarpsborg, Fredrikstad og Halden."),
            dict(navn="Sortering", kilde="sortering", typ="int64", skjult=True),
            dict(navn="Farge", kilde="farge", typ="string", skjult=True),
            dict(navn="Kart X", kilde="kart_x", typ="double", skjult=True),
            dict(navn="Kart Y", kilde="kart_y", typ="double", skjult=True),
        ],
    ),
    "dim_aar": tabell(
        "dim_aar",
        "Regnskapsårene 2020-2025.",
        "dim_aar.csv",
        [
            dict(navn="År", kilde="aar", typ="int64", fmt="0", beskrivelse="Regnskapsår."),
            dict(navn="Siste år", kilde="er_siste_aar", typ="boolean", skjult=True),
        ],
    ),
    "dim_funksjon": tabell(
        "dim_funksjon",
        "KOSTRA-funksjonene i eiendomsforvaltningen. FGK6 og FGK6a er SSBs aggregater og er merket, så de ikke summeres sammen med delene.",
        "dim_funksjon.csv",
        [
            dict(navn="funksjon_kode", kilde="funksjon_kode", typ="string", skjult=True),
            dict(navn="Funksjon", kilde="funksjon_kort", typ="string", sorter="Sortering"),
            dict(navn="Funksjon fullt navn", kilde="funksjon_navn", typ="string"),
            dict(navn="Funksjonsgruppe", kilde="funksjon_gruppe", typ="string",
                 beskrivelse="Forvaltning (121), Formålsbygg (de seks byggfunksjonene) eller Aggregat."),
            dict(navn="Er aggregat", kilde="er_aggregat", typ="boolean", skjult=True),
            dict(navn="Sortering", kilde="sortering", typ="int64", skjult=True),
        ],
    ),
    "fact_eiendom": tabell(
        "fact_eiendom",
        "Hovedtall fra SSB tabell 12559 per region, år og funksjon. Netto, korrigert brutto og brutto ligger i hver sin kolonne. Østfold 2020-2023 er beregnet fra kommunene.",
        "fact_eiendom.csv",
        [
            dict(navn="region_id", kilde="region_id", typ="string", skjult=True),
            dict(navn="aar", kilde="aar", typ="int64", skjult=True),
            dict(navn="funksjon_kode", kilde="funksjon_kode", typ="string", skjult=True),
            dict(navn="netto_1000kr", kilde="netto_1000kr", typ="double", skjult=True),
            dict(navn="korr_brutto_1000kr", kilde="korr_brutto_1000kr", typ="double", skjult=True),
            dict(navn="brutto_1000kr", kilde="brutto_1000kr", typ="double", skjult=True),
            dict(navn="netto_per_innbygger", kilde="netto_per_innbygger", typ="double", skjult=True),
            dict(navn="korr_brutto_per_kvm", kilde="korr_brutto_per_kvm", typ="double", skjult=True),
            dict(navn="innbyggere", kilde="innbyggere", typ="double", skjult=True),
            dict(navn="Kilde", kilde="kilde", typ="string",
                 beskrivelse="SSB, eller beregnet fra de tolv kommunene (Østfold 2020-2023)."),
        ],
    ),
    "fact_art": tabell(
        "fact_art",
        "Korrigerte brutto driftsutgifter brutt ned på art, kommunekonsern (SSB tabell 12367). Gruppene summerer til AGD4 i tabell 12559.",
        "fact_art.csv",
        [
            dict(navn="region_id", kilde="region_id", typ="string", skjult=True),
            dict(navn="aar", kilde="aar", typ="int64", skjult=True),
            dict(navn="funksjon_kode", kilde="funksjon_kode", typ="string", skjult=True),
            dict(navn="Art", kilde="art_gruppe", typ="string", sorter="Art sortering",
                 beskrivelse="Lønn, pensjon, arbeidsgiveravgift, kjøp av varer og tjenester, eller resten: overføringer, kjøp som erstatter egenproduksjon, merverdiavgift, internt fordelte utgifter m.m."),
            dict(navn="Personal", kilde="er_personal", typ="boolean",
                 beskrivelse="Sann for lønn, pensjon og arbeidsgiveravgift."),
            dict(navn="Art sortering", kilde="sortering", typ="int64", skjult=True),
            dict(navn="belop_1000kr", kilde="belop_1000kr", typ="double", skjult=True),
        ],
    ),
    "fact_mke_aarsverk": tabell(
        "fact_mke_aarsverk",
        "Årsverk i MKEiendom per 31.12, fra Moss kommunes årsrapporter 2024 og 2025. Ledige stillinger og lærlinger er ikke med.",
        "fact_mke_aarsverk.csv",
        [
            dict(navn="aar", kilde="aar", typ="int64", skjult=True),
            dict(navn="aarsverk", kilde="aarsverk", typ="double", skjult=True),
            dict(navn="Kilde årsverk", kilde="kilde", typ="string"),
        ],
    ),
    "fact_fdv": tabell(
        "fact_fdv",
        "Forvaltning, drift og vedlikehold av formålsbyggene (SSB tabell 12905) med areal fra tabell 11906. Kroner per m² er mot eid areal, som hos SSB.",
        "fact_fdv.csv",
        [
            dict(navn="region_id", kilde="region_id", typ="string", skjult=True),
            dict(navn="aar", kilde="aar", typ="int64", skjult=True),
            dict(navn="funksjon_kode", kilde="funksjon_kode", typ="string", skjult=True),
            dict(navn="energi_1000kr", kilde="energi_1000kr", typ="double", skjult=True),
            dict(navn="vedlikehold_1000kr", kilde="vedlikehold_1000kr", typ="double", skjult=True),
            dict(navn="energi_per_kvm", kilde="energi_per_kvm", typ="double", skjult=True),
            dict(navn="renhold_per_kvm", kilde="renhold_per_kvm", typ="double", skjult=True),
            dict(navn="drift_ellers_per_kvm", kilde="drift_ellers_per_kvm", typ="double", skjult=True),
            dict(navn="vedlikehold_per_kvm", kilde="vedlikehold_per_kvm", typ="double", skjult=True),
            dict(navn="fdv_eide_bygg_per_kvm", kilde="fdv_eide_bygg_per_kvm", typ="double", skjult=True),
            dict(navn="areal_eid", kilde="areal_eid", typ="double", skjult=True),
            dict(navn="areal_samlet", kilde="areal_samlet", typ="double", skjult=True),
        ],
    ),
}

# --------------------------------------------------------------------------- mål

EN = "HASONEVALUE ( dim_region[region_id] ) && HASONEVALUE ( dim_aar[År] )"
MOSS = 'dim_region[region_id] = "3103"'
KG11 = 'dim_region[region_id] = "EKG11"'
FORRIGE = "VAR _Aar = SELECTEDVALUE ( dim_aar[År] )"


def fast(funksjon, kol, tabell_="fact_eiendom"):
    return f"""IF (
			    {EN},
			    CALCULATE ( SUM ( {tabell_}[{kol}] ), dim_funksjon[funksjon_kode] = "{funksjon}" )
			)"""


MAAL = [
    # (navn, uttrykk, format, mappe, beskrivelse, skjult)
    ("Eiendomsforvaltning per innbygger", fast("FGK6a", "netto_per_innbygger"), "#,0", "Per innbygger",
     "Netto driftsutgifter til eiendomsforvaltning (FGK6a) per innbygger, kroner. SSBs tall for én region og ett år; tomt ellers, fordi tall per innbygger ikke kan summeres.", False),
    ("Forvaltning 121 per innbygger", fast("121", "netto_per_innbygger"), "#,0", "Per innbygger",
     "Netto driftsutgifter på funksjon 121 Forvaltningsutgifter i eiendomsforvaltningen per innbygger, kroner. Tallet bak +105 prosent i kommunedirektørens analyse.", False),
    ("Formålsbygg per innbygger", "[Eiendomsforvaltning per innbygger] - [Forvaltning 121 per innbygger]", "#,0", "Per innbygger",
     "Eiendomsforvaltning minus funksjon 121, per innbygger. SSB publiserer ikke FGK6 per innbygger; differansen er det samme som summen av de seks byggfunksjonene.", False),

    ("Formålsbygg kr per m²", fast("FGK6", "korr_brutto_per_kvm"), "#,0", "Per m²",
     "Korrigerte brutto driftsutgifter på formålsbyggene per m² samlet areal (eid + leid), som hos SSB.", False),
    ("Forvaltning 121 kr per m²", fast("121", "korr_brutto_per_kvm"), "#,0", "Per m²",
     "Funksjon 121 per m² formålsbygg. SSB fordeler forvaltningen på hele byggmassen.", False),
    ("Energi kr per m²", fast("FGK6", "energi_per_kvm", "fact_fdv"), "#,0", "Per m²",
     "Energiutgifter per m² eid areal, formålsbyggene samlet (SSB tabell 12905).", False),
    ("Renhold kr per m²", fast("FGK6", "renhold_per_kvm", "fact_fdv"), "#,0", "Per m²",
     "Renhold per m² eid areal.", False),
    ("Drift ellers kr per m²", fast("FGK6", "drift_ellers_per_kvm", "fact_fdv"), "#,0", "Per m²",
     "Driftsaktiviteter minus energi og renhold, per m² eid areal: vakthold, vaktmester, forsikring, kommunale avgifter m.m.", False),
    ("Vedlikehold kr per m²", fast("FGK6", "vedlikehold_per_kvm", "fact_fdv"), "#,0", "Per m²",
     "Vedlikeholdsaktiviteter per m² eid areal.", False),
    ("FDV kr per m²", "[Energi kr per m²] + [Renhold kr per m²] + [Drift ellers kr per m²] + [Vedlikehold kr per m²]", "#,0", "Per m²",
     "Drift og vedlikehold per m² eid areal: energi, renhold, drift ellers og vedlikehold.", False),

    ("Korrigerte brutto (mill.)",
     "DIVIDE ( CALCULATE ( SUM ( fact_eiendom[korr_brutto_1000kr] ), KEEPFILTERS ( dim_funksjon[Er aggregat] = FALSE () ) ), 1000 )",
     "#,0.0", "Kroner",
     "Korrigerte brutto driftsutgifter i millioner kroner, summert over de sju funksjonene. Aggregatene FGK6 og FGK6a er holdt utenfor, så ingenting telles to ganger.", False),
    ("Forvaltning 121 (mill.)", 'CALCULATE ( [Korrigerte brutto (mill.)], dim_funksjon[funksjon_kode] = "121" )', "#,0.0", "Kroner",
     "Korrigerte brutto driftsutgifter på funksjon 121, millioner kroner.", False),
    ("Formålsbygg (mill.)", 'CALCULATE ( [Korrigerte brutto (mill.)], dim_funksjon[Funksjonsgruppe] = "Formålsbygg" )', "#,0.0", "Kroner",
     "Korrigerte brutto driftsutgifter på de seks byggfunksjonene, millioner kroner.", False),
    ("Eiendomsforvaltning (mill.)", 'CALCULATE ( [Korrigerte brutto (mill.)], REMOVEFILTERS ( dim_funksjon ) )', "#,0.0", "Kroner",
     "121 og formålsbyggene samlet, millioner kroner. Lik SSBs FGK6a (testet i dbt).", False),
    ("Endring mot året før (mill.)",
     f"""{FORRIGE}
			RETURN
			    IF ( NOT ISBLANK ( _Aar ), [Korrigerte brutto (mill.)] - CALCULATE ( [Korrigerte brutto (mill.)], dim_aar[År] = _Aar - 1 ) )""",
     '+#,0.0;-#,0.0;0.0', "Kroner",
     "Korrigerte brutto i valgt år minus året før, millioner kroner. Med funksjon på aksen: hvor endringen ligger.", False),

    ("Beløp art (mill.)", "DIVIDE ( SUM ( fact_art[belop_1000kr] ), 1000 )", "#,0.0", "Art",
     "Korrigerte brutto driftsutgifter per art, millioner kroner, kommunekonsern.", False),
    ("Endring art (mill.)",
     f"""{FORRIGE}
			RETURN
			    IF ( NOT ISBLANK ( _Aar ), [Beløp art (mill.)] - CALCULATE ( [Beløp art (mill.)], dim_aar[År] = _Aar - 1 ) )""",
     '+#,0.0;-#,0.0;0.0', "Art",
     "Beløp per art i valgt år minus året før, millioner kroner. Summen over artene er lik Endring mot året før.", False),
    ("Personalkostnader (mill.)", "CALCULATE ( [Beløp art (mill.)], fact_art[Personal] = TRUE () )", "#,0.0", "Art",
     "Lønn, pensjon og arbeidsgiveravgift, millioner kroner.", False),
    ("Endring personal (mill.)", "CALCULATE ( [Endring art (mill.)], fact_art[Personal] = TRUE () )", '+#,0.0;-#,0.0;0.0', "Art",
     "Personalkostnader i valgt år minus året før, millioner kroner.", False),

    # Faste sammenligninger til kortene
    ("Moss eiendomsforvaltning per innbygger", f"CALCULATE ( [Eiendomsforvaltning per innbygger], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 eiendomsforvaltning per innbygger", f"CALCULATE ( [Eiendomsforvaltning per innbygger], {KG11} )", "#,0", "Kort", "", False),
    ("Østfold eiendomsforvaltning per innbygger", 'CALCULATE ( [Eiendomsforvaltning per innbygger], dim_region[region_id] = "EKA31" )', '#,0" kr"', "Kort", "", False),
    ("Moss 121 per innbygger", f"CALCULATE ( [Forvaltning 121 per innbygger], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 121 per innbygger", f"CALCULATE ( [Forvaltning 121 per innbygger], {KG11} )", "#,0", "Kort", "", False),
    ("Moss formålsbygg kr per m²", f"CALCULATE ( [Formålsbygg kr per m²], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 formålsbygg kr per m²", f"CALCULATE ( [Formålsbygg kr per m²], {KG11} )", "#,0", "Kort", "", False),
    ("Moss energi kr per m²", f"CALCULATE ( [Energi kr per m²], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 energi kr per m²", f"CALCULATE ( [Energi kr per m²], {KG11} )", "#,0", "Kort", "", False),
    ("Moss FDV kr per m²", f"CALCULATE ( [FDV kr per m²], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 FDV kr per m²", f"CALCULATE ( [FDV kr per m²], {KG11} )", "#,0", "Kort", "", False),

    ("Moss 121 endring (mill.)", f"CALCULATE ( [Endring mot året før (mill.)], {MOSS}, dim_funksjon[funksjon_kode] = \"121\" )",
     '"+"#,0.0" mill. kr";"−"#,0.0" mill. kr";"0"', "Kort", "Endring i funksjon 121 for Moss fra året før.", False),
    ("Moss formålsbygg endring (mill.)", f"CALCULATE ( [Endring mot året før (mill.)], {MOSS}, dim_funksjon[Funksjonsgruppe] = \"Formålsbygg\" )",
     '"+"#,0.0" mill. kr";"−"#,0.0" mill. kr";"0"', "Kort", "Endring i de seks byggfunksjonene for Moss fra året før.", False),
    ("Moss eiendomsforvaltning endring (mill.)", f"CALCULATE ( [Endring mot året før (mill.)], {MOSS}, REMOVEFILTERS ( dim_funksjon ) )",
     '"+"#,0.0" mill. kr";"−"#,0.0" mill. kr";"0"', "Kort", "Endring i eiendomsforvaltningen samlet for Moss fra året før.", False),
    ("Moss eiendomsforvaltning endring %",
     f"""{FORRIGE}
			VAR _Naa = CALCULATE ( [Eiendomsforvaltning (mill.)], {MOSS} )
			VAR _Foer = CALCULATE ( [Eiendomsforvaltning (mill.)], {MOSS}, dim_aar[År] = _Aar - 1 )
			RETURN
			    DIVIDE ( _Naa - _Foer, _Foer )""",
     '"▲ "0.0%" mot året før";"▼ "0.0%" mot året før";"uendret"', "Kort", "", False),
    ("Moss 121 personal endring (mill.)", f"CALCULATE ( [Endring personal (mill.)], {MOSS}, dim_funksjon[funksjon_kode] = \"121\" )",
     '"+"#,0.0" mill. kr";"−"#,0.0" mill. kr";"0"', "Kort", "Lønn, pensjon og arbeidsgiveravgift på 121 for Moss, endring fra året før.", False),
    ("Moss formålsbygg personal endring (mill.)", f"CALCULATE ( [Endring personal (mill.)], {MOSS}, dim_funksjon[Funksjonsgruppe] = \"Formålsbygg\" )",
     '"+"#,0.0" mill. kr";"−"#,0.0" mill. kr";"0"', "Kort", "Lønn, pensjon og arbeidsgiveravgift på de seks byggfunksjonene for Moss, endring fra året før.", False),

    ("Avvik eiendomsforvaltning mot KG11",
     "DIVIDE ( [Moss eiendomsforvaltning per innbygger] - [KG11 eiendomsforvaltning per innbygger], [KG11 eiendomsforvaltning per innbygger] )",
     '"▲ "0%" over KOSTRA-gruppe 11";"▼ "0%" under KOSTRA-gruppe 11";"lik KOSTRA-gruppe 11"', "Kort", "Moss mot gruppen, relativt.", False),
    ("Avvik 121 mot KG11",
     "DIVIDE ( [Moss 121 per innbygger] - [KG11 121 per innbygger], [KG11 121 per innbygger] )",
     '"▲ "0%" over KOSTRA-gruppe 11";"▼ "0%" under KOSTRA-gruppe 11";"lik KOSTRA-gruppe 11"', "Kort",
     "Moss mot gruppen på funksjon 121. +106 prosent i 2025 med SSBs tall med én desimal; 693 mot 336 avrundet gir 106 prosent.", False),
    ("Østfold avvik mot Moss",
     "DIVIDE ( [Moss eiendomsforvaltning per innbygger] - [Østfold eiendomsforvaltning per innbygger], [Østfold eiendomsforvaltning per innbygger] )",
     '"Moss ▲ "0.0%" over fylket";"Moss ▼ "0.0%" under fylket";"Moss lik fylket"', "Kort", "", False),

    # Vedlikehold
    ("Moss vedlikehold kr per m²", f"CALCULATE ( [Vedlikehold kr per m²], {MOSS} )", '#,0" kr"', "Kort", "", False),
    ("KG11 vedlikehold kr per m²", f"CALCULATE ( [Vedlikehold kr per m²], {KG11} )", "#,0", "Kort", "", False),

    # Kroneverdien av avviket på 121
    ("Innbyggere", fast("FGK6a", "innbyggere"), "#,0", "Per innbygger",
     "Innbyggere 31.12 i regnskapsåret (SSB tabell 06913), samme tall som KOSTRA deler på. Bare kommunene og Østfold.", False),
    ("Avvik 121 per innbygger mot KG11", "[Moss 121 per innbygger] - [KG11 121 per innbygger]", "#,0", "Kort",
     "Moss minus KOSTRA-gruppe 11 på funksjon 121, kroner per innbygger.", False),
    ("Avvik 121 i kroner (mill.)",
     f"DIVIDE ( [Avvik 121 per innbygger mot KG11] * CALCULATE ( [Innbyggere], {MOSS} ), 1000000 )",
     '#,0.0" mill. kr"', "Kort",
     "Hva avviket på 121 betyr i kroner: avvik per innbygger ganger innbyggerne i Moss. Drifts- og investeringsanalysen 2027-2030 regnet om lag 20 millioner på foreløpige 2025-tall.", False),

    # Personal og årsverk over tid
    ("Moss 121 personal (mill.)", f"CALCULATE ( [Personalkostnader (mill.)], {MOSS}, dim_funksjon[funksjon_kode] = \"121\" )", "#,0.0", "Art",
     "Lønn, pensjon og arbeidsgiveravgift på funksjon 121, Moss, millioner kroner.", False),
    ("Moss formålsbygg personal (mill.)", f"CALCULATE ( [Personalkostnader (mill.)], {MOSS}, dim_funksjon[Funksjonsgruppe] = \"Formålsbygg\" )", "#,0.0", "Art",
     "Lønn, pensjon og arbeidsgiveravgift på de seks byggfunksjonene, Moss, millioner kroner.", False),
    ("Årsverk MKEiendom", "SUM ( fact_mke_aarsverk[aarsverk] )", "#,0", "Art",
     "Årsverk i MKEiendom per 31.12 (Moss kommunes årsrapporter).", False),

    # Tekstlinjer under tallene i kortene. Retning og tall i én tekst, så linjen stemmer for alle år.
    ("Tekst eiendom mot KG11",
     """VAR _A = [Avvik eiendomsforvaltning mot KG11]
			RETURN
			    IF (
			        NOT ISBLANK ( _A ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 ("
			            & FORMAT ( [KG11 eiendomsforvaltning per innbygger], "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),
    ("Tekst eiendom mot Østfold",
     """VAR _A = [Østfold avvik mot Moss]
			RETURN
			    IF (
			        NOT ISBLANK ( _A ),
			        "Moss " & IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0.0 %" )
			            & IF ( _A < 0, " under", " over" ) & " fylket"
			    )""", None, "Tekst", "", True),
    ("Tekst 121 mot KG11",
     """VAR _A = [Avvik 121 mot KG11]
			RETURN
			    IF (
			        NOT ISBLANK ( _A ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 ("
			            & FORMAT ( [KG11 121 per innbygger], "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),
    ("Tekst 121 to år",
     f"""{FORRIGE}
			VAR _Naa = [Avvik 121 mot KG11]
			VAR _Foer = CALCULATE ( [Avvik 121 mot KG11], dim_aar[År] = _Aar - 1 )
			RETURN
			    IF (
			        NOT ISBLANK ( _Naa ),
			        "▲ " & FORMAT ( _Naa, "0 %" ) & " over gruppen"
			            & IF ( NOT ISBLANK ( _Foer ), ", " & ( _Aar - 1 ) & ": ▲ " & FORMAT ( _Foer, "0 %" ) )
			    )""", None, "Tekst", "", True),
    ("Tekst avvik i kroner",
     f"""VAR _Per = [Avvik 121 per innbygger mot KG11]
			VAR _Innb = CALCULATE ( [Innbyggere], {MOSS} )
			RETURN
			    IF ( NOT ISBLANK ( _Per ), FORMAT ( _Per, "#,0" ) & " kr per innbygger × " & FORMAT ( _Innb, "#,0" ) & " innbyggere" )""",
     None, "Tekst", "", True),
    ("Tekst personal 121",
     """VAR _P = [Moss 121 personal endring (mill.)]
			RETURN
			    IF ( NOT ISBLANK ( _P ), "Herav personalkostnader: " & IF ( _P >= 0, "+", "−" ) & FORMAT ( ABS ( _P ), "#,0.0" ) & " mill." )""",
     None, "Tekst", "", True),
    ("Tekst personal formålsbygg",
     """VAR _P = [Moss formålsbygg personal endring (mill.)]
			RETURN
			    IF ( NOT ISBLANK ( _P ), "Herav personalkostnader: " & IF ( _P >= 0, "+", "−" ) & FORMAT ( ABS ( _P ), "#,0.0" ) & " mill." )""",
     None, "Tekst", "", True),
    ("Tekst eiendom endring",
     f"""{FORRIGE}
			VAR _E = [Moss eiendomsforvaltning endring %]
			RETURN
			    IF ( NOT ISBLANK ( _E ), IF ( _E < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _E ), "0.0 %" ) & " mot " & ( _Aar - 1 ) )""",
     None, "Tekst", "", True),
    ("Tekst formålsbygg mot KG11",
     """VAR _M = [Moss formålsbygg kr per m²]
			VAR _K = [KG11 formålsbygg kr per m²]
			VAR _A = DIVIDE ( _M - _K, _K )
			RETURN
			    IF (
			        NOT ISBLANK ( _M ) && NOT ISBLANK ( _K ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0.0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 (" & FORMAT ( _K, "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),
    ("Tekst FDV mot KG11",
     """VAR _M = [Moss FDV kr per m²]
			VAR _K = [KG11 FDV kr per m²]
			VAR _A = DIVIDE ( _M - _K, _K )
			RETURN
			    IF (
			        NOT ISBLANK ( _M ) && NOT ISBLANK ( _K ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0.0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 (" & FORMAT ( _K, "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),
    ("Tekst energi mot KG11",
     """VAR _M = [Moss energi kr per m²]
			VAR _K = [KG11 energi kr per m²]
			VAR _A = DIVIDE ( _M - _K, _K )
			RETURN
			    IF (
			        NOT ISBLANK ( _M ) && NOT ISBLANK ( _K ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0.0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 (" & FORMAT ( _K, "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),
    ("Tekst vedlikehold mot KG11",
     """VAR _M = [Moss vedlikehold kr per m²]
			VAR _K = [KG11 vedlikehold kr per m²]
			VAR _A = DIVIDE ( _M - _K, _K )
			RETURN
			    IF (
			        NOT ISBLANK ( _M ) && NOT ISBLANK ( _K ),
			        IF ( _A < 0, "▼ ", "▲ " ) & FORMAT ( ABS ( _A ), "0 %" )
			            & IF ( _A < 0, " under", " over" ) & " KOSTRA-gruppe 11 (" & FORMAT ( _K, "#,0" ) & " kr)"
			    )""", None, "Tekst", "", True),

    # Kart og farger
    ("Kart X", "IF ( HASONEVALUE ( dim_region[region_id] ), MAX ( dim_region[Kart X] ) )", "0.000", "Kart",
     "Tyngdepunktet til kommunens største sammenhengende flate, lengdegrad × cos(59,3°).", True),
    ("Kart Y", "IF ( HASONEVALUE ( dim_region[region_id] ), MAX ( dim_region[Kart Y] ) )", "0.000", "Kart",
     "Tyngdepunktet til kommunens største sammenhengende flate, breddegrad.", True),
    ("Farge kart",
     """VAR _V = [Eiendomsforvaltning per innbygger]
			VAR _Moss = CALCULATE ( [Eiendomsforvaltning per innbygger], REMOVEFILTERS ( dim_region ), dim_region[region_id] = "3103" )
			RETURN
			    SWITCH (
			        TRUE (),
			        SELECTEDVALUE ( dim_region[region_id] ) = "3103", "#2DD4BF",
			        _V > _Moss, "#FF6B8B",
			        "#7C83FF"
			    )""",
     None, "Visning", "Turkis for Moss, rosa for kommuner som bruker mer per innbygger enn Moss, indigo for de som bruker mindre.", True),

    # Tekst
    ("Data til og med", '"KOSTRA " & CALCULATE ( MAX ( fact_eiendom[aar] ), REMOVEFILTERS () )', None, "Tekst", "", True),

    # Kontroll
    ("Kontroll aggregat mot deler",
     """VAR _Deler = CALCULATE ( SUM ( fact_eiendom[korr_brutto_1000kr] ), dim_funksjon[Er aggregat] = FALSE () )
			VAR _Fgk6a = CALCULATE ( SUM ( fact_eiendom[korr_brutto_1000kr] ), dim_funksjon[funksjon_kode] = "FGK6a" )
			RETURN
			    _Deler - _Fgk6a""",
     "#,0", "Kontroll", "Sju funksjoner minus SSBs FGK6a, tusen kroner. Skal være 0.", False),
    ("Kontroll art mot hovedtabell",
     """VAR _Art = SUM ( fact_art[belop_1000kr] )
			VAR _Hoved = CALCULATE ( SUM ( fact_eiendom[korr_brutto_1000kr] ), dim_funksjon[Er aggregat] = FALSE () )
			RETURN
			    _Art - _Hoved""",
     "#,0", "Kontroll", "Sum over artene (tabell 12367) minus korrigerte brutto (tabell 12559), tusen kroner. 0 for alle regioner unntatt landet.", False),
]


def maal_tekst():
    ut = ["/// Alle mål, ordnet i visningsmapper. Ingen data.", "table _Mål", f"\tlineageTag: {tag('_Mål')}", ""]
    for navn, uttrykk, fmt, mappe, besk, skjult in MAAL:
        if besk:
            ut.append(f"\t/// {besk}")
        if "\n" in uttrykk:
            ut.append(f"\tmeasure {q(navn)} =\n\t\t\t{uttrykk}")
        else:
            ut.append(f"\tmeasure {q(navn)} = {uttrykk}")
        if fmt:
            if '"' in fmt or ";" in fmt:
                fmt = '"' + fmt.replace('"', '""') + '"'
            ut.append(f"\t\tformatString: {fmt}")
        if skjult:
            ut.append("\t\tisHidden")
        ut.append(f"\t\tdisplayFolder: {mappe}")
        ut.append(f"\t\tlineageTag: {tag('_Mål', navn)}")
        ut.append("")
    ut.append("""\tpartition _Mål = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Kilde = #table(type table [Tom = text], {})
\t\t\t\tin
\t\t\t\t    Kilde
""")
    return "\n".join(ut)


RELASJONER = [("fact_mke_aarsverk", "aar", "dim_aar", "År")]
for fakta in ["fact_eiendom", "fact_art", "fact_fdv"]:
    RELASJONER += [
        (fakta, "region_id", "dim_region", "region_id"),
        (fakta, "aar", "dim_aar", "År"),
        (fakta, "funksjon_kode", "dim_funksjon", "funksjon_kode"),
    ]


def skriv(sti, tekst):
    sti.parent.mkdir(parents=True, exist_ok=True)
    sti.write_text(tekst.replace("\r\n", "\n"), encoding="utf-8")


def main():
    d = SM / "definition"
    skriv(SM / "definition.pbism", json.dumps({"version": "4.2", "settings": {}}, indent=2))
    skriv(SM / ".platform", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAVN},
        "config": {"version": "2.0", "logicalId": tag("logicalId", "sm")},
    }, indent=2))
    skriv(d / "database.tmdl", "database\n\tcompatibilityLevel: 1606\n\n")
    rekkefolge = list(TABELLER) + ["_Mål"]
    skriv(d / "model.tmdl", f"""/// Eiendomsforvaltningen i Moss målt mot KOSTRA-gruppe 11, Østfold og nabobyene, 2020-2025. SSB KOSTRA. Leser dbt-martene i MartMappe.
model {NAVN}
\tculture: nb-NO
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tdiscourageImplicitMeasures
\tsourceQueryCulture: en-US
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_QueryOrder = {json.dumps(rekkefolge + ["MartMappe", "fnLesCsv"], ensure_ascii=False)}

annotation PBI_ProTooling = ["DevMode"]

""" + "".join(f"ref table {q(t)}\n" for t in rekkefolge) + "\nref cultureInfo nb-NO\n")
    skriv(d / "cultures" / "nb-NO.tmdl", "cultureInfo nb-NO\n")
    skriv(d / "expressions.tmdl", f"""/// Mappen der src/eksport.py legger dbt-martene. Full sti med skråstrek på slutten.
expression MartMappe = "C:\\prosjekt\\mke-forvaltning\\data\\mart\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
\tlineageTag: {tag('expr', 'MartMappe')}

\tannotation PBI_ResultType = Text

/// Leser en CSV fra MartMappe. Samme funksjon som i de andre prosjektene.
expression fnLesCsv =
\t\tlet
\t\t    fnLesCsv = (Filnavn as text) as table =>
\t\t        let
\t\t            Kilde = Csv.Document(
\t\t                File.Contents(MartMappe & Filnavn),
\t\t                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
\t\t            ),
\t\t            Overskrifter = Table.PromoteHeaders(Kilde, [PromoteAllScalars = true])
\t\t        in
\t\t            Overskrifter
\t\tin
\t\t    fnLesCsv
\tlineageTag: {tag('expr', 'fnLesCsv')}

""")
    rel = []
    for f, fk, t, tk in RELASJONER:
        rel.append(f"relationship {tag('rel', f, fk)}\n\tfromColumn: {f}.{q(fk)}\n\ttoColumn: {t}.{q(tk)}\n")
    skriv(d / "relationships.tmdl", "\n".join(rel))
    for navn, tekst in TABELLER.items():
        skriv(d / "tables" / f"{navn}.tmdl", tekst)
    skriv(d / "tables" / "_Mål.tmdl", maal_tekst())
    skriv(SM / ".pbi" / "editorSettings.json", json.dumps({
        "version": "1.0", "autodetectRelationships": False, "parallelQueryLoading": True,
        "typeDetectionEnabled": False, "relationshipImportEnabled": False,
        "runBackgroundAnalysis": True, "shouldNotifyUserOfNameConflictResolution": True}, indent=2))
    print(f"Skrev {SM.relative_to(ROT)}: {len(TABELLER) + 1} tabeller, {len(MAAL)} mål, {len(RELASJONER)} relasjoner")


if __name__ == "__main__":
    main()
