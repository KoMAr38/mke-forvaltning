"""
Henter KOSTRA-tall for eiendomsforvaltningen fra SSBs statistikkbank (API v0,
json-stat2) og skriver dem som flate CSV-filer til data/raw/ssb/.
Kun standardbiblioteket.

Tabeller
  12559  Hovedøkonomi for kommunal eiendomsforvaltning (kroner, per innbygger, per m²)
  12367  Detaljerte regnskapstall, driftsregnskapet, konsern og kasse (art for art)
  12905  Utgifter til forvaltning, drift og vedlikehold (energi, renhold, vedlikehold)
  11906  Areal for kommunale formålsbygg
  06913  Befolkning 1. januar (til Østfold 2020-2023, se README)

Utvalget er Østfold-kommunene under begge nummerseriene (30xx 2020-2023,
31xx fra 2024), KOSTRA-gruppe 11, Østfold fylke (fra 2024) og landet.
Manifest med sha256 og uttrekkstidspunkt skrives til data/raw/ssb/manifest.json.
"""
import csv
import hashlib
import itertools
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://data.ssb.no/api/v0/no/table/{}"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "ssb"

AAR = ["2020", "2021", "2022", "2023", "2024", "2025"]
KOMMUNER_GAMLE = ["3001", "3002", "3003", "3004", "3011", "3012",
                  "3013", "3014", "3015", "3016", "3017", "3018"]
KOMMUNER_NYE = ["3101", "3103", "3105", "3107", "3110", "3112",
                "3114", "3116", "3118", "3120", "3122", "3124"]
REGIONER = KOMMUNER_GAMLE + KOMMUNER_NYE + ["EKG11", "EKA31", "EAK"]
BYGG = ["130", "221", "222", "261", "381", "386"]

UTTREKK = {
    "hovedokonomi": ("12559", {
        "KOKkommuneregion0000": REGIONER,
        "KOKfunksjon0000": ["121", "FGK6", "FGK6a"] + BYGG,
        "KOKart0000": ["AGD2", "AGD4", "AGD10"],
        "ContentsCode": ["KOSbelop0000", "KOSbelopperinnby0000", "KOSbelopperkvm0000"],
        "Tid": AAR,
    }),
    "detaljregnskap": ("12367", {
        "KOKkommuneregion0000": REGIONER,
        "KOKregnskapsomfa0000": ["A", "B"],
        "KOKfunksjon0000": ["121"] + BYGG,
        "KOKart0000": ["*"],
        "ContentsCode": ["KOSbelop0000"],
        "Tid": AAR,
    }),
    "fdv": ("12905", {
        "KOKkommuneregion0000": REGIONER,
        "KOKfunksjon0000": ["121", "FGK6"] + BYGG,
        "KOKart0000": ["*"],
        "ContentsCode": ["KOSbelop0000", "KOSbelopperkvm0000"],
        "Tid": AAR,
    }),
    "areal": ("11906", {
        "KOKkommuneregion0000": REGIONER,
        "KOKeieform0000": ["samlet", "eid", "leid"],
        "KOKfunksjon0000": ["FGK6"] + BYGG,
        "ContentsCode": ["KOSareal0000"],
        "Tid": AAR,
    }),
    "befolkning": ("06913", {
        "Region": KOMMUNER_GAMLE + KOMMUNER_NYE,
        "ContentsCode": ["Folkemengde"],
        "Tid": AAR + ["2026"],
    }),
}


def hent(url, body=None, forsok=5):
    for i in range(forsok):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode() if body else None,
                headers={"Content-Type": "application/json", "User-Agent": "mke-forvaltning/1.0"},
                method="POST" if body else "GET",
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            vent = 2 ** i
            print(f"  feil ({e}), prøver igjen om {vent}s", file=sys.stderr)
            time.sleep(vent)
    raise SystemExit(f"Ga opp: {url}")


def sporring(utvalg):
    q = []
    for kode, verdier in utvalg.items():
        if verdier == ["*"]:
            q.append({"code": kode, "selection": {"filter": "all", "values": ["*"]}})
        else:
            q.append({"code": kode, "selection": {"filter": "item", "values": verdier}})
    return {"query": q, "response": {"format": "json-stat2"}}


def til_rader(js):
    dims = js["id"]
    kategorier = [list(js["dimension"][d]["category"]["index"].keys()) for d in dims]
    etiketter = [js["dimension"][d]["category"]["label"] for d in dims]
    rader = []
    for i, kombo in enumerate(itertools.product(*kategorier)):
        v = js["value"][i]
        rad = {}
        for d, kode, lab in zip(dims, kombo, etiketter):
            if d == "ContentsCode":
                rad["statistikkvariabel"] = kode
            else:
                rad[d] = kode
                rad[f"{d}_tekst"] = lab[kode]
        rad["verdi"] = "" if v is None else v
        rader.append(rad)
    return rader


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {"uttrekkstidspunkt": datetime.now(timezone.utc).isoformat(), "tabeller": {}}
    for navn, (tabell, utvalg) in UTTREKK.items():
        print(f"{tabell} -> {navn}.csv")
        js = hent(API.format(tabell), sporring(utvalg))
        rader = til_rader(js)
        sti = RAW / f"{navn}.csv"
        with open(sti, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rader[0].keys()))
            w.writeheader()
            w.writerows(rader)
        sha = hashlib.sha256(sti.read_bytes()).hexdigest()
        manifest["tabeller"][tabell] = {
            "fil": sti.name,
            "tittel": js["label"],
            "rader": len(rader),
            "sist_oppdatert_ssb": js.get("updated"),
            "sha256": sha,
        }
        print(f"  {len(rader)} rader, sha256 {sha[:12]}")
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Ferdig.")


if __name__ == "__main__":
    main()
