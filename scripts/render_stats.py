"""Renders assets/stats.png from live GitHub data.

Run by .github/workflows/stats.yml once a day. Everything is drawn as pixels
with the toolkit in pixel.py, so the panel matches the rest of the profile and
does not depend on any third-party image service.

Falls back to scripts/stats_cache.json when the network or API is unavailable,
so the panel never renders blank.
"""
import json
import os
import re
import sys

from pixel import (C, upscale, text_width,
                   VOID, PANEL, LINE, GOLD, GOLD_D, CREAM, DIM, RED, CYAN, TRACE)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CACHE = os.path.join(HERE, "stats_cache.json")
USER = os.environ.get("GH_USER", "AhmadTChaudhry")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

LANG_COLOURS = [GOLD, CYAN, CREAM, RED, TRACE]


# ---------------------------------------------------------------- data
def fetch():
    import requests

    s = requests.Session()
    s.headers["Accept"] = "application/vnd.github+json"
    if TOKEN:
        s.headers["Authorization"] = f"Bearer {TOKEN}"

    user = s.get(f"https://api.github.com/users/{USER}", timeout=20)
    user.raise_for_status()
    user = user.json()

    repos, page = [], 1
    while True:
        r = s.get(f"https://api.github.com/users/{USER}/repos",
                  params={"per_page": 100, "page": page, "type": "owner"}, timeout=20)
        r.raise_for_status()
        batch = r.json()
        repos += batch
        if len(batch) < 100:
            break
        page += 1

    own = [r for r in repos if not r.get("fork")]
    langs = {}
    for r in own:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1

    # Contribution total is only exposed on the public profile page.
    contrib = 0
    try:
        html = s.get(f"https://github.com/{USER}", timeout=20).text
        m = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html, re.I)
        if m:
            contrib = int(m.group(1).replace(",", ""))
    except Exception:
        pass

    return {
        "user": USER,
        "contrib": contrib,
        "repos": len(own),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "forks": sum(r.get("forks_count", 0) for r in own),
        "followers": user.get("followers", 0),
        "languages": sorted(langs.items(), key=lambda kv: -kv[1])[:5],
    }


def load():
    try:
        data = fetch()
        with open(CACHE, "w") as fh:
            json.dump(data, fh, indent=2)
        return data, "live"
    except Exception as exc:                                  # noqa: BLE001
        print(f"live fetch failed ({exc}); using cache", file=sys.stderr)
        with open(CACHE) as fh:
            return json.load(fh), "cache"


# ---------------------------------------------------------------- render
def render(d):
    W, H = 320, 134
    c = C(W, H, VOID)
    c.frame(2, 2, W - 4, H - 4, LINE)
    c.frame(4, 4, W - 8, H - 8, CREAM)
    c.rect(6, 6, W - 12, H - 12, PANEL)

    c.rect(6, 6, W - 12, 12, LINE)
    c.text(12, 8, "STATUS", GOLD, 1, 1)
    tag = "@" + d["user"].upper()
    c.text(W - 12 - text_width(tag, 1), 8, tag, CREAM, 1)

    c.rect(154, 22, 1, 82, LINE)

    stats = [
        ("CONTRIB/YR", d["contrib"]),
        ("REPOS", d["repos"]),
        ("STARS", d["stars"]),
        ("FORKS", d["forks"]),
        ("FOLLOWERS", d["followers"]),
    ]
    y = 26
    for label, value in stats:
        c.text(14, y, label, GOLD_D, 1)
        v = f"{value:,}"
        c.text(148 - text_width(v, 1), y, v, CREAM, 1)
        y += 12

    c.text(164, 26, "LANGUAGES", GOLD, 1)
    c.text(164 + text_width("LANGUAGES", 1) + 6, 26, "BY REPO", DIM, 1)
    top = max([n for _, n in d["languages"]] + [1])
    y = 40
    BAR_X, BAR_W = 232, 52
    for i, (name, n) in enumerate(d["languages"]):
        col = LANG_COLOURS[i % len(LANG_COLOURS)]
        c.text(164, y, name[:11].upper(), CREAM if i == 0 else DIM, 1)
        c.rect(BAR_X, y + 1, BAR_W, 5, VOID)
        c.frame(BAR_X - 1, y, BAR_W + 2, 7, LINE)
        c.rect(BAR_X, y + 1, max(2, round(BAR_W * n / top)), 5, col)
        c.text(BAR_X + BAR_W + 6, y, str(n), CREAM, 1)
        y += 12

    c.rect(10, 108, W - 20, 1, LINE)
    c.text(14, 114, "ACHIEVEMENTS", GOLD_D, 1)
    c.text(14 + text_width("ACHIEVEMENTS", 1) + 6, 114,
           "PULL SHARK  PAIR EXTRAORDINAIRE", CREAM, 1)
    return c


if __name__ == "__main__":
    data, source = load()
    img = upscale(render(data))
    out = os.path.join(ROOT, "assets", "stats.png")
    img.save(out)
    print(f"wrote {out} from {source} data: {data}")
