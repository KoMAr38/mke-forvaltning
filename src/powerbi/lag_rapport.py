"""
Skriver rapporten (PBIR) til powerbi/MKE_Eiendomsforvaltning.Report.

Fire sider på 1920 × 1080: Oversikt, Funksjon 121, Bygg og energi og Metode.
Rammer, ikoner og kart ligger i bakgrunnsbildene fra lag_bilder.py. Her legges
visualene oppå, med de samme koordinatene fra layout.py.

Navnene på sider og visualer er de første 20 tegnene av en md5 av en fast nøkkel,
så de er like fra kjøring til kjøring.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402

ROT = Path(__file__).resolve().parents[2]
NAVN = "MKE_Eiendomsforvaltning"
RAPP = ROT / "powerbi" / f"{NAVN}.Report"
DEF = RAPP / "definition"
RES = RAPP / "StaticResources"
TEMA = "Nordlys-mke.json"
BASETEMA = "Fluent2-CY26SU10"
SKJEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"

REGIONFARGER = {}  # fylles fra seeds/region.csv


def nid(*deler):
    return hashlib.md5("/".join(deler).encode()).hexdigest()[:20]


SIDE_ID = {s["id"]: nid("side", s["id"]) for s in L.SIDER}


# --------------------------------------------------------------------------- små hjelpere

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def farge(c):
    return {"solid": {"color": lit(f"'{c}'")}}


def tekstlit(t):
    return lit("'" + t.replace("'", "''") + "'")


def maal(navn, visningsnavn=None):
    p = {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Mål"}}, "Property": navn}},
         "queryRef": f"_Mål.{navn}", "nativeQueryRef": navn}
    if visningsnavn:
        p["displayName"] = visningsnavn
    return p


def kol(tabell, navn):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": tabell}}, "Property": navn}},
            "queryRef": f"{tabell}.{navn}", "nativeQueryRef": navn}


def sortering(tabell, navn, retning="Ascending"):
    return {"sort": [{"field": {"Column": {"Expression": {"SourceRef": {"Entity": tabell}}, "Property": navn}},
                      "direction": retning}], "isDefaultSort": True}


def filter_in(tabell, kolonne, verdier, nokkel):
    """Kategorisk filter på visualnivå. verdier er DAX-literaler som tekst, f.eks. "'Moss'" eller "true"."""
    return {
        "name": "Filter" + nid("filter", nokkel, tabell, kolonne),
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": tabell}}, "Property": kolonne}},
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": tabell, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": kolonne}}],
                "Values": [[{"Literal": {"Value": v}}] for v in verdier],
            }}}],
        },
        "howCreated": "User",
    }


def ingen_ramme(padding=0):
    p = f"{padding}D"
    return {
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"top": lit(p), "bottom": lit(p), "left": lit(p), "right": lit(p)}}],
    }


def diagramramme(tittel, undertittel):
    return {
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"top": lit("18D"), "bottom": lit("14D"), "left": lit("22D"), "right": lit("22D")}}],
        "title": [{"properties": {"show": lit("true"), "text": tekstlit(tittel), "fontSize": lit("13D"),
                                  "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": farge("#E8EEF9")}}],
        "subTitle": [{"properties": {"show": lit("true"), "text": tekstlit(undertittel), "fontSize": lit("10D"),
                                     "fontColor": farge(L.DEMPET)}}],
    }


AKSER = {
    "categoryAxis": [{"properties": {"show": lit("true"), "labelColor": farge("#9AA8C7"), "fontSize": lit("10D"),
                                     "showAxisTitle": lit("false"), "gridlineShow": lit("false"),
                                     "axisType": lit("'Categorical'")}}],
    "valueAxis": [{"properties": {"show": lit("true"), "labelColor": farge("#6B7A99"), "fontSize": lit("9D"),
                                  "showAxisTitle": lit("false"), "gridlineShow": lit("true"),
                                  "gridlineColor": farge(L.LINJE), "gridlineStyle": lit("'dotted'")}}],
    "legend": [{"properties": {"show": lit("true"), "position": lit("'Top'"), "labelColor": farge("#C9D3E8"),
                               "fontSize": lit("10D"), "showTitle": lit("false")}}],
}


def region_velger(region):
    return {"data": [{"scopeId": {"Comparison": {
        "ComparisonKind": 0,
        "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dim_region"}}, "Property": "Region"}},
        "Right": {"Literal": {"Value": "'" + region + "'"}},
    }}}]}


def regionfarger():
    return [{"properties": {"fill": farge(c)}, "selector": region_velger(r)} for r, c in REGIONFARGER.items()]


def stolpefarger():
    """Moss, gruppen og fylket i sine farger, nabobyene i dempet skifer."""
    viktige = {"Moss", "KOSTRA-gruppe 11", "Østfold"}
    return [{"properties": {"fill": farge(c if r in viktige else "#64748B")}, "selector": region_velger(r)}
            for r, c in REGIONFARGER.items()]


# Moss tegnes tykkest, sammenligningene litt tynnere og nabobyene tynnest,
# så Moss skiller seg ut selv der to farger ligger nær hverandre.
LINJEBREDDE = {"Moss": (4, 7), "KOSTRA-gruppe 11": (3, 5), "Østfold": (3, 5)}


def linjestiler(regioner):
    ut = [{"properties": {"strokeWidth": lit("2D"), "lineChartType": lit("'smooth'"),
                          "showMarker": lit("true"), "markerSize": lit("4D")}}]
    for r in regioner:
        bredde, markor = LINJEBREDDE.get(r, (2, 4))
        ut.append({"properties": {"strokeWidth": lit(f"{bredde}D"), "markerSize": lit(f"{markor}D")},
                   "selector": region_velger(r)})
    return ut


def maalfarger(par):
    return [{"properties": {"fill": farge(c)}, "selector": {"metadata": f"_Mål.{m}"}} for m, c in par]


# --------------------------------------------------------------------------- visualer

class Side:
    def __init__(self, spec):
        self.spec = spec
        self.visualer = []
        self.z = 1000
        self.ikke_filtrer = []   # visualer årsvelgeren ikke skal filtrere

    def legg(self, nokkel, x, y, w, h, visual, filtre=None, ekstra=None):
        navn = nid("visual", self.spec["id"], nokkel)
        v = {
            "$schema": f"{SKJEMA}/visualContainer/2.9.0/schema.json",
            "name": navn,
            "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
            "visual": visual,
        }
        if filtre:
            v["filterConfig"] = {"filters": filtre}
        if ekstra:
            v.update(ekstra)
        self.z += 1000
        self.visualer.append(v)
        return navn

    # tekst ----------------------------------------------------------------
    def tekst(self, nokkel, x, y, w, h, avsnitt, justering="left"):
        """avsnitt: liste av (tekst, skrift, pt, farge). Tom tekst gir luft."""
        par = []
        for t, skrift, pt, c in avsnitt:
            par.append({"textRuns": [{"value": t, "textStyle": {"fontFamily": skrift, "fontSize": f"{pt}pt",
                                                                "color": c}}],
                        "horizontalTextAlignment": justering})
        visual = {"visualType": "textbox",
                  "objects": {"general": [{"properties": {"paragraphs": par}}]},
                  "visualContainerObjects": {k: v for k, v in ingen_ramme().items()
                                             if k in ("background", "border", "padding")}}
        return self.legg(nokkel, x, y, w, h, visual)

    # kort ------------------------------------------------------------------
    def tall(self, nokkel, x, y, w, h, maalnavn, pt, c, skrift="Segoe UI Semibold", filtre=None, tom="–"):
        visual = {
            "visualType": "cardVisual",
            "query": {"queryState": {"Data": {"projections": [maal(maalnavn)]}}},
            "objects": {
                "value": [{"properties": {"fontSize": lit(f"{pt}D"), "fontFamily": lit(f"'{skrift}'"),
                                          "fontColor": farge(c), "horizontalAlignment": lit("'left'"),
                                          "showBlankAs": tekstlit(tom)},
                           "selector": {"id": "default"}}],
                "label": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
                "padding": [{"properties": {"paddingSelection": lit("'Custom'"), "paddingIndividual": lit("false"),
                                            "paddingUniform": lit("0L")}, "selector": {"id": "default"}}],
                "layout": [{"properties": {"paddingIndividual": lit("false"), "paddingUniform": lit("0L")},
                            "selector": {"id": "default"}}],
                "spacing": [{"properties": {"verticalSpacing": lit("2L")}, "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
                "fillCustom": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
                "accentBar": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
            },
            "visualContainerObjects": ingen_ramme(),
            "drillFilterOtherVisuals": True,
        }
        return self.legg(nokkel, x, y, w, h, visual, filtre)

    def aarfilter(self, nokkel):
        """Filter på visualnivå for sider som er låst til ett år (fast_aar i layout.py)."""
        aar = self.spec.get("fast_aar")
        return [filter_in("dim_aar", "År", [f"{aar}L"], nokkel)] if aar else []

    def kpi(self, i, k):
        x = L.kort_x(i) + 84
        y = L.KORT_Y
        self.tekst(f"kort{i}-etikett", x, y + 24, 316, 24, [(k["etikett"], "Segoe UI", 10.5, "#9AA8C7")])
        self.tall(f"kort{i}-verdi", x, y + 48, 316, 52, k["verdi"], 30, L.TEKST,
                  filtre=self.aarfilter(f"kort{i}-verdi"))
        self.tall(f"kort{i}-linje", x, y + 102, 316, 24, k["linje"], 10.5, k["linjefarge"],
                  skrift="Segoe UI Semibold", tom=" ", filtre=self.aarfilter(f"kort{i}-linje"))

    # diagrammer ----------------------------------------------------------
    def linje(self, nokkel, p, tittel, undertittel, maalnavn, regioner, filtre_ekstra=None):
        visual = {
            "visualType": "lineChart",
            "query": {"queryState": {
                "Category": {"projections": [kol("dim_aar", "År")]},
                "Series": {"projections": [kol("dim_region", "Region")]},
                "Y": {"projections": [maal(maalnavn)]},
            }, "sortDefinition": sortering("dim_aar", "År")},
            "objects": {
                **AKSER,
                "dataPoint": regionfarger(),
                "lineStyles": linjestiler(regioner),
            },
            "visualContainerObjects": diagramramme(tittel, undertittel),
            "drillFilterOtherVisuals": True,
        }
        filtre = [filter_in("dim_region", "Region", ["'" + r + "'" for r in regioner], nokkel)]
        filtre += filtre_ekstra or []
        navn = self.legg(nokkel, p["x"], p["y"], p["w"], p["h"], visual, filtre)
        self.ikke_filtrer.append(navn)
        return navn

    def stolper(self, nokkel, p, tittel, undertittel, typ, kategori, maalfarge, filtre, sorter=None,
                etiketter=True, totaler=True):
        visual = {
            "visualType": typ,
            "query": {"queryState": {
                "Category": {"projections": [kol(*kategori)]},
                "Y": {"projections": [maal(m, *navn) for m, _, *navn in maalfarge]},
            }, "sortDefinition": sorter or sortering(*kategori)},
            "objects": {
                **{k: v for k, v in AKSER.items() if k != "categoryAxis"},
                "categoryAxis": [{"properties": {"show": lit("true"), "labelColor": farge("#E8EEF9"),
                                                 "fontSize": lit("10.5D"), "showAxisTitle": lit("false"),
                                                 "gridlineShow": lit("false"), "innerPadding": lit("30L")}}],
                "dataPoint": maalfarger([(m, c) for m, c, *_ in maalfarge]),
                "labels": [{"properties": {"show": lit("true" if etiketter else "false"), "color": farge("#0B1222"),
                                           "fontSize": lit("9D"), "labelPrecision": lit("0L")}}],
                "totals": [{"properties": {"show": lit("true" if totaler else "false"), "color": farge("#E8EEF9"),
                                           "fontSize": lit("10D")}}],
            },
            "visualContainerObjects": diagramramme(tittel, undertittel),
            "drillFilterOtherVisuals": True,
        }
        return self.legg(nokkel, p["x"], p["y"], p["w"], p["h"], visual, filtre)

    def regionstolper(self, nokkel, x, y, w, h, tittel, maalnavn, filtre):
        """Liggende søyler med én måling, én søyle per region i regionens farge og verdien ved enden."""
        visual = {
            "visualType": "barChart",
            "query": {"queryState": {
                "Category": {"projections": [kol("dim_region", "Region")]},
                "Y": {"projections": [maal(maalnavn)]},
            }, "sortDefinition": sortering("dim_region", "Region")},
            "objects": {
                "categoryAxis": [{"properties": {"show": lit("true"), "labelColor": farge("#E8EEF9"),
                                                 "fontSize": lit("10D"), "showAxisTitle": lit("false"),
                                                 "gridlineShow": lit("false"), "innerPadding": lit("28L")}}],
                "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
                "legend": [{"properties": {"show": lit("false")}}],
                "dataPoint": stolpefarger(),
                "labels": [{"properties": {"show": lit("true"), "color": farge("#E8EEF9"), "fontSize": lit("10D"),
                                           "labelPrecision": lit("0L"), "labelPosition": lit("'OutsideEnd'")}}],
            },
            "visualContainerObjects": {
                **{k: v for k, v in diagramramme(tittel, "").items() if k != "subTitle"},
                "subTitle": [{"properties": {"show": lit("false")}}],
                "padding": [{"properties": {"top": lit("6D"), "bottom": lit("6D"), "left": lit("14D"),
                                            "right": lit("14D")}}],
                "title": [{"properties": {"show": lit("true"), "text": tekstlit(tittel), "fontSize": lit("11D"),
                                          "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": farge("#C9D3E8")}}],
            },
            "drillFilterOtherVisuals": True,
        }
        return self.legg(nokkel, x, y, w, h, visual, filtre)

    def foss(self, nokkel, p, tittel, undertittel, kategori, maalnavn, filtre):
        visual = {
            "visualType": "waterfallChart",
            "query": {"queryState": {
                "Category": {"projections": [kol(*kategori)]},
                "Y": {"projections": [maal(maalnavn)]},
            }, "sortDefinition": sortering(*kategori)},
            "objects": {
                "categoryAxis": [{"properties": {"show": lit("true"), "labelColor": farge("#C9D3E8"),
                                                 "fontSize": lit("10D"), "showAxisTitle": lit("false")}}],
                "valueAxis": AKSER["valueAxis"],
                "legend": [{"properties": {"show": lit("false")}}],
                "sentimentColors": [{"properties": {"increaseFill": farge(L.ROSA), "decreaseFill": farge(L.TURKIS),
                                                    "totalFill": farge(L.INDIGO)}}],
                "labels": [{"properties": {"show": lit("true"), "color": farge("#E8EEF9"), "fontSize": lit("10D"),
                                           "labelPrecision": lit("1L")}}],
            },
            "visualContainerObjects": diagramramme(tittel, undertittel),
            "drillFilterOtherVisuals": True,
        }
        return self.legg(nokkel, p["x"], p["y"], p["w"], p["h"], visual, filtre)

    def kombi(self, nokkel, p, tittel, undertittel, soyler, linje):
        visual = {
            "visualType": "lineClusteredColumnComboChart",
            "query": {"queryState": {
                "Category": {"projections": [kol("dim_aar", "År")]},
                "Y": {"projections": [maal(m, navn) for m, _, navn in soyler]},
                "Y2": {"projections": [maal(linje[0], linje[2])]},
            }, "sortDefinition": sortering("dim_aar", "År")},
            "objects": {
                **AKSER,
                # Faste akser: søylene går opp til rundt to tredjedeler, og årsverklinjen
                # (50-59) ligger over dem, så etikettene ikke kolliderer.
                "valueAxis": [{"properties": {**AKSER["valueAxis"][0]["properties"],
                                              "start": lit("0D"), "end": lit("160D"),
                                              "secShow": lit("true"), "secLabelColor": farge(L.GULL),
                                              "secFontSize": lit("9D"), "secStart": lit("0D"), "secEnd": lit("66D")}}],
                "dataPoint": maalfarger([(m, c) for m, c, _ in list(soyler) + [linje]]),
                "lineStyles": [{"properties": {"strokeWidth": lit("3D"), "showMarker": lit("true"),
                                               "markerSize": lit("6D")}}],
                "labels": [{"properties": {"show": lit("true"), "color": farge("#E8EEF9"), "fontSize": lit("9D"),
                                           "labelPrecision": lit("1L")}},
                           {"properties": {"labelPrecision": lit("0L"), "labelPosition": lit("'Above'"),
                                           "color": farge(linje[1])},
                            "selector": {"metadata": f"_Mål.{linje[0]}"}}],
            },
            "visualContainerObjects": diagramramme(tittel, undertittel),
            "drillFilterOtherVisuals": True,
        }
        navn = self.legg(nokkel, p["x"], p["y"], p["w"], p["h"], visual)
        self.ikke_filtrer.append(navn)
        return navn

    def kart(self):
        r = L.KART_RUTE
        fargemaal = {"Measure": {"Expression": {"SourceRef": {"Entity": "_Mål"}}, "Property": "Farge kart"}}
        visual = {
            "visualType": "scatterChart",
            "query": {"queryState": {
                "Category": {"projections": [kol("dim_region", "Region")]},
                "X": {"projections": [maal("Kart X")]},
                "Y": {"projections": [maal("Kart Y")]},
                "Size": {"projections": [maal("Eiendomsforvaltning per innbygger")]},
                "Tooltips": {"projections": [maal("Forvaltning 121 per innbygger"), maal("Formålsbygg per innbygger")]},
            }},
            "objects": {
                "categoryAxis": [{"properties": {"show": lit("false"), "start": lit(f"{L.KART_X[0]}D"),
                                                 "end": lit(f"{L.KART_X[1]}D"), "gridlineShow": lit("false")}}],
                "valueAxis": [{"properties": {"show": lit("false"), "start": lit(f"{L.KART_Y[0]}D"),
                                              "end": lit(f"{L.KART_Y[1]}D"), "gridlineShow": lit("false")}}],
                "legend": [{"properties": {"show": lit("false")}}],
                "categoryLabels": [{"properties": {"show": lit("false")}}],
                "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": fargemaal}}}},
                               "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
                "bubbles": [{"properties": {"bubbleSize": lit("-20L")}}],
                "plotArea": [{"properties": {"transparency": lit("100D")}}],
            },
            "visualContainerObjects": ingen_ramme(),
            "drillFilterOtherVisuals": True,
        }
        return self.legg("kart", r["x"], r["y"], r["w"], r["h"], visual,
                         [filter_in("dim_region", "Regiontype", ["'kommune'"], "kart")])

    # faste deler --------------------------------------------------------
    def aarvelger(self):
        p = L.AARVELGER
        visual = {
            "visualType": "advancedSlicerVisual",
            "query": {"queryState": {"Values": {"projections": [kol("dim_aar", "År")]}}},
            "objects": {
                "general": [{"properties": {"filter": {"filter": {
                    "Version": 2, "From": [{"Name": "d", "Entity": "dim_aar", "Type": 0}],
                    "Where": [{"Condition": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "År"}}],
                        "Values": [[{"Literal": {"Value": "2025L"}}]]}}}]}}}}],
                "selection": [{"properties": {"singleSelect": lit("true"), "strictSingleSelect": lit("true")}}],
                "layout": [{"properties": {"rowCount": lit("1L"), "columnCount": lit("6L"), "cellPadding": lit("8L"),
                                           "maxTiles": lit("6L")}}],
                "shapeCustomRectangle": [{"properties": {"tileShape": lit("'rectangleRoundedByPixel'"),
                                                         "rectangleRoundedCurve": lit("10L")},
                                          "selector": {"id": "default"}}],
                "value": [{"properties": {"fontSize": lit("12D"), "fontFamily": lit("'Segoe UI Semibold'"),
                                          "fontColor": farge("#E8EEF9"), "horizontalAlignment": lit("'center'")},
                           "selector": {"id": "default"}}],
                "label": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
                "fillCustom": [
                    {"properties": {"show": lit("true"), "fillColor": farge("#FFFFFF"), "transparency": lit("94D")},
                     "selector": {"id": "default"}},
                    {"properties": {"fillColor": farge("#FFFFFF"), "transparency": lit("88D")},
                     "selector": {"id": "interaction:hover"}},
                    {"properties": {"fillColor": farge(L.TURKIS), "transparency": lit("80D")},
                     "selector": {"id": "selection:selected"}}],
                "outline": [
                    {"properties": {"show": lit("true"), "lineColor": farge("#FFFFFF"), "transparency": lit("85D"),
                                    "weight": lit("1D")}, "selector": {"id": "default"}},
                    {"properties": {"show": lit("true"), "lineColor": farge(L.TURKIS), "transparency": lit("0D"),
                                    "weight": lit("1D")}, "selector": {"id": "selection:selected"}}],
            },
            "visualContainerObjects": {k: v for k, v in ingen_ramme().items() if k != "dropShadow"},
            "syncGroup": {"groupName": "Aar", "fieldChanges": True, "filterChanges": True},
        }
        return self.legg("aarvelger", p["x"], p["y"], p["w"], p["h"], visual)

    def navigasjon(self):
        for i, s in enumerate(L.SIDER):
            y = L.NAV_Y0 + i * L.NAV_STEG
            visual = {
                "visualType": "actionButton",
                "objects": {
                    "text": [{"properties": {"show": lit("false")}}],
                    "icon": [{"properties": {"show": lit("false")}},
                             {"properties": {"shapeType": lit("'blank'"), "placement": lit("'left'")},
                              "selector": {"id": "default"}}],
                    "fill": [{"properties": {"show": lit("true")}},
                             {"properties": {"fillColor": farge("#FFFFFF"), "transparency": lit("100D")},
                              "selector": {"id": "default"}},
                             {"properties": {"fillColor": farge("#FFFFFF"), "transparency": lit("93D")},
                              "selector": {"id": "hover"}},
                             {"properties": {"fillColor": farge(L.TURKIS), "transparency": lit("88D")},
                              "selector": {"id": "selected"}}],
                    "outline": [{"properties": {"show": lit("false")}}],
                    "shape": [{"properties": {"tileShape": lit("'rectangleRounded'"), "roundEdge": lit("14L")}},
                              {"properties": {"tileShape": lit("'rectangleRounded'")}, "selector": {"id": "default"}}],
                },
                "visualContainerObjects": {
                    "background": [{"properties": {"show": lit("false")}}],
                    "border": [{"properties": {"show": lit("false")}}],
                    "padding": [{"properties": {"top": lit("0D"), "bottom": lit("0D"), "left": lit("0D"),
                                                "right": lit("0D")}}],
                    "visualLink": [{"properties": {"show": lit("true"), "type": lit("'PageNavigation'"),
                                                   "navigationSection": lit(f"'{SIDE_ID[s['id']]}'"),
                                                   "tooltip": tekstlit(s["navn"])}}],
                },
                "drillFilterOtherVisuals": True,
            }
            self.legg(f"nav-{s['id']}", L.NAV_KNAPP["x"], y, L.NAV_KNAPP["w"], L.NAV_KNAPP["h"], visual,
                      ekstra={"howCreated": "InsertVisualButton"})

    def topp_og_bunn(self):
        t, u, b = L.TITTEL, L.UNDERTITTEL, L.BUNN
        self.tekst("tittel", t["x"], t["y"], t["w"], t["h"], [(self.spec["tittel"], "Segoe UI Semibold", 24, L.TEKST)])
        self.tekst("undertittel", u["x"], u["y"], u["w"], u["h"],
                   [(self.spec["undertittel"], "Segoe UI", 11, "#AEB9D1")])
        self.tekst("kilder", b["x"], b["y"], b["w"], b["h"], [(L.KILDER, "Segoe UI", 8.5, "#6B7A99")])

    # side.json -------------------------------------------------------------
    def page_json(self, aarvelger_navn):
        bilde = f"bg-{self.spec['id']}.png"
        objekter = {
            "background": [{"properties": {
                "image": {"image": {"name": tekstlit(bilde),
                                    "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources",
                                                                             "PackageType": 1, "ItemName": bilde}}},
                                    "scaling": lit("'Fit'")}},
                "color": farge(L.BG), "transparency": lit("0D")}}],
            "outspace": [{"properties": {"color": farge("#070C17"), "transparency": lit("0D")}}],
        }
        side = {
            "$schema": f"{SKJEMA}/page/2.1.0/schema.json",
            "name": SIDE_ID[self.spec["id"]],
            "displayName": self.spec["navn"],
            "displayOption": "FitToPage",
            "height": L.H,
            "width": L.B,
            "objects": objekter,
        }
        if aarvelger_navn and self.ikke_filtrer:
            side["visualInteractions"] = [{"source": aarvelger_navn, "target": m, "type": "NoFilter"}
                                          for m in self.ikke_filtrer]
        return side


# --------------------------------------------------------------------------- sidene

MOSS = lambda n: [filter_in("dim_region", "Region", ["'Moss'"], n)]  # noqa: E731
SEKS = ["Moss", "KOSTRA-gruppe 11", "Østfold", "Sarpsborg", "Fredrikstad", "Halden"]


def side_oversikt(s):
    p = s.spec["paneler"]
    s.linje("linje", p["linje"], "Moss har ligget under KOSTRA-gruppe 11 hvert år siden 2020",
            "Eiendomsforvaltning per innbygger, kroner. Østfold 2020–2023 er beregnet fra de tolv kommunene.",
            "Eiendomsforvaltning per innbygger", SEKS)
    # To søylediagram side om side, hvert med egen skala, under én felles overskrift.
    q = p["stolper"]
    s.tekst("stolper-tittel", q["x"] + 22, q["y"] + 14, q["w"] - 44, 28,
            [("Moss ligger over gruppen på 121 og under på byggene", "Segoe UI Semibold", 13, "#E8EEF9")])
    s.tekst("stolper-undertittel", q["x"] + 22, q["y"] + 40, q["w"] - 44, 22,
            [("Valgt år, kroner per innbygger. Formålsbyggene er eiendomsforvaltningen minus 121.",
              "Segoe UI", 10, L.DEMPET)])
    halv = (q["w"] - 16) // 2
    for i, (nokkel, tittel, maalnavn) in enumerate([
        ("stolper", "Forvaltning (121)", "Forvaltning 121 per innbygger"),  # samme navn som før, samme mappe
        ("stolperbygg", "Formålsbyggene", "Formålsbygg per innbygger"),
    ]):
        s.regionstolper(nokkel, q["x"] + 8 + i * halv, q["y"] + 64, halv, q["h"] - 70, tittel, maalnavn,
                        [filter_in("dim_region", "I utvalget", ["true"], nokkel)])
    k = p["kart"]
    s.tekst("kart-tittel", k["x"] + 22, k["y"] + 18, k["w"] - 44, 26,
            [("Østfold-kommunene", "Segoe UI Semibold", 13, "#E8EEF9")])
    s.tekst("kart-undertittel", k["x"] + 22, k["y"] + 44, k["w"] - 44, 40,
            [("Eiendomsforvaltning per innbygger i valgt år. Størrelsen er kroner per innbygger; "
              "rosa bruker mer enn Moss, indigo mindre.", "Segoe UI", 10, L.DEMPET)])
    s.kart()


def side_f121(s):
    p = s.spec["paneler"]
    s.foss("bro_art", p["bro_art"], "Lønn, pensjon og arbeidsgiveravgift står for hele økningen på 121",
           "Moss, funksjon 121. Endring fra 2024 til 2025 per art, millioner kroner.",
           ("fact_art", "Art"), "Endring art (mill.)",
           MOSS("bro_art") + [filter_in("dim_funksjon", "Funksjon", ["'Forvaltning (121)'"], "bro_art")]
           + s.aarfilter("bro_art"))
    s.foss("bro_funksjon", p["bro_funksjon"], "Byggene falt nesten like mye som 121 steg",
           "Moss, korrigerte brutto driftsutgifter. Endring fra 2024 til 2025 per funksjon, millioner kroner.",
           ("dim_funksjon", "Funksjon"), "Endring mot året før (mill.)",
           MOSS("bro_funksjon") + [filter_in("dim_funksjon", "Er aggregat", ["false"], "bro_funksjon")]
           + s.aarfilter("bro_funksjon"))
    s.linje("linje121", p["linje121"], "Avviket mot gruppen ble mer enn doblet i 2025",
            "Funksjon 121 per innbygger, kroner.",
            "Forvaltning 121 per innbygger", ["Moss", "KOSTRA-gruppe 11", "Østfold"])
    s.kombi("personal", p["personal"], "I 2025 kom ett årsverk til, men lønnen på 121 ble mer enn doblet",
            "Moss, lønn, pensjon og arbeidsgiveravgift, millioner kroner. Linjen er årsverk i MKEiendom.",
            [("Moss 121 personal (mill.)", L.ROSA, "Funksjon 121"),
             ("Moss formålsbygg personal (mill.)", L.SKIFER, "Formålsbyggene")],
            ("Årsverk MKEiendom", L.GULL, "Årsverk i MKEiendom"))


def side_bygg(s):
    p = s.spec["paneler"]
    s.linje("linje_kvm", p["linje_kvm"], "Moss lå over gruppen i 2020, men har fulgt den siden",
            "Korrigerte brutto driftsutgifter på formålsbyggene per m² samlet areal, kroner.",
            "Formålsbygg kr per m²", SEKS)
    s.linje("linje_energi", p["linje_energi"], "Energitoppen i 2022 ble lavere i Moss enn i gruppen",
            "Energiutgifter per m² eid areal, kroner.", "Energi kr per m²", SEKS)
    s.stolper("fdv", p["fdv"], "Hva en m² koster: energi, renhold, drift og vedlikehold",
              "Valgt år, kroner per m² eid areal. Moss har brukt mer på vedlikehold enn KOSTRA-gruppe 11 "
              "hvert år siden 2020.",
              "columnChart", ("dim_region", "Region"),
              [("Energi kr per m²", L.GULL, "Energi"), ("Renhold kr per m²", L.HIMMEL, "Renhold"),
               ("Drift ellers kr per m²", L.INDIGO, "Drift ellers"), ("Vedlikehold kr per m²", L.ROSA, "Vedlikehold")],
              [filter_in("dim_region", "I utvalget", ["true"], "fdv")])


METODE_TEKST = {
    "tekst_a": ("Hva som er målt", [
        "Eiendomsforvaltning er KOSTRA-funksjon 121 Forvaltningsutgifter og de seks formålsbyggene: "
        "administrasjonslokaler, barnehager, skoler, institusjoner, idrettsbygg og kulturbygg. SSB kaller "
        "summen FGK6a.",
        "Tallene gjelder kommunekonsernet, altså Moss kommune og foretakene, slik kommunedirektøren også "
        "bruker dem. På funksjon 121 har kommunekassen ingen lønn, så lønnen der er foretakenes.",
        "Per innbygger er netto driftsutgifter. Kronebeløpene og kroner per m² er korrigerte brutto "
        "driftsutgifter, som SSB bruker for bygg.",
        "Kroner per m² er delt på samlet areal, eid og leid. For drift og vedlikehold bruker SSB bare eid areal.",
    ]),
    "tekst_b": ("Kommunenummer og Østfold", [
        "Kommunene i Østfold fikk nye nummer i 2024, fra 30xx til 31xx. Modellen fører 2020–2023 over "
        "til dagens nummer, og en test sjekker at alle seks regionene har tall for alle år.",
        "Østfold fylke finnes i KOSTRA først fra 2024. For 2020–2023 er fylket bygget opp av de tolv "
        "kommunene med samme regel som SSB: sum kroner delt på sum innbyggere eller areal. For 2024 og "
        "2025 gir regelen SSBs egne fylkestall, innenfor én krone per innbygger.",
        "For barnehager, skoler og institusjoner regner SSB per innbygger i målgruppen. De tallene er "
        "ikke brukt per innbygger her.",
        "Befolkningen telles 1. januar. KOSTRA deler på innbyggerne 31. desember i regnskapsåret, så 2025 "
        "deles på folketallet 1.1.2026.",
    ]),
    "tekst_c": ("Forbehold", [
        "KOSTRA viser hvor utgiftene er ført, ikke hvorfor. Regnskapet viser at personalkostnadene steg "
        "på 121 og falt på byggene. Om det skyldes ny føringspraksis eller annet arbeid, må sjekkes i "
        "MKEiendoms regnskap og lønnssystem.",
        "Drifts- og investeringsanalysen 2027–2030 brukte foreløpige tall fra mars 2026 og fant 105 prosent. "
        "Med SSBs tall slik de ligger nå, er avviket 106 prosent.",
        "Konsernet er mer enn MKEiendom. På byggene har også kommunekassen lønn, så nedgangen i lønn på "
        "byggene gjelder hele konsernet.",
        "Årsverkene er fra Moss kommunes årsrapporter for 2024 og 2025.",
    ]),
}


def side_metode(s, antall_tester):
    p = s.spec["paneler"]
    for nokkel, (overskrift, avsnitt) in METODE_TEKST.items():
        q = p[nokkel]
        innhold = [(overskrift, "Segoe UI Semibold", 15, "#E8EEF9"), ("", "Segoe UI", 7, L.TEKST2)]
        for a in avsnitt:
            innhold += [(a, "Segoe UI", 12, "#C9D3E8"), ("", "Segoe UI", 7, L.TEKST2)]
        s.tekst(nokkel, q["x"] + 26, q["y"] + 22, q["w"] - 52, q["h"] - 40, innhold)

    k = p["kontroll"]
    del_b = k["w"] / 4
    etiketter = [
        ("Sju funksjoner mot SSBs sum (FGK6a)", "Kontroll aggregat mot deler", None),
        ("Artene mot hovedtabellen, fire byer", "Kontroll art mot hovedtabell",
         [filter_in("dim_region", "Regiontype", ["'kommune'"], "kontroll2"),
          filter_in("dim_region", "I utvalget", ["true"], "kontroll2")]),
        ("Tester i dbt", None, None),
        ("Datagrunnlag", "Data til og med", None),
    ]
    for i, (etikett, m, filtre) in enumerate(etiketter):
        x = int(k["x"] + i * del_b + 84)
        s.tekst(f"kontroll{i}-etikett", x, k["y"] + 30, int(del_b) - 100, 22, [(etikett, "Segoe UI", 10.5, "#9AA8C7")])
        if m:
            s.tall(f"kontroll{i}-verdi", x, k["y"] + 56, int(del_b) - 100, 48, m, 24, L.TEKST, filtre=filtre)
        else:
            s.tekst(f"kontroll{i}-verdi", x, k["y"] + 54, int(del_b) - 100, 48,
                    [(f"{antall_tester} av {antall_tester} bestått", "Segoe UI Semibold", 24, L.TEKST)])


# --------------------------------------------------------------------------- skriving

def skriv_json(sti, data):
    sti.parent.mkdir(parents=True, exist_ok=True)
    sti.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def tema():
    kilde = json.loads((Path(__file__).resolve().parent / "tema.json").read_text(encoding="utf-8"))
    kilde["name"] = TEMA
    return kilde


def main(antall_tester="?"):
    import csv
    for r in csv.DictReader(open(ROT / "seeds" / "region.csv", encoding="utf-8")):
        if r["i_utvalg"] == "1":
            REGIONFARGER[r["region_navn"]] = r["farge"]

    if DEF.exists():
        shutil.rmtree(DEF)
    sider = []
    for spec in L.SIDER:
        s = Side(spec)
        s.topp_og_bunn()
        for i, k in enumerate(spec["kort"]):
            s.kpi(i, k)
        {"oversikt": side_oversikt, "f121": side_f121, "bygg": side_bygg}.get(
            spec["id"], lambda s_: side_metode(s_, antall_tester))(s)
        velger = s.aarvelger() if spec["aarvelger"] else None
        s.navigasjon()
        sider.append(s)
        skriv_json(DEF / "pages" / SIDE_ID[spec["id"]] / "page.json", s.page_json(velger))
        for v in s.visualer:
            skriv_json(DEF / "pages" / SIDE_ID[spec["id"]] / "visuals" / v["name"] / "visual.json", v)

    skriv_json(DEF / "pages" / "pages.json", {
        "$schema": f"{SKJEMA}/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [SIDE_ID[s["id"]] for s in L.SIDER],
        "activePageName": SIDE_ID["oversikt"],
    })
    skriv_json(DEF / "version.json", {"$schema": f"{SKJEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    bilder = [f"bg-{s['id']}.png" for s in L.SIDER]
    skriv_json(DEF / "report.json", {
        "$schema": f"{SKJEMA}/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASETEMA, "reportVersionAtImport": {"visual": "2.11.0", "report": "3.4.0",
                                                                     "page": "2.3.1"}, "type": "SharedResources"},
            "customTheme": {"name": TEMA, "reportVersionAtImport": {"visual": "2.11.0", "report": "3.4.0",
                                                                    "page": "2.3.1"}, "type": "RegisteredResources"},
        },
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASETEMA, "path": f"BaseThemes/{BASETEMA}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": TEMA, "path": TEMA, "type": "CustomTheme"}]
             + [{"name": b, "path": b, "type": "Image"} for b in bilder]},
        ],
        # Norsk tallformat i alle visualer uansett språk på maskinen, og ingen K/M-forkortelser.
        "settings": {"locale": "nb-NO", "defaultDisplayUnitsToNone": True,
                     "useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    })
    skriv_json(RES / "RegisteredResources" / TEMA, tema())
    base = Path(__file__).resolve().parent / f"{BASETEMA}.json"
    (RES / "SharedResources" / "BaseThemes").mkdir(parents=True, exist_ok=True)
    shutil.copy(base, RES / "SharedResources" / "BaseThemes" / f"{BASETEMA}.json")
    skriv_json(RAPP / "definition.pbir", {
        "$schema": f"{SKJEMA}Properties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAVN}.SemanticModel"}},
    })
    skriv_json(RAPP / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAVN},
        "config": {"version": "2.0", "logicalId": "3f0c2a8e-7b1d-5c4e-9a6f-" + nid("rapport")[:12]},
    })
    skriv_json(ROT / "powerbi" / f"{NAVN}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAVN}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })
    n = sum(len(s.visualer) for s in sider)
    print(f"Skrev {RAPP.relative_to(ROT)}: {len(sider)} sider, {n} visualer")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "?")
