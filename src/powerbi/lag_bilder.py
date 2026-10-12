"""
Tegner bakgrunnsbildene til rapporten (1920 × 1080, én per side): nordlysbakgrunn,
navigasjon til venstre, rammene rundt kort og paneler, ikoner, kartet over Østfold
og flytdiagrammet på metodesiden. Visualene i Power BI ligger oppå med
gjennomsiktig bakgrunn, så rammene her og posisjonene i lag_rapport.py må stemme.

Tegner i dobbel oppløsning og skalerer ned, så kanter og tekst blir glatte.
"""
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402

ROT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent / "assets"
UT = ROT / "powerbi" / "MKE_Eiendomsforvaltning.Report" / "StaticResources" / "RegisteredResources"
S = 2  # tegneskala

IKON = {l.split()[0]: chr(int(l.split()[1], 16))
        for l in (ASSETS / "ikoner.txt").read_text().splitlines() if l.strip()}


def font(navn, px):
    return ImageFont.truetype(str(ASSETS / navn), int(px * S))


def rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ss(*v):
    return [int(round(x * S)) for x in v]


# --------------------------------------------------------------------------- bakgrunn

def nordlys(seed):
    """Mørk bunn med myke lysflater og svake høydekoter."""
    rng = np.random.default_rng(seed)
    w, h = L.B * S, L.H * S
    bunn = Image.new("RGBA", (w, h), rgb(L.BG))

    # Lysflater: tegnet i lav oppløsning, uskarpe, skalert opp.
    lw, lh = 192, 108
    flater = [
        (0.22, 0.05, 0.42, 0.20, L.TURKIS, 0.16),
        (0.80, 0.10, 0.38, 0.22, L.INDIGO, 0.15),
        (0.62, 0.95, 0.40, 0.18, L.ROSA, 0.05),
        (0.05, 0.90, 0.30, 0.20, L.INDIGO, 0.07),
    ]
    lag = np.zeros((lh, lw, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:lh, 0:lw]
    for cx, cy, rx, ry, farge, styrke in flater:
        cx += rng.uniform(-0.03, 0.03)
        d = ((xx / lw - cx) / rx) ** 2 + ((yy / lh - cy) / ry) ** 2
        a = np.exp(-d * 2.2) * styrke
        r, g, b, _ = rgb(farge)
        for i, c in enumerate((r, g, b)):
            lag[..., i] = lag[..., i] * (1 - a) + c * a
        lag[..., 3] = 1 - (1 - lag[..., 3]) * (1 - a)
    rgb_del = np.where(lag[..., 3:4] > 0, lag[..., :3] / np.maximum(lag[..., 3:4], 1e-6), 0)
    lys = np.concatenate([rgb_del, lag[..., 3:4] * 255], axis=2).clip(0, 255).astype(np.uint8)
    lys = Image.fromarray(lys, "RGBA").resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30 * S))
    bunn = Image.alpha_composite(bunn, lys)

    # Høydekoter: glatt støyfelt, konturer med lav dekning.
    gx, gy = np.meshgrid(np.linspace(0, 1, 240), np.linspace(0, 1, 135))
    felt = np.zeros_like(gx)
    for _ in range(9):
        felt += rng.uniform(0.4, 1.0) * np.exp(-(((gx - rng.uniform()) / rng.uniform(0.1, 0.35)) ** 2
                                                  + ((gy - rng.uniform()) / rng.uniform(0.1, 0.35)) ** 2))
    fig = plt.figure()
    cs = plt.contour(gx, gy, felt, levels=22)
    segs = cs.allsegs
    plt.close(fig)
    koter = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(koter)
    for nivaa in segs:
        for seg in nivaa:
            if len(seg) < 2:
                continue
            pts = [(float(x) * w, float(y) * h) for x, y in seg]
            d.line(pts, fill=(255, 255, 255, 9), width=S)
    return Image.alpha_composite(bunn, koter)


# --------------------------------------------------------------------------- byggeklosser

