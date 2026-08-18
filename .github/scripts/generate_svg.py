#!/usr/bin/env python3
"""
Generate GitHub profile card SVGs for dark and light themes.
Outputs: profile-dark.svg and profile-light.svg

Left panel: uses ui-dark.png / ui-light.png (base64-embedded) when present,
            falls back to raw SVG text ASCII art.
Right panel: coloured key/dot/value/header/green/red tspan system.
"""

import base64
import re
import json
import urllib.request
import os
import xml.sax.saxutils as saxutils
from datetime import date
from dateutil.relativedelta import relativedelta

# ── ASCII ART ─────────────────────────────────────────────────────────────────
ASCII_ART = """\
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@*.::.::-::-#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@%+:::::--:-:-::::##@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@%:......::-::..:::.:::%@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@:::-:.--:--::.....::::.::-+%@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@%-:.:-::::::.::::..::.::::::::-#-@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@#::::-:::.:::-::..:::::...-:.:::::-%@@@@@@@@@@@@@@@@
@@@@@@@@@@@@-::::-::...:::-=++++++++--:::....::::#@@@@@@@@@@@@@@@
@@@@@@@@@@@%=:::--:....:-+********+++==-:..:...:.:*@@@@@@@@@@@@@@
@@@@@@@@@@@@+-:::-::..::+###********+++=-::..:::..:+@@@@@@@@@@@@@
@@@@@@@@@@@@%-::::...=***#####*******+++=::...:.:::#@@@@@@@@@@@@@
@@@@@@@@@@@@@%--::..===----:-***+=-------+:.:::.::+@@@@@@@@@@@@@@
@@@@@@@@@@@@@=:.:::*%+--::::-=..--:::::=##+:=..:::#@@@@@@@@@@@@@@
@@@@@@@@@@@@@::...-+++---:::-:**::::::::-*+=:..::=*@@@@@@@@@@@@@@
@@@@@@@@@@@@@:.::-***+=---==:*#*+:--:---==++:.::.*@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@:=#=*####*++++*##**+==+=++*+++:-+-*@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@:*=***##*++#*-=*+--++=+***+++--+:@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@*++*#**+++==-----:-=++=+++++-+==@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@%******-+:-#%#%#**--=:-+++++++.:@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@%==*****#**#****+++*++++++--::@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@+-:..-+****##*++++++*+++++=-::-%@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@#:---::==+****#**+++++==-:-:..::+@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@####+:--=++++==--:::-+%*::-#@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@###*=:.::..::.-==#@-::@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@*##***++=+=====@@%:::::-@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@-***#****++#@@@@::::::::..:::-#@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@=@#-*****++@@@@@*::::::::.::::::::-----*@@@@@
@@@@@@@@@@@@@@@@@#--:@@@*+**%@@@@@@-:::::::::::::::::::::-:::--+@
@@@@@@@@@@@@#-:::---.#@@=-=-#@@@@#::::::::.:::::::::::::-:-::::::
@@@@@+--:::::::::--:+%@-==-=--@@--::::::::-:::::::-----:---::::::
%---::::::::::-----+*@=--=---::---::::::::::----------:-----:::::
--::::---::::------*#@*----:::---:::::::::--::------:-:--::::::::"""

# ── CONFIG ────────────────────────────────────────────────────────────────────
BORN = date(2001, 9, 27)
USERNAME = os.environ.get("GITHUB_USERNAME", "sanzserif")
WAKATIME_USER_ID = "018c62f8-0dfd-4403-a80b-cfbb08a36703"
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ── FETCH HELPERS ─────────────────────────────────────────────────────────────
def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  fetch error {url}: {e}")
        return ""


def gh_get(url, extra=None):
    h = {
        "Authorization": "Bearer " + GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        **(extra or {}),
    }
    raw = fetch(url, h)
    try:
        return json.loads(raw)
    except Exception:
        return {}


# ── FETCH STATS ───────────────────────────────────────────────────────────────
today = date.today()
rd = relativedelta(today, BORN)
uptime = f"{rd.years} years, {rd.months} months, {rd.days} days"

user = gh_get(f"https://api.github.com/users/{USERNAME}")
followers = user.get("followers", 0)
pub_repos = user.get("public_repos", 0)

stars = 0
page = 1
while True:
    repo_list = gh_get(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}"
    )
    if not isinstance(repo_list, list) or not repo_list:
        break
    stars += sum(r.get("stargazers_count", 0) for r in repo_list)
    if len(repo_list) < 100:
        break
    page += 1

commits_data = gh_get(
    f"https://api.github.com/search/commits?q=author:{USERNAME}&per_page=1",
    {"Accept": "application/vnd.github.cloak-preview+json"},
)
commits = commits_data.get("total_count", 0)

# Wakatime: parse hours text from public badge SVG
wakatime = "N/A"
waka_svg = fetch(
    f"https://wakatime.com/badge/user/{WAKATIME_USER_ID}.svg?style=flat-square"
)
if waka_svg:
    m = re.search(r"(\d[\d,]* hrs?(?: \d+ mins?)?)", waka_svg)
    if m:
        wakatime = m.group(1)

