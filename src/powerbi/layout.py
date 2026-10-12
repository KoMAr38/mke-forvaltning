"""
Felles oppsett for bakgrunnsbildene (lag_bilder.py) og rapporten (lag_rapport.py).
Alle koordinater er i piksler på en side på 1920 × 1080. Rammene til kort og paneler
tegnes i bakgrunnsbildet, og visualene legges oppå med gjennomsiktig bakgrunn.
"""

B, H = 1920, 1080

# Fargene. Én palett for hele rapporten; regionfargene ligger i seeds/region.csv.
BG = "#0B1222"
TEKST = "#F4F7FD"
TEKST2 = "#C9D3E8"
DEMPET = "#8D9BBA"
LINJE = "#2A3757"
TURKIS = "#2DD4BF"
INDIGO = "#7C83FF"
ROSA = "#FF6B8B"
GULL = "#F5C26B"
HIMMEL = "#38BDF8"
FIOLETT = "#A78BFA"
ORANSJE = "#FB923C"
SKIFER = "#475A82"

# Navigasjon til venstre
NAV_B = 112
NAV_KNAPP = dict(x=8, w=96, h=80)
NAV_Y0, NAV_STEG = 152, 92

# Topp og bunn
TITTEL = dict(x=144, y=24, w=1180, h=54)
UNDERTITTEL = dict(x=144, y=78, w=1180, h=30)
AARVELGER = dict(x=1352, y=34, w=528, h=60)
BUNN = dict(x=144, y=1030, w=1736, h=28)

# Fire kort øverst
KORT_Y, KORT_H, KORT_B, KORT_GAP = 136, 136, 416, 24


def kort_x(i):
    return 144 + i * (KORT_B + KORT_GAP)


KILDER = ("Kilder: SSB KOSTRA, tabell 12559, 12367, 12905, 11906 og 06913, kommunekonsern. "
          "Årsverk: Moss kommunes årsrapporter 2024 og 2025. Kart: Kartverket, CC BY 4.0.")

# Kartet over Østfold. Akseområdet til punktdiagrammet og bildet under må være like.
KART_X = (5.37, 6.075)        # lengdegrad × cos(59,3°)
KART_Y = (58.83, 59.815)      # breddegrad
KART_RUTE = dict(x=1326, y=380, w=444, h=620)

