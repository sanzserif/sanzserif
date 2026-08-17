#!/usr/bin/env python3
"""
Generate GitHub profile card SVGs for dark and light themes.
Outputs: profile-dark.svg and profile-light.svg
"""

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
    if not repo_list:
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


def pad_line(label, value, width=LINE_WIDTH):
    """Return label + dots + value, escaped for SVG."""
    dots = width - len(label) - len(str(value))
    dots = max(dots, 1)
    return esc(label + "." * dots + str(value))


def h_sep(title="", width=LINE_WIDTH):
    """Horizontal separator with optional title, escaped for SVG."""
    if title:
        inner = f"─ {title} "
        rem = width - len(inner)
        return esc(inner + "─" * max(rem, 0))
    return esc("─" * width)


# ── RIGHT-PANEL CONTENT ───────────────────────────────────────────────────────
# Each entry: (style, text_already_escaped)
# styles: "header" | "sep" | "text" | "blank"
info = [
    ("header", esc(f"{USERNAME}@github")),
    ("sep",    h_sep(width=LINE_WIDTH)),
    ("blank",  ""),
    ("text",   pad_line("OS: ",                   "Windows")),
    ("text",   pad_line("Uptime: ",               uptime)),
    ("text",   pad_line("Certification: ",        "CS grad, Uni of Westminster")),
    ("text",   pad_line("Certified Batch: ",      "Class of 2026")),
    ("text",   pad_line("Current Host: ",         "LOLC Technologies")),
    ("text",   pad_line("Kernel: ",               "Associate SE")),
    ("text",   pad_line("IDE: ",                  "VS Code, Terminal")),
    ("blank",  ""),
    ("text",   pad_line("Languages.Programming: ", "TypeScript, Java")),
    ("text",   pad_line("Languages.Real: ",        "English, Sinhala")),
    ("text",   pad_line("Hobbies: ",               "Tech Communicator")),
    ("blank",  ""),
    ("sep",    h_sep("Contact", LINE_WIDTH)),
    ("text",   pad_line("Email: ",   "hi@nipun.is-a.dev")),
    ("text",   pad_line("Social: ",  "linktr.ee/sanzserif")),
    ("blank",  ""),
    ("sep",    h_sep("GitHub Stats", LINE_WIDTH)),
    ("text",   pad_line("Repos: ",     str(pub_repos))),
    ("text",   pad_line("Stars: ",     f"{stars:,}")),
    ("text",   pad_line("Commits: ",   f"{commits:,}")),
    ("text",   pad_line("Followers: ", f"{followers:,}")),
    ("text",   pad_line("Wakatime: ",  wakatime)),
]

# ── LAYOUT CONSTANTS ──────────────────────────────────────────────────────────
PAD = 24             # outer padding (px)
GAP = 20             # gap between ASCII panel and info panel

ASCII_FONT   = 7.5
# Courier New character width ≈ font-size × 0.601
ASCII_CHAR_W = ASCII_FONT * 0.601
ASCII_LINE_H = ASCII_FONT * 1.2

INFO_FONT   = 12.5
INFO_CHAR_W = INFO_FONT * 0.601
INFO_LINE_H = 16

ASCII_LINES  = ASCII_ART.split("\n")
ASCII_N      = len(ASCII_LINES)
ASCII_MAX_W  = max(len(l) for l in ASCII_LINES)
ASCII_PX_W   = int(ASCII_MAX_W * ASCII_CHAR_W) + 4
INFO_PX_W    = int(LINE_WIDTH  * INFO_CHAR_W)  + 4

INFO_X  = PAD + ASCII_PX_W + GAP
SVG_W   = INFO_X + INFO_PX_W + PAD

# Height driven by whichever panel is taller
ascii_last_y = PAD + ASCII_FONT + (ASCII_N - 1) * ASCII_LINE_H
info_last_y  = PAD + INFO_FONT  + (len(info) - 1) * INFO_LINE_H
SVG_H = int(max(ascii_last_y, info_last_y)) + PAD + 4

# ── THEMES ───────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":           "#0d1117",
        "ascii":        "#8b949e",
        "header":       "#f0883e",
        "sep":          "#6e7681",
        "text":         "#c9d1d9",
    },
    "light": {
        "bg":           "#ffffff",
        "ascii":        "#57606a",
        "header":       "#cf222e",
        "sep":          "#6e7781",
        "text":         "#24292f",
    },
}

STYLE_COLOR = {
    "header": "header",
    "sep":    "sep",
    "text":   "text",
    "blank":  "text",
}


def generate_svg(theme_name):
    t = THEMES[theme_name]
    out = []

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{SVG_W}" height="{SVG_H}"'
        f' viewBox="0 0 {SVG_W} {SVG_H}"'
        f' role="img" aria-label="GitHub profile card">'
    )

    # Background
    out.append(f'  <rect width="{SVG_W}" height="{SVG_H}" rx="6" fill="{t["bg"]}"/>')

    # ── ASCII art ──────────────────────────────────────────────────────────
    ascii_attrs = (
        f'font-family="\'Courier New\', Courier, monospace"'
        f' font-size="{ASCII_FONT}"'
        f' fill="{t["ascii"]}"'
        f' xml:space="preserve"'
    )
    for i, line in enumerate(ASCII_LINES):
        y = PAD + ASCII_FONT + i * ASCII_LINE_H
        out.append(f'  <text {ascii_attrs} x="{PAD}" y="{y:.2f}">{esc(line)}</text>')

    # ── Info panel ─────────────────────────────────────────────────────────
    info_attrs_base = (
        f'font-family="\'Courier New\', Courier, monospace"'
        f' font-size="{INFO_FONT}"'
        f' xml:space="preserve"'
    )
    for i, (style, text) in enumerate(info):
        if style == "blank":
            continue
        y = PAD + INFO_FONT + i * INFO_LINE_H
        color = t[STYLE_COLOR[style]]
        out.append(
            f'  <text {info_attrs_base} fill="{color}"'
            f' x="{INFO_X}" y="{y:.2f}">{text}</text>'
        )

    out.append("</svg>")
    return "\n".join(out)


# ── WRITE FILES ───────────────────────────────────────────────────────────────
for theme in ("dark", "light"):
    path = f"profile-{theme}.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(generate_svg(theme))
    print(f"  Written {path}")

print("Done.")