def panel(img, x, y, w, h, r=16, aksent=None):
    lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    d.rounded_rectangle(ss(x, y, x + w, y + h), radius=r * S, fill=(255, 255, 255, 10),
                        outline=(255, 255, 255, 22), width=S)
    # lys kant øverst
    topp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(topp)
    farge = rgb(aksent or "#FFFFFF", 70 if aksent else 26)
    for i in range(int(w * S * 0.6)):
        a = int(farge[3] * (1 - i / (w * S * 0.6)))
        td.point((x * S + r * S + i, y * S), fill=farge[:3] + (a,))
        td.point((x * S + r * S + i, y * S + 1), fill=farge[:3] + (a,))
    lag = Image.alpha_composite(lag, topp)
    return Image.alpha_composite(img, lag)


def ikon(d, navn, cx, cy, px, farge):
    f = font("MaterialIcons-Regular.ttf", px)
    d.text((cx * S, cy * S), IKON[navn], font=f, fill=rgb(farge), anchor="mm")


def ikonring(img, cx, cy, r, navn, farge):
    lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    d.ellipse(ss(cx - r, cy - r, cx + r, cy + r), fill=rgb(farge, 34), outline=rgb(farge, 110), width=S)
    ikon(d, navn, cx, cy, r * 1.05, farge)
    return Image.alpha_composite(img, lag)


def navigasjon(img, aktiv):
    lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    d.rectangle(ss(0, 0, L.NAV_B, L.H), fill=(10, 16, 30, 215))
    d.line(ss(L.NAV_B, 0, L.NAV_B, L.H), fill=(255, 255, 255, 16), width=S)

    # Merke: et avrundet kvadrat med bygning, ikke MKEiendoms logo.
    merke = Image.new("RGBA", ss(56, 56)[0:1] * 2, (0, 0, 0, 0))
    g = np.linspace(0, 1, merke.size[0])
    t, i_ = np.array(rgb(L.TURKIS)[:3]), np.array(rgb(L.INDIGO)[:3])
    grad = np.zeros((merke.size[1], merke.size[0], 4), dtype=np.uint8)
    for yy in range(merke.size[1]):
        for c in range(3):
            grad[yy, :, c] = (t[c] * (1 - (g + yy / merke.size[1]) / 2) + i_[c] * ((g + yy / merke.size[1]) / 2))
    grad[..., 3] = 255
    grad_img = Image.fromarray(grad, "RGBA")
    maske = Image.new("L", merke.size, 0)
    ImageDraw.Draw(maske).rounded_rectangle((0, 0, merke.size[0] - 1, merke.size[1] - 1), radius=14 * S, fill=255)
    lag.paste(grad_img, ss(28, 24), maske)
    ikon(d, "apartment", 56, 52, 30, "#FFFFFF")

    tf_aktiv = font("Inter-SemiBold.otf", 11)
    tf = font("Inter-Medium.otf", 11)
    for i, side in enumerate(L.SIDER):
        y0 = L.NAV_Y0 + i * L.NAV_STEG
        er_aktiv = side["id"] == aktiv
        if er_aktiv:
            d.rounded_rectangle(ss(8, y0, 104, y0 + 80), radius=14 * S, fill=rgb(L.TURKIS, 30),
                                outline=rgb(L.TURKIS, 70), width=S)
            d.rounded_rectangle(ss(0, y0 + 18, 4, y0 + 62), radius=2 * S, fill=rgb(L.TURKIS))
        farge = L.TURKIS if er_aktiv else "#8592AE"
        ikon(d, side["ikon"], 56, y0 + 30, 26, farge)
        d.text((56 * S, (y0 + 60) * S), side["navn"], font=tf_aktiv if er_aktiv else tf,
               fill=rgb(L.TEKST if er_aktiv else "#8592AE"), anchor="mm")
    return Image.alpha_composite(img, lag)


def kort(img, side):
    for i, k in enumerate(side["kort"]):
        x = L.kort_x(i)
        img = panel(img, x, L.KORT_Y, L.KORT_B, L.KORT_H, aksent=k["farge"])
        img = ikonring(img, x + 46, L.KORT_Y + 50, 22, k["ikon"], k["farge"])
    return img


