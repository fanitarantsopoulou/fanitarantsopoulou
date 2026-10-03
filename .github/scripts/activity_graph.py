"""Render a 31-day contribution line chart as SVG (replacement for github-readme-activity-graph)."""
import json
import os
import sys
import urllib.request

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity-graph.svg"
DAYS = 31

BG, TITLE, LINE, POINT, AREA, AXIS = "#0D1117", "#F8BBD0", "#EF93C4", "#FF69B4", "#F8BBD0", "#F8BBD0"
W, H = 1200, 420
L, R, T, B = 80, 40, 70, 70

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
  contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def render(days):
    counts = [d["contributionCount"] for d in days]
    top = max(max(counts), 4)
    step = max(1, -(-top // 4))
    top = step * 4
    pw, ph = W - L - R, H - T - B

    def x(i):
        return L + pw * i / (len(days) - 1)

    def y(v):
        return T + ph * (1 - v / top)

    pts = [(x(i), y(c)) for i, c in enumerate(counts)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{L},{T + ph} {line} {L + pw},{T + ph}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Ubuntu, sans-serif">',
        "<style>.d{opacity:0;animation:f .6s ease forwards}@keyframes f{to{opacity:1}}"
        f".l{{stroke-dasharray:4000;stroke-dashoffset:4000;animation:s 2s ease forwards}}@keyframes s{{to{{stroke-dashoffset:0}}}}</style>",
        f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
        f'<text x="{W / 2}" y="40" fill="{TITLE}" font-size="22" text-anchor="middle">{USER}\'s Contribution Graph</text>',
    ]
    for k in range(5):
        v = step * k
        parts.append(f'<line x1="{L}" x2="{L + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{AXIS}" stroke-opacity=".15"/>')
        parts.append(f'<text x="{L - 12}" y="{y(v) + 4:.1f}" fill="{AXIS}" font-size="12" text-anchor="end">{v}</text>')
    for i, d in enumerate(days):
        parts.append(f'<text x="{x(i):.1f}" y="{T + ph + 22}" fill="{AXIS}" font-size="12" text-anchor="middle">{int(d["date"][-2:])}</text>')
    parts += [
        f'<text x="{W / 2}" y="{H - 14}" fill="{AXIS}" font-size="14" text-anchor="middle">Days</text>',
        f'<text x="22" y="{T + ph / 2}" fill="{AXIS}" font-size="14" text-anchor="middle" transform="rotate(-90 22 {T + ph / 2})">Contributions</text>',
        f'<polygon class="d" points="{area}" fill="{AREA}" fill-opacity=".25"/>',
        f'<polyline class="l" points="{line}" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>',
    ]
    for i, (px, py) in enumerate(pts):
        parts.append(f'<circle class="d" style="animation-delay:{i * 0.05:.2f}s" cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{POINT}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        f.write(render(fetch()))
