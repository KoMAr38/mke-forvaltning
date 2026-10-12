"""
Eksporterer mart-laget til data/mart/*.csv for Power BI og skriver
data/mart/manifest.json med radantall og sha256 per fil.
"""
import hashlib
import json
from pathlib import Path

import duckdb

ROT = Path(__file__).resolve().parents[1]
DB = ROT / "data" / "mke_forvaltning.duckdb"
MART = ROT / "data" / "mart"
TABELLER = ["dim_region", "dim_aar", "dim_funksjon", "fact_eiendom", "fact_art", "fact_fdv", "fact_mke_aarsverk"]


def main():
    MART.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    manifest = {}
    for t in TABELLER:
        sti = MART / f"{t}.csv"
        con.execute(
            f"copy (select * from marts.{t} order by all) to '{sti.as_posix()}' (header, delimiter ',')"
        )
        n = con.execute(f"select count(*) from marts.{t}").fetchone()[0]
        manifest[t] = {"rader": n, "sha256": hashlib.sha256(sti.read_bytes()).hexdigest()}
        print(f"{t}.csv: {n} rader")
    (MART / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