def fast_periode(img, aar):
    """For sider som er låst til ett år: to fliser i årsvelgerens stil der velgeren ellers står."""
    p = L.AARVELGER
    flis_b, flis_h, pad = 79, 44, 8
    y = p["y"] + pad
    x2 = p["x"] + p["w"] - pad - flis_b
    x1 = x2 - 44 - flis_b
    lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    d.rounded_rectangle(ss(x1, y, x1 + flis_b, y + flis_h), radius=10 * S, fill=(255, 255, 255, 15),
                        outline=(255, 255, 255, 38), width=S)
    d.rounded_rectangle(ss(x2, y, x2 + flis_b, y + flis_h), radius=10 * S, fill=rgb(L.TURKIS, 51),
                        outline=rgb(L.TURKIS), width=S)
    img = Image.alpha_composite(img, lag)
    d = ImageDraw.Draw(img)
    f = font("Inter-SemiBold.otf", 16)
    for x, tekst in ((x1, str(aar - 1)), (x2, str(aar))):
        d.text(((x + flis_b / 2) * S, (y + flis_h / 2) * S), tekst, font=f, fill=rgb("#E8EEF9"), anchor="mm")
    ikon(d, "arrow_forward", x1 + flis_b + 22, y + flis_h / 2, 20, L.DEMPET)
    d.text(((x1 - 14) * S, (y + flis_h / 2) * S), "Fast periode", font=font("Inter-Medium.otf", 12),
           fill=rgb(L.DEMPET), anchor="rm")
    return img


def bunnlinje(img):
    d = ImageDraw.Draw(img)
    d.line(ss(144, 1022, 1880, 1022), fill=(255, 255, 255, 14), width=S)
    return img


# --------------------------------------------------------------------------- kartet

def kart(img):
    geo = json.loads((ROT / "data" / "kart" / "ostfold_kommuner.geojson").read_text(encoding="utf-8"))
    k = math.cos(math.radians(59.3))
    r = L.KART_RUTE
    (x0, x1), (y0, y1) = L.KART_X, L.KART_Y

    def px(lon, lat):
        return ((r["x"] + (lon * k - x0) / (x1 - x0) * r["w"]) * S,
                (r["y"] + (y1 - lat) / (y1 - y0) * r["h"]) * S)

    lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lag)
    for f in geo["features"]:
        g = f["geometry"]
        ringer = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        moss = f["properties"]["kommunenummer"] == "3103"
        for poly in ringer:
            ytre = [px(*p) for p in poly[0]]
            d.polygon(ytre, fill=rgb(L.TURKIS, 46) if moss else (34, 48, 82, 150))
    for f in geo["features"]:
        g = f["geometry"]
        ringer = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        moss = f["properties"]["kommunenummer"] == "3103"
        for poly in ringer:
            ytre = [px(*p) for p in poly[0]]
            d.line(ytre + [ytre[0]], fill=rgb(L.TURKIS, 200) if moss else (110, 130, 175, 120),
                   width=2 * S if moss else S)
    return Image.alpha_composite(img, lag)


def kartetiketter(img):
    """Kommunenavn ved punktene. Leser koordinatene fra seeds/region.csv."""
    import csv
    k_rad = list(csv.DictReader(open(ROT / "seeds" / "region.csv", encoding="utf-8")))
    r = L.KART_RUTE
    (x0, x1), (y0, y1) = L.KART_X, L.KART_Y
    d = ImageDraw.Draw(img)
    f = font("Inter-Medium.otf", 11.5)
    fm = font("Inter-SemiBold.otf", 13)
    # Forskyvning per kommune så navnet ikke ligger under boblen.
    forskyv = {"3103": (-34, -6, "rm"), "3112": (-26, 16, "rm"), "3107": (-26, 18, "rm"),
               "3110": (0, 32, "mm"), "3101": (0, 34, "mm"), "3105": (30, 0, "lm"),
               "3114": (0, -24, "mm"), "3116": (30, 0, "lm"), "3118": (0, -30, "mm"),
               "3120": (28, 6, "lm"), "3122": (0, -28, "mm"), "3124": (0, 36, "mm")}
    for rad in k_rad:
        if not rad["kart_x"]:
            continue
        x = r["x"] + (float(rad["kart_x"]) - x0) / (x1 - x0) * r["w"]
        y = r["y"] + (y1 - float(rad["kart_y"])) / (y1 - y0) * r["h"]
        dx, dy, anker = forskyv.get(rad["region_id"], (0, -26, "mm"))
        navn = rad["region_navn"].replace(" (Østfold)", "")
        moss = rad["region_id"] == "3103"
        d.text(((x + dx) * S, (y + dy) * S), navn, font=fm if moss else f,
               fill=rgb(L.TURKIS if moss else "#AEB9D1"), anchor=anker)
    return img


