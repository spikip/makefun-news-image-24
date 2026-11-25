#!/usr/bin/env python3
"""Render the 'World in One Day' dense news digest for Tuesday 24 November 2026.

Build-time renderer (needs Pillow and the Liberation fonts). The shipped entry
program is main.py, which copies the rendered entry.png into place; this script
is kept in the repo so the page can be re-rendered and audited. Every story on
the page was checked against live reporting of Tuesday 24 November 2026 (see
README.md for the sources). Nothing on the page is invented: dates, figures and
scores all come from the reporting cited in the README.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 26                      # side margin
CW = W - 2 * M              # content width
PAPER = (247, 242, 231)
PANEL = (238, 231, 214)
INK = (26, 23, 18)
RED = (163, 22, 33)
NAVY = (29, 53, 87)
GREY = (96, 88, 74)
RULE = (178, 164, 138)
LAND = (146, 130, 94)
SEA = (233, 226, 205)
GREEN = (46, 110, 58)

FD = "/usr/share/fonts/truetype/liberation"
F_SERIF = f"{FD}/LiberationSerif-Regular.ttf"
F_SERIF_B = f"{FD}/LiberationSerif-Bold.ttf"
F_SERIF_I = f"{FD}/LiberationSerif-Italic.ttf"
F_SANS = f"{FD}/LiberationSans-Regular.ttf"
F_SANS_B = f"{FD}/LiberationSans-Bold.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, s, f, maxw):
    """Greedy word wrap; returns a list of lines."""
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, s, f, maxw, leading, fill=INK, align="left"):
    """Draw wrapped text; return y just past the last line."""
    for ln in wrap(d, s, f, maxw):
        if align == "center":
            d.text((x + (maxw - tw(d, ln, f)) / 2, y), ln, font=f, fill=fill)
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def centre(d, x, y, w_, s, f, fill=INK):
    d.text((x + (w_ - tw(d, s, f)) / 2, y), s, font=f, fill=fill)


def chip(d, x, y, text, fill, fg=(255, 255, 255), fsize=9):
    f = font(F_SANS_B, fsize)
    w_ = tw(d, text, f) + 10
    d.rectangle([x, y, x + w_, y + fsize + 6], fill=fill)
    d.text((x + 5, y + 3), text, font=f, fill=fg)
    return w_


def num_disc(d, x, y, n, r=9):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=RED)
    f = font(F_SANS_B, 11)
    s = str(n)
    d.text((x + r - tw(d, s, f) / 2, y + r - 6), s, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------------------
# The day's stories — all verified against live reporting of Tue 24 Nov 2026.
# Each story carries a region and a field; the top bar counts are computed
# from these, so they always match what is actually on the page.
# ---------------------------------------------------------------------------
LEADS = [
    {
        "num": 1, "tag": "PARIS · ECONOMY", "region": "Europe",
        "field": "Economy", "status": "CONFIRMED",
        "headline": "Sanofi buys Insmed for $41bn in cash",
        "summary": "France's Sanofi agreed to pay $175 a share for US biotech "
                   "Insmed — the year's biggest pharma deal — to build a "
                   "respiratory franchise as patents loom.",
        "art": "sanofi",
    },
    {
        "num": 2, "tag": "KERCH STRAIT · WAR", "region": "Europe",
        "field": "War", "status": "REPORTED",
        "headline": "Ukraine hits the Kerch Bridge again",
        "summary": "Kyiv struck the bridge to occupied Crimea again in a wave "
                   "of drone and missile attacks; Russia hit back at Kyiv's "
                   "river crossings and energy grid.",
        "art": "bridge",
    },
    {
        "num": 3, "tag": "NEW YORK · MARKETS", "region": "North America",
        "field": "Markets", "status": "CONFIRMED",
        "headline": "Dow tops 50,000 as chips give back",
        "summary": "The Dow closed above 50,000 for the first time, up 0.85%, "
                   "while the Nasdaq fell 1.48% as chip stocks handed back "
                   "part of Monday's Nvidia-driven surge.",
        "art": "market",
    },
]

MAINS = [
    (4, "ABU DHABI · DIPLOMACY", "Middle East", "Diplomacy", "OFFICIAL",
     "Moscow rules out land concessions",
     "After US-mediated talks in Abu Dhabi, Russia's negotiator Medinsky "
     "rejected any territorial concessions."),
    (5, "ZAPORIZHZHIA · WAR", "Europe", "War", "OFFICIAL",
     "Flats hit overnight: 2 dead, 40 hurt",
     "A Russian strike wrecked a five-storey block; four of the wounded "
     "are children, officials said."),
    (6, "BERLIN · SECURITY", "Europe", "Security", "REPORTED",
     "NATO vows to defend space",
     "Chief Mark Rutte said the alliance will defend against any threat "
     "in space after reports of a Russian nuclear satellite."),
    (7, "RIYADH · CONFLICT", "Middle East", "Conflict", "OFFICIAL",
     "Houthi strike on Riyadh tower: 11 hurt",
     "Saudi civil defence said a Houthi attack hit a tower in the King "
     "Abdullah Financial District."),
    (8, "GAZA · WAR", "Middle East", "War", "OFFICIAL",
     "Israeli strikes kill six in Gaza",
     "Medics said two police officers were among the dead; three died "
     "at a police post in Khan Younis."),
    (9, "JERUSALEM · POLITICS", "Middle East", "Politics", "CONFIRMED",
     "Eisenkot signs first coalition pact",
     "Ex-military chief Gadi Eisenkot agreed a deal with Avigdor "
     "Lieberman's party in his bid to form a government."),
    (10, "CARTAGENA · CRIME", "South America", "Crime", "OFFICIAL",
     "Gunmen hold 25 hostage in supermarket",
     "Armed men fled into an Exito store after a failed armoured-truck "
     "robbery; five elderly women were freed."),
    (11, "BANTEN, INDONESIA · DISASTER", "Asia", "Disaster", "OFFICIAL",
     "Cikande fire toll rises to 26",
     "Rescuers recovered more remains from the wrecked candy factory; "
     "eight workers are still missing."),
    (12, "GLOBAL · SOCIETY", "Global", "Society", "OFFICIAL",
     "47,000 women killed by partners in 2025",
     "A UN report finds five women an hour were killed by a partner or "
     "relative last year — 60% of all femicides."),
    (13, "MADRID · SPORT", "Europe", "Sport", "CONFIRMED",
     "Real Madrid hit five past PSV",
     "Madrid came from behind to win 5–1; Arsenal drew 1–1 with "
     "Dortmund and City drew 2–2 with Napoli."),
]

ALSO = [
    ("BERLIN", "Germany first to get access to Ukraine's Delta battle system", "Europe", "Diplomacy"),
    ("BAGHDAD", "Iraq PM orders ministry to run oilfields in Kurdish-held areas", "Middle East", "Diplomacy"),
    ("OSLO", "Norway pledges at least $7bn for Ukraine in 2027", "Europe", "Diplomacy"),
    ("SEOUL", "Russian jets enter South Korea's air defence zone", "Asia", "Security"),
    ("CHISINAU", "Seven Russian drones cross Moldova's airspace", "Europe", "War"),
    ("ST PETERSBURG", "Ukrainian drones hit the Kirishi oil refinery", "Europe", "War"),
    ("KYIV", "Zelensky: Ukraine needs €115bn in outside help in 2027", "Europe", "Diplomacy"),
    ("KYIV", "Russian attacks kill nine across Ukraine", "Europe", "War"),
    ("KYIV", "Ukraine puts Russian 2026 casualties at 432,519, a record year", "Europe", "War"),
    ("WASHINGTON", "FBI probes suspected breach of police crime database", "North America", "Tech"),
    ("WASHINGTON", "NYT: CIA and ODNI found a breach of an unclassified network", "North America", "Tech"),
    ("LONDON", "UK sanctions five Myanmar generals after ICJ genocide ruling", "Europe", "Justice"),
    ("TRIPOLI", "UN mission urges probe into Benghazi port attacks", "Africa", "War"),
    ("LONDON", "UK designates Houthis under Yemen sanctions", "Europe", "Security"),
    ("LONDON", "UK warns firms aiding Ukraine to brace for Russian sabotage", "Europe", "Security"),
    ("TEHRAN", "Rial slides after fresh US sanctions", "Middle East", "Economy"),
    ("WASHINGTON", "Hegseth yet to sign off 60 Patriot interceptors for Kyiv (FT)", "North America", "Diplomacy"),
    ("BRUSSELS", "EU to seek overhaul of UN climate consensus rules after COP31", "Europe", "Climate"),
    ("CARRARA", "England beat Australia by 8 wickets in 2nd T20I; series 1–1", "Europe", "Sport"),
    ("DOHA", "Sooryavanshi's 204 off 53 powers India A past UAE", "Asia", "Sport"),
    ("BEIJING", "China starts 6G pilot tests in eight regions", "Asia", "Tech"),
    ("CANBERRA", "Australia sets 46 AI rules; victims may sue platforms", "Oceania", "Tech"),
]

TIMELINE = [
    ("c.01:00", "KYIV", "Overnight strike hits Zaporizhzhia flats"),
    ("06:30", "PARIS", "Sanofi announces $41bn Insmed deal"),
    ("c.09:00", "VIENNA", "UN: 47,000 women killed by partners"),
    ("c.14:00", "ABU DHABI", "Medinsky rules out concessions"),
    ("c.17:00", "CARTAGENA", "Gunmen seize supermarket; 25 held"),
    ("21:00", "NEW YORK", "Dow closes above 50,000"),
]

STATS = [
    ("$41bn", "SANOFI'S INSMED DEAL"),
    ("50,018.70", "DOW'S FIRST CLOSE ABOVE 50,000"),
    ("47,000", "WOMEN KILLED BY PARTNERS IN 2025"),
    ("432,519", "RUSSIAN CASUALTIES IN 2026, PER KYIV"),
    ("26", "DEAD IN THE CIKANDE FACTORY FIRE"),
    ("25", "HOSTAGES HELD IN CARTAGENA"),
]

DATE_CHECK = (
    "Left out as not Tuesday's news: the COP31 collapse and the sinking of the Russian corvette "
    "Merkury off Benghazi (both Sunday 22 Nov); Nvidia's Huang reinstated and shares +31% (Monday "
    "23 Nov); the ICJ's Myanmar genocide ruling (Thu 19 Nov); the US losing measles-free status "
    "(17 Nov); the FDA's first limb-girdle drug approval, the Grok lawsuits and the Gaza '77 years' "
    "warning (all Monday 23 Nov); the Guterres AI-safety call (Bridgetown, Monday). The Cikande "
    "fire began Sat 21 Nov — Tuesday brought the toll update, story 11."
)

N_STORIES = len(LEADS) + len(MAINS) + len(ALSO)
REGIONS = sorted({s["region"] for s in LEADS}
                 | {m[2] for m in MAINS} | {a[2] for a in ALSO})
FIELDS = sorted({s["field"] for s in LEADS}
                | {m[3] for m in MAINS} | {a[3] for a in ALSO})


# ---------------------------------------------------------------------------
# Lead illustrations (simple drawn graphics).
# ---------------------------------------------------------------------------
def art_sanofi(d, x, y, w_, h_):
    d.rectangle([x, y, x + w_, y + h_], fill=PANEL, outline=RULE)
    f_t = font(F_SANS_B, 10)
    d.text((x + 8, y + 5), "INSMED SHARE PRICE, $", font=f_t, fill=GREY)
    vals = [("BEFORE", 119.90, NAVY), ("MON CLOSE", 149.09, NAVY),
            ("OFFER", 175.00, RED)]
    base = y + h_ - 20
    top = y + 24
    bw = 62
    gap = (w_ - 3 * bw - 16) / 2
    f_v = font(F_SANS_B, 11)
    f_l = font(F_SANS_B, 9)
    for i, (lab, v, col) in enumerate(vals):
        bh = (v / 175.0) * (base - top)
        bx = x + 8 + i * (bw + gap)
        d.rectangle([bx, base - bh, bx + bw, base], fill=col)
        centre(d, bx, base - bh - 14, bw, f"${v:,.0f}", f_v, INK)
        centre(d, bx, base + 4, bw, lab, f_l, GREY)
    d.line([x + 8, base, x + w_ - 8, base], fill=INK, width=1)


def art_bridge(d, x, y, w_, h_):
    d.rectangle([x, y, x + w_, y + h_], fill=SEA, outline=RULE)
    f_t = font(F_SANS_B, 10)
    d.text((x + 8, y + 5), "KERCH STRAIT", font=f_t, fill=GREY)
    for i in range(9):
        wx = x + 8 + i * 34
        d.arc([wx, y + h_ - 26, wx + 22, y + h_ - 12], 0, 180, fill=NAVY)
    deck_y = y + 52
    d.line([x + 10, deck_y, x + w_ / 2 - 26, deck_y], fill=INK, width=5)
    d.line([x + w_ / 2 + 26, deck_y, x + w_ - 10, deck_y], fill=INK, width=5)
    for tx in (x + 70, x + w_ - 70):
        d.line([tx, deck_y, tx, y + 22], fill=INK, width=3)
    d.line([x + 70, y + 22, x + w_ / 2 - 26, deck_y], fill=INK, width=1)
    d.line([x + w_ - 70, y + 22, x + w_ / 2 + 26, deck_y], fill=INK, width=1)
    cx, cy = x + w_ / 2, deck_y - 6
    for ang in range(0, 360, 30):
        dx = math.cos(math.radians(ang)) * 16
        dy = math.sin(math.radians(ang)) * 16
        d.line([cx, cy, cx + dx, cy + dy], fill=RED, width=3)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=RED)
    dx0, dy0 = x + w_ - 46, y + 16
    d.ellipse([dx0, dy0, dx0 + 14, dy0 + 5], fill=INK)
    d.line([dx0 + 2, dy0 - 3, dx0 + 12, dy0 - 3], fill=INK, width=2)


def art_market(d, x, y, w_, h_):
    d.rectangle([x, y, x + w_, y + h_], fill=PANEL, outline=RULE)
    f_t = font(F_SANS_B, 10)
    d.text((x + 8, y + 5), "WALL ST, TUESDAY", font=f_t, fill=GREY)
    ox, oy = x + 10, y + 22
    pw, ph = w_ - 20, h_ - 44
    ly = oy + ph * 0.42
    for sx in range(ox, ox + pw, 8):
        d.line([sx, ly, sx + 5, ly], fill=GREY, width=1)
    f_l = font(F_SANS_B, 9)
    d.text((ox + pw - 52, ly - 13), "50,000", font=f_l, fill=GREY)
    pts_dow = [(ox, oy + ph * 0.72), (ox + pw * 0.45, oy + ph * 0.55),
               (ox + pw * 0.8, oy + ph * 0.30), (ox + pw, oy + ph * 0.22)]
    d.line(pts_dow, fill=GREEN, width=3, joint="curve")
    pts_nas = [(ox, oy + ph * 0.30), (ox + pw * 0.45, oy + ph * 0.48),
               (ox + pw * 0.8, oy + ph * 0.66), (ox + pw, oy + ph * 0.78)]
    d.line(pts_nas, fill=RED, width=3, joint="curve")
    f_v = font(F_SANS_B, 11)
    d.text((ox + 2, oy + ph - 14), "DOW +0.85%", font=f_v, fill=GREEN)
    d.text((ox + pw - 108, oy + ph - 14), "NASDAQ −1.48%", font=f_v, fill=RED)


ART = {"sanofi": art_sanofi, "bridge": art_bridge, "market": art_market}


# ---------------------------------------------------------------------------
# World map: coarse continent polygons, rasterised to dots.
# ---------------------------------------------------------------------------
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-75, 62), (-65, 60), (-55, 52), (-60, 47), (-65, 44), (-70, 42),
     (-75, 38), (-80, 32), (-81, 26), (-85, 30), (-90, 21), (-86, 12),
     (-80, 8), (-77, 7), (-80, 9), (-83, 9), (-90, 14), (-95, 16),
     (-97, 16), (-105, 20), (-110, 23), (-114, 29), (-120, 34), (-124, 42),
     (-125, 49), (-130, 54), (-135, 58), (-145, 60), (-155, 58), (-162, 55),
     (-168, 60)],
    # South America
    [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52), (-66, -55),
     (-65, -45), (-62, -40), (-58, -34), (-52, -32), (-48, -28), (-41, -23),
     (-38, -15), (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0),
     (-55, 4), (-60, 8), (-65, 10), (-70, 11), (-75, 10), (-80, 9)],
    # Africa
    [(-6, 35), (-10, 31), (-17, 15), (-17, 12), (-13, 8), (-8, 5), (-4, 5),
     (0, 6), (6, 4), (9, 4), (9, -1), (12, -6), (13, -12), (12, -18),
     (15, -27), (18, -34), (20, -35), (26, -34), (32, -28), (35, -24),
     (36, -18), (40, -15), (40, -10), (42, -4), (46, -1), (51, 2),
     (51, 11), (44, 11), (40, 15), (38, 18), (37, 22), (35, 28), (32, 31),
     (30, 31), (22, 33), (19, 32), (15, 32), (10, 37), (10, 34), (5, 37),
     (0, 36), (-6, 35)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 49), (2, 51),
     (5, 53), (8, 57), (10, 59), (5, 60), (5, 62), (10, 64), (12, 66),
     (18, 69), (25, 71), (30, 70), (35, 68), (40, 68), (45, 68), (50, 69),
     (55, 68), (60, 69), (65, 69), (70, 72), (75, 72), (80, 73), (85, 74),
     (90, 75), (95, 76), (100, 77), (105, 77), (110, 74), (115, 73),
     (120, 73), (125, 72), (130, 72), (135, 71), (140, 72), (145, 72),
     (150, 70), (155, 69), (160, 69), (165, 66), (170, 66), (178, 65),
     (178, 62), (170, 60), (162, 60), (158, 56), (156, 51), (150, 59),
     (142, 59), (140, 54), (135, 45), (130, 42), (127, 40), (126, 38),
     (122, 38), (120, 35), (122, 31), (120, 28), (118, 25), (112, 22),
     (108, 18), (105, 10), (103, 8), (100, 8), (98, 10), (95, 16),
     (92, 20), (90, 22), (88, 22), (85, 20), (80, 16), (80, 13), (77, 8),
     (75, 12), (72, 20), (70, 22), (66, 25), (62, 25), (58, 25), (56, 26),
     (52, 26), (50, 29), (48, 30), (44, 29), (42, 27), (40, 22), (38, 20),
     (35, 29), (34, 31), (36, 36), (33, 36), (30, 36), (27, 37), (26, 38),
     (23, 36), (22, 37), (19, 40), (15, 40), (12, 44), (10, 44), (8, 44),
     (3, 42), (0, 39), (-2, 37), (-6, 36), (-9, 37)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-3, 50)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 38), (141, 41), (143, 43),
     (145, 44), (142, 44), (140, 40), (139, 37), (136, 34), (132, 33),
     (130, 31)],
    # Australia
    [(114, -22), (114, -30), (115, -35), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -22)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (178, -38), (176, -40),
     (174, -42), (171, -44), (168, -46), (167, -45)],
    # Indonesia
    [(95, 5), (98, 3), (100, 0), (102, -3), (105, -5), (108, -7), (110, -7),
     (114, -8), (118, -9), (120, -10), (122, -9), (125, -9), (128, -8),
     (130, -3), (132, -2), (135, -2), (138, -2), (140, -3), (141, -8),
     (138, -8), (135, -8), (132, -7), (128, -7), (125, -8), (122, -8),
     (120, -7), (117, -8), (114, -8), (111, -7), (108, -6), (105, -5),
     (102, -3), (100, 0), (97, 3), (95, 5)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (44, -25),
     (43, -22), (44, -16)],
]

# (number, lon, lat, dx, dy) — dx/dy nudge crowded pins; a leader line is drawn.
PINS = [
    (1, 2.35, 48.85, -16, -10),
    (2, 36.5, 45.3, 20, 16),
    (3, -74.0, 40.7, 0, 0),
    (4, 54.4, 24.45, 16, -6),
    (5, 35.2, 47.85, -18, -14),
    (6, 13.4, 52.5, 20, -18),
    (7, 46.7, 24.7, -14, 12),
    (8, 34.45, 31.5, 0, 0),
    (9, 35.2, 31.8, -18, 14),
    (10, -75.5, 10.4, 0, 0),
    (11, 106.1, -6.1, 0, 0),
    (12, 16.4, 48.2, -18, 14),
    (13, -3.7, 40.4, -12, 12),
]


def _inside(lon, lat, poly):
    """Ray-casting point-in-polygon test."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < xin:
                inside = not inside
    return inside