print(
    f"Stats: uptime={uptime}, repos={pub_repos}, stars={stars}, "
    f"commits={commits}, followers={followers}, wakatime={wakatime}"
)

# ── TEXT HELPERS ──────────────────────────────────────────────────────────────
def esc(s):
    return saxutils.escape(str(s))


LINE_WIDTH = 52  # characters for right-panel dot-padded lines


# ── COLOURED SPAN SYSTEM ──────────────────────────────────────────────────────
# Each info line is a list of (text, token_type) pairs.
# Token types: "h" header/title | "k" key/fuchsia | "d" dots/muted |
#              "v" value/normal | "g" green | "r" red | "s" separator

def kv(label, value, width=LINE_WIDTH):
    """Return a styled [(text, token)] list for a key: ...dots... value line."""
    dots = width - len(label) - len(str(value))
    dots = max(dots, 1)
    return [(label, "k"), ("." * dots, "d"), (str(value), "v")]


def kv2(k1, v1, k2, v2, left_w=28):
    """Two key-value pairs on one line separated by ' | '."""
    left = kv(k1, v1, left_w)
    right = kv(k2, v2, LINE_WIDTH - left_w - 3)
    return left + [(" | ", "d")] + right


def rule(title="", width=LINE_WIDTH):
    """Horizontal separator with optional title."""
    if title:
        inner = f"\u2500 {title} "
        return [(inner, "s"), ("\u2500" * max(width - len(inner), 0), "d")]
    return [("\u2500" * width, "d")]


def header_line(text, width=LINE_WIDTH):
    """Username@github ─────── line."""
    dashes = "\u2500" * max(width - len(text) - 1, 0)
    # Use "s" (blue) for the header name, matching separator colour
    return [(text + " ", "s"), (dashes, "d")]


# ── RIGHT-PANEL CONTENT ───────────────────────────────────────────────────────
# Each entry: list of (text, token) OR [] for a blank line.
info = [
    header_line(f"{USERNAME}@github"),
    [],
    kv("OS: ",                    "Windows"),
    kv("Uptime: ",                uptime),
    kv("Certification: ",         "CS grad, Uni of Westminster"),
    kv("Certified Batch: ",       "Class of 2026"),
    kv("Current Host: ",          "LOLC Technologies"),
    kv("Kernel: ",                "Associate SE"),
    kv("IDE: ",                   "VS Code, Terminal"),
    [],
    kv("Languages.Programming: ", "TypeScript, Java"),
    kv("Languages.Real: ",        "English, Sinhala"),
    kv("Hobbies: ",               "Tech Communicator"),
    [],
    rule("Contact"),
    kv("Email: ",   "hi@nipun.is-a.dev"),
    kv("Social: ",  "linktr.ee/sanzserif"),
    [],
    rule("GitHub Stats"),
    kv2("Repos",    str(pub_repos),    "Stars",     f"{stars:,}"),
    kv2("Commits",  f"{commits:,}",    "Followers", f"{followers:,}"),
    kv("Wakatime: ", wakatime),
]

# ── PNG EMBEDDING ─────────────────────────────────────────────────────────────
def load_png_b64(path):
    """Return base64 data URI for a PNG, or None if file missing."""
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None


# ── LAYOUT CONSTANTS ──────────────────────────────────────────────────────────
PAD = 24             # outer padding (px)
GAP = 20             # gap between left panel and info panel

ASCII_FONT   = 7.5
ASCII_CHAR_W = ASCII_FONT * 0.601
ASCII_LINE_H = ASCII_FONT * 1.2

INFO_FONT   = 12.5
INFO_CHAR_W = INFO_FONT * 0.601
INFO_LINE_H = 16

ASCII_LINES  = ASCII_ART.split("\n")
ASCII_N      = len(ASCII_LINES)
ASCII_MAX_W  = max(len(line) for line in ASCII_LINES)
ASCII_PX_W   = int(ASCII_MAX_W * ASCII_CHAR_W) + 4
INFO_PX_W    = int(LINE_WIDTH  * INFO_CHAR_W)  + 4

INFO_X  = PAD + ASCII_PX_W + GAP
SVG_W   = INFO_X + INFO_PX_W + PAD

ascii_last_y = PAD + ASCII_FONT + (ASCII_N - 1) * ASCII_LINE_H
info_last_y  = PAD + INFO_FONT  + (len(info) - 1) * INFO_LINE_H
SVG_H = int(max(ascii_last_y, info_last_y)) + PAD + 4

# Portrait PNG aspect ratio: the user's images are taller than wide (~2:3).
# We compute the left panel width to fill SVG_H at that ratio so the image
# sits flush top-to-bottom without letterboxing.
PNG_ASPECT_W = 413   # approximate pixel width of the provided portrait PNGs
PNG_ASPECT_H = 540   # approximate pixel height
IMG_H = SVG_H - 2 * PAD          # fill the full inner height
IMG_W = int(IMG_H * PNG_ASPECT_W / PNG_ASPECT_H)  # keep portrait aspect ratio