SIDER = [
    dict(
        id="oversikt", navn="Oversikt", ikon="dashboard",
        tittel="Moss bruker mindre på eiendom enn KOSTRA-gruppe 11 og Østfold",
        undertittel=("Netto driftsutgifter til eiendomsforvaltning per innbygger, kommunekonsern. "
                     "Funksjon 121 og de seks formålsbyggene samlet, KOSTRA 2020–2025."),
        aarvelger=True,
        kort=[
            dict(ikon="apartment", farge=TURKIS, etikett="Moss, eiendomsforvaltning per innbygger",
                 verdi="Moss eiendomsforvaltning per innbygger", linje="Tekst eiendom mot KG11", linjefarge=TURKIS),
            dict(ikon="map", farge=INDIGO, etikett="Østfold, eiendomsforvaltning per innbygger",
                 verdi="Østfold eiendomsforvaltning per innbygger", linje="Tekst eiendom mot Østfold", linjefarge=TURKIS),
            dict(ikon="account_tree", farge=ROSA, etikett="Funksjon 121, Moss per innbygger",
                 verdi="Moss 121 per innbygger", linje="Tekst 121 mot KG11", linjefarge=ROSA),
            dict(ikon="payments", farge=GULL, etikett="Avviket på 121 i kroner",
                 verdi="Avvik 121 i kroner (mill.)", linje="Tekst avvik i kroner", linjefarge=DEMPET),
        ],
        paneler=dict(
            linje=dict(x=144, y=296, w=1048, h=420),
            kart=dict(x=1216, y=296, w=664, h=720),
            stolper=dict(x=144, y=740, w=1048, h=276),
        ),
    ),
    dict(
        id="f121", navn="Funksjon 121", ikon="account_tree",
        tittel="I 2025 steg personalkostnadene på 121, mens de falt på byggene",
        undertittel=("Moss, kommunekonsern. Endringen fra 2024 til 2025 per art og per funksjon. "
                     "MKEiendom gikk fra 58 til 59 årsverk."),
        # Siden forteller om ett bestemt år. Kortene og fossefallene er låst til 2025,
        # og i stedet for årsvelgeren står perioden øverst til høyre.
        aarvelger=False,
        fast_aar=2025,
        kort=[
            dict(ikon="account_tree", farge=ROSA, etikett="Funksjon 121, Moss per innbygger",
                 verdi="Moss 121 per innbygger", linje="Tekst 121 to år", linjefarge=ROSA),
            dict(ikon="trending_up", farge=ROSA, etikett="Funksjon 121, endring fra 2024",
                 verdi="Moss 121 endring (mill.)", linje="Tekst personal 121", linjefarge=DEMPET),
            dict(ikon="trending_down", farge=TURKIS, etikett="Formålsbyggene, endring fra 2024",
                 verdi="Moss formålsbygg endring (mill.)", linje="Tekst personal formålsbygg", linjefarge=DEMPET),
            dict(ikon="apartment", farge=INDIGO, etikett="Eiendomsforvaltning i alt, endring",
                 verdi="Moss eiendomsforvaltning endring (mill.)", linje="Tekst eiendom endring", linjefarge=DEMPET),
        ],
        paneler=dict(
            bro_art=dict(x=144, y=296, w=856, h=380),
            bro_funksjon=dict(x=1024, y=296, w=856, h=380),
            linje121=dict(x=144, y=700, w=856, h=316),
            personal=dict(x=1024, y=700, w=856, h=316),
        ),
    ),
    dict(
        id="bygg", navn="Bygg og energi", ikon="bolt",
        tittel="Siden 2021 har byggene kostet omtrent det samme per m² som i gruppen",
        undertittel=("Formålsbyggene, kroner per m². Drift og vedlikehold er målt mot eid areal, "
                     "driftsutgiftene i alt mot samlet areal, som hos SSB."),
        aarvelger=True,
        kort=[
            dict(ikon="apartment", farge=TURKIS, etikett="Formålsbygg, driftsutgifter per m²",
                 verdi="Moss formålsbygg kr per m²", linje="Tekst formålsbygg mot KG11", linjefarge=DEMPET),
            dict(ikon="handyman", farge=INDIGO, etikett="Drift og vedlikehold per m²",
                 verdi="Moss FDV kr per m²", linje="Tekst FDV mot KG11", linjefarge=DEMPET),
            dict(ikon="bolt", farge=GULL, etikett="Energi per m²",
                 verdi="Moss energi kr per m²", linje="Tekst energi mot KG11", linjefarge=DEMPET),
            dict(ikon="construction", farge=ROSA, etikett="Vedlikehold per m²",
                 verdi="Moss vedlikehold kr per m²", linje="Tekst vedlikehold mot KG11", linjefarge=ROSA),
        ],
        paneler=dict(
            linje_kvm=dict(x=144, y=296, w=856, h=380),
            linje_energi=dict(x=1024, y=296, w=856, h=380),
            fdv=dict(x=144, y=700, w=1736, h=316),
        ),
    ),
    dict(
        id="metode", navn="Metode", ikon="schema",
        tittel="Slik er tallene laget",
        undertittel=("KOSTRA-tallene er hentet fra SSB med API og kontrollert i dbt "
                     "før de kommer inn i rapporten."),
        aarvelger=False,
        kort=[],
        paneler=dict(
            flyt=dict(x=144, y=136, w=1736, h=250),
            tekst_a=dict(x=144, y=410, w=560, h=436),
            tekst_b=dict(x=728, y=410, w=560, h=436),
            tekst_c=dict(x=1312, y=410, w=568, h=436),
            kontroll=dict(x=144, y=870, w=1736, h=136),
        ),
    ),
]

# Flytdiagrammet på metodesiden: (ikon, tittel, linje 1, linje 2)
FLYT = [
    ("cloud_download", "SSB statistikkbanken", "KOSTRA 12559, 12367, 12905,", "11906 og befolkning 06913"),
    ("code", "Python", "extract/hent_ssb.py", "API v0, sha256 i manifest"),
    ("storage", "dbt + DuckDB", "staging, intermediate, marts", "{tester} tester"),
    ("table_chart", "data/mart", "sju CSV-filer", "i Git"),
    ("bar_chart", "Power BI", "modell i TMDL,", "rapport i PBIR"),
]