def draw_map(d, x, y, w_, h_):
    d.rectangle([x, y, x + w_, y + h_], fill=SEA, outline=RULE)
    cols, rows = 104, 48
    lat_top, lat_bot = 84.0, -58.0
    cw, ch = w_ / cols, h_ / rows
    for ri in range(rows):
        lat = lat_top + (ri + 0.5) * (lat_bot - lat_top) / rows
        for ci in range(cols):
            lon = -180.0 + (ci + 0.5) * 360.0 / cols
            if any(_inside(lon, lat, p) for p in CONTINENTS):
                cx = x + (ci + 0.5) * cw
                cy = y + (ri + 0.5) * ch
                d.ellipse([cx - 1.2, cy - 1.7, cx + 1.2, cy + 1.7], fill=LAND)
    f = font(F_SANS_B, 9)
    for num, lon, lat, dx, dy in PINS:
        px = x + (lon + 180.0) / 360.0 * w_
        py = y + (lat_top - lat) / (lat_top - lat_bot) * h_
        qx, qy = px + dx, py + dy
        if dx or dy:
            d.line([px, py, qx, qy], fill=RED, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
        d.ellipse([qx - 7, qy - 7, qx + 7, qy + 7], fill=RED,
                  outline=(255, 255, 255), width=1)
        s = str(num)
        d.text((qx - tw(d, s, f) / 2, qy - 5), s, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = 12

    # --- top bar (counts computed from the story data) ----------------------
    bar = (f"THE WORLD IN ONE DAY — {N_STORIES} STORIES • {len(REGIONS)} "
           f"REGIONS • {len(FIELDS)} FIELDS • EVERY ONE FROM "
           f"TUESDAY 24 NOVEMBER 2026")
    d.rectangle([M, y, M + CW, y + 26], fill=INK)
    centre(d, M, y + 6, CW, bar, font(F_SANS_B, 13), (255, 255, 255))
    y += 34

    # --- masthead ------------------------------------------------------------
    centre(d, M, y, CW, "Tuesday 24 November 2026",
           font(F_SERIF_B, 50), INK)
    y += 58
    sub = ("SANOFI BUYS INSMED FOR $41BN   ·   UKRAINE HITS THE KERCH BRIDGE "
           "AGAIN   ·   DOW TOPS 50,000")
    centre(d, M, y, CW, sub, font(F_SANS_B, 14), RED)
    y += 22
    d.line([M, y, M + CW, y], fill=INK, width=2)
    d.line([M, y + 3, M + CW, y + 3], fill=INK, width=1)
    y += 10

    # --- the day in UTC ------------------------------------------------------
    d.text((M, y), "THE DAY IN UTC", font=font(F_SANS_B, 12), fill=RED)
    y += 17
    col_w = CW // 3
    f_t = font(F_SANS_B, 11)
    f_b = font(F_SERIF, 11)
    for i, (t, place, ev) in enumerate(TIMELINE):
        cx = M + (i % 3) * col_w
        cy = y + (i // 3) * 16
        d.text((cx, cy), t, font=f_t, fill=RED)
        d.text((cx + 52, cy), place + " —", font=f_t, fill=INK)
        d.text((cx + 52 + tw(d, place + " — ", f_t) + 2, cy), ev,
               font=f_b, fill=INK)
    y += 34
    d.line([M, y, M + CW, y], fill=RULE, width=1)
    y += 8

    # --- statistics strip ----------------------------------------------------
    sw = CW // 6
    for i, (num, lab) in enumerate(STATS):
        cx = M + i * sw
        if i:
            d.line([cx, y, cx, y + 44], fill=RULE, width=1)
        centre(d, cx + 4, y, sw - 8, num, font(F_SERIF_B, 21), RED)
        block(d, cx + 8, y + 26, lab, font(F_SANS_B, 8), sw - 16, 10,
              fill=GREY, align="center")
    y += 46
    d.line([M, y, M + CW, y], fill=INK, width=2)
    y += 10

    # --- three leads ---------------------------------------------------------
    lw = (CW - 2 * 18) // 3
    lead_top = y
    for i, s in enumerate(LEADS):
        lx = M + i * (lw + 18)
        ART[s["art"]](d, lx, y, lw, 90)
        ty = y + 98
        num_disc(d, lx, ty, s["num"])
        d.text((lx + 22, ty + 2), s["tag"], font=font(F_SANS_B, 10), fill=INK)
        chip(d, lx + lw - 78, ty, s["status"], NAVY)
        hy = ty + 20
        hy = block(d, lx, hy, s["headline"], font(F_SERIF_B, 17), lw, 20)
        block(d, lx, hy + 2, s["summary"], font(F_SERIF, 12.5), lw, 16)
    y = lead_top + 96 + 8 + 20 + 62 + 6
    d.line([M, y, M + CW, y], fill=INK, width=2)
    y += 8

    # --- numbered stories 4–13 (two columns) + map --------------------------
    grid_left = M
    grid_w = 622
    col2_w = (grid_w - 18) // 2
    map_x = M + grid_w + 16
    map_w = W - M - map_x
    mains_top = y
    for idx, (num, tag, region, field, status, head, summ) in enumerate(MAINS):
        col = idx % 2
        row = idx // 2
        sx = grid_left + col * (col2_w + 18)
        sy = mains_top + row * 58
        num_disc(d, sx, sy, num, r=8)
        d.text((sx + 20, sy + 1), tag, font=font(F_SANS_B, 9.5), fill=INK)
        tw_tag = tw(d, tag, font(F_SANS_B, 9.5))
        chip(d, sx + 20 + tw_tag + 6, sy, status, RED, fsize=8)
        block(d, sx, sy + 14, head, font(F_SERIF_B, 13.5), col2_w, 16)
        block(d, sx, sy + 30, summ, font(F_SERIF, 11), col2_w, 13)
    # map
    d.text((map_x, mains_top), "WHERE IT HAPPENED",
           font=font(F_SANS_B, 12), fill=NAVY)
    draw_map(d, map_x, mains_top + 18, map_w, 208)
    block(d, map_x, mains_top + 232,
          "Pins 1–13 mark the numbered stories; 12 is worldwide, pinned at Vienna.",
          font(F_SERIF_I, 10.5), map_w, 13, fill=GREY)
    y = mains_top + 5 * 58 + 4
    d.line([M, y, M + CW, y], fill=INK, width=2)
    y += 8

    # --- also on Tuesday -----------------------------------------------------
    d.text((M, y), "ALSO ON TUESDAY 24 NOVEMBER",
           font=font(F_SANS_B, 12), fill=NAVY)
    y += 17
    also_col_w = (CW - 24) // 2
    f_a = font(F_SANS, 11)
    f_ab = font(F_SANS_B, 11)
    for i, (place, item, region, field) in enumerate(ALSO):
        col = 0 if i < 11 else 1
        row = i if i < 11 else i - 11
        ax = M + col * (also_col_w + 24)
        ay = y + row * 14
        d.text((ax, ay), place + " — ", font=f_ab, fill=INK)
        d.text((ax + tw(d, place + " — ", f_ab), ay), item, font=f_a,
               fill=INK)
    y += 11 * 14 + 6
    d.line([M, y, M + CW, y], fill=INK, width=1)
    y += 7

    # --- date check ----------------------------------------------------------
    d.rectangle([M, y, M + CW, y + 60], outline=RED, width=1)
    d.text((M + 8, y + 5), "DATE CHECK", font=font(F_SANS_B, 11), fill=RED)
    block(d, M + 8, y + 20, DATE_CHECK, font(F_SERIF, 10.5), CW - 16, 13)
    y += 68

    # --- footer --------------------------------------------------------------
    centre(d, M, y, CW,
           "Compiled from Tuesday's reporting — every story above happened, or "
           "was first reported, on Tuesday 24 November 2026.",
           font(F_SERIF_I, 11), GREY)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out} {W}x{H} {os.path.getsize(out)} bytes "
          f"({N_STORIES} stories, {len(REGIONS)} regions, {len(FIELDS)} fields)")


if __name__ == "__main__":
    render()