# Recompute INFO_X using the image width (wider than ASCII fallback text)
IMG_INFO_X = PAD + IMG_W + GAP

# ── THEMES ───────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":    "#0d1117",
        "ascii": "#8b949e",
        "h":     "#f0883e",   # (unused for header now, kept for future use)
        "k":     "#ff79c6",   # key (fuchsia)
        "d":     "#484f58",   # dots / muted
        "v":     "#c9d1d9",   # value / normal text
        "s":     "#58a6ff",   # separator title + header username (blue)
        "g":     "#3fb950",   # green (additions)
        "r":     "#f85149",   # red (deletions)
    },
    "light": {
        "bg":    "#ffffff",
        "ascii": "#57606a",
        "h":     "#953800",   # (unused for header now)
        "k":     "#b4009e",   # key (fuchsia)
        "d":     "#afb8c1",   # dots / muted
        "v":     "#24292f",   # value / normal text
        "s":     "#0969da",   # separator title + header username (blue)
        "g":     "#1a7f37",   # green
        "r":     "#cf222e",   # red
    },
}

# Doto font: weight 700, roundness axis (ROND) = 100
# Loaded via Google Fonts @import so GitHub Markdown/SVG renderers can fetch it.
DOTO_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Doto:ROND,wght@100,700&display=swap');"
)
DOTO_CLASS = (
    "font-family: 'Doto', 'Courier New', monospace;"
    " font-weight: 700;"
    " font-variation-settings: 'ROND' 100;"
)


def spans_svg(tokens, theme, x, y, font_size):
    """Render a list of (text, token_type) as a <text> with <tspan> children."""
    base = (
        f'<text class="info" font-size="{font_size}"'
        f' xml:space="preserve" x="{x}" y="{y:.2f}">'
    )
    parts = []
    for text, tok in tokens:
        col = theme.get(tok, theme["v"])
        parts.append(f'<tspan fill="{col}">{esc(text)}</tspan>')
    return "  " + base + "".join(parts) + "</text>"


def generate_svg(theme_name):
    t = THEMES[theme_name]
    out = []
    mono = "'Courier New', Courier, monospace"

    # ── Check for user-provided portrait PNG ───────────────────────────────
    png_path = os.path.join(os.path.dirname(__file__), "..", "..", f"ui-{theme_name}.png")
    png_uri = load_png_b64(png_path)

    # When PNG is present, widen SVG to use the portrait-aspect left panel
    left_w = IMG_W if png_uri else ASCII_PX_W
    info_x = PAD + left_w + GAP
    svg_w  = info_x + INFO_PX_W + PAD

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{svg_w}" height="{SVG_H}"'
        f' viewBox="0 0 {svg_w} {SVG_H}"'
        f' role="img" aria-label="GitHub profile card">'
    )

    # ── Embedded style: Doto font ───────────────────────────────────────────
    out.append(f'  <defs>')
    out.append(f'    <style>')
    out.append(f'      {DOTO_IMPORT}')
    out.append(f'      .info {{ {DOTO_CLASS} }}')
    out.append(f'    </style>')
    if png_uri:
        # Clip the portrait image to the left-panel rectangle
        out.append(
            f'    <clipPath id="left-clip">'
            f'<rect x="{PAD}" y="{PAD}" width="{IMG_W}" height="{IMG_H}"/></clipPath>'
        )
    out.append(f'  </defs>')

    # Background
    out.append(f'  <rect width="{svg_w}" height="{SVG_H}" rx="6" fill="{t["bg"]}"/>')

    # ── Left panel ─────────────────────────────────────────────────────────
    if png_uri:
        out.append(
            f'  <image href="{png_uri}"'
            f' x="{PAD}" y="{PAD}"'
            f' width="{IMG_W}" height="{IMG_H}"'
            f' preserveAspectRatio="xMidYMid slice"'
            f' clip-path="url(#left-clip)"/>'
        )
    else:
        ascii_attrs = (
            f'font-family="{mono}"'
            f' font-size="{ASCII_FONT}"'
            f' fill="{t["ascii"]}"'
            f' xml:space="preserve"'
        )
        for i, line in enumerate(ASCII_LINES):
            y = PAD + ASCII_FONT + i * ASCII_LINE_H
            out.append(f'  <text {ascii_attrs} x="{PAD}" y="{y:.2f}">{esc(line)}</text>')

    # ── Info panel ─────────────────────────────────────────────────────────
    for i, tokens in enumerate(info):
        if not tokens:
            continue
        y = PAD + INFO_FONT + i * INFO_LINE_H
        out.append(spans_svg(tokens, t, info_x, y, INFO_FONT))

    out.append("</svg>")
    return "\n".join(out)


# ── WRITE FILES ───────────────────────────────────────────────────────────────
for theme in ("dark", "light"):
    path = f"profile-{theme}.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(generate_svg(theme))
    print(f"  Written {path}")

print("Done.")