# --------------------------------------------------------------------------- metodesiden

def flyt(img, p, antall_tester):
    n = len(L.FLYT)
    boks_b, boks_h = 280, 170
    mellom = (p["w"] - 2 * 40 - n * boks_b) / (n - 1)
    y = p["y"] + (p["h"] - boks_h) / 2
    farger = [L.HIMMEL, L.GULL, L.TURKIS, L.INDIGO, L.ROSA]
    for i, (ik, tittel, l1, l2) in enumerate(L.FLYT):
        x = p["x"] + 40 + i * (boks_b + mellom)
        lag = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lag)
        d.rounded_rectangle(ss(x, y, x + boks_b, y + boks_h), radius=14 * S, fill=rgb(farger[i], 20),
                            outline=rgb(farger[i], 90), width=S)
        img = Image.alpha_composite(img, lag)
        img = ikonring(img, x + boks_b / 2, y + 44, 22, ik, farger[i])
        d = ImageDraw.Draw(img)
        d.text(((x + boks_b / 2) * S, (y + 88) * S), tittel, font=font("Inter-SemiBold.otf", 15),
               fill=rgb(L.TEKST), anchor="mm")
        for j, l in enumerate((l1, l2)):
            d.text(((x + boks_b / 2) * S, (y + 114 + j * 20) * S), l.format(tester=antall_tester),
                   font=font("Inter-Regular.otf", 12), fill=rgb("#AEB9D1"), anchor="mm")
        if i < n - 1:
            ax = x + boks_b + mellom / 2
            ikon(d, "arrow_forward", ax, y + boks_h / 2, 26, "#6B7A99")
    return img


def kontrollstripe(img, p):
    d = ImageDraw.Draw(img)
    del_b = p["w"] / 4
    for i in range(1, 4):
        x = p["x"] + i * del_b
        d.line(ss(x, p["y"] + 24, x, p["y"] + p["h"] - 24), fill=(255, 255, 255, 18), width=S)
    for i, ik in enumerate(["fact_check", "verified", "check_circle", "calendar_month"]):
        img = ikonring(img, p["x"] + i * del_b + 46, p["y"] + p["h"] / 2, 22, ik,
                       [L.TURKIS, L.INDIGO, L.GULL, L.HIMMEL][i])
    return img


# --------------------------------------------------------------------------- sider

def lag_side(side, antall_tester):
    frø = {"oversikt": 3, "f121": 7, "bygg": 11, "metode": 19}[side["id"]]
    img = nordlys(seed=frø)
    img = navigasjon(img, side["id"])
    img = kort(img, side)
    for navn, p in side["paneler"].items():
        if navn == "flyt":
            img = panel(img, **p)
            img = flyt(img, p, antall_tester)
        elif navn == "kontroll":
            img = panel(img, **p)
            img = kontrollstripe(img, p)
        else:
            img = panel(img, **p)
    if side["id"] == "oversikt":
        img = kart(img)
        img = kartetiketter(img)
    if side.get("fast_aar"):
        img = fast_periode(img, side["fast_aar"])
    img = bunnlinje(img)
    return img.resize((L.B, L.H), Image.LANCZOS).convert("RGB")


def main(antall_tester="?"):
    UT.mkdir(parents=True, exist_ok=True)
    for side in L.SIDER:
        sti = UT / f"bg-{side['id']}.png"
        lag_side(side, antall_tester).save(sti, optimize=True)
        print(f"{sti.relative_to(ROT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "?")
