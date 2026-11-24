"""Render the activity card from GitHub's contribution calendar (stdlib only)."""

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


QUERY = """
query {
  user(login: "seonjeong20") {
    login
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def render(data):
    if data.get("errors"):
        raise ValueError(data["errors"])
    user = data["data"]["user"]
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    if len(days) < 300 or any(day["contributionCount"] < 0 for day in days):
        raise ValueError("Incomplete contribution calendar; keeping the previous card")
    counts = [day["contributionCount"] for day in days]
    active_days = sum(count > 0 for count in counts)
    stats = [
        ("CONTRIBUTIONS", calendar["totalContributions"], "commits + PRs + issues + reviews"),
        ("COMMITS", collection["totalCommitContributions"], "code, one change at a time"),
        ("ACTIVE DAYS", active_days, "days with a contribution"),
    ]
    tiles = ""
    for i, (label, value, caption) in enumerate(stats):
        x = 26 + i * 318
        tiles += f'''<g transform="translate({x},76)">
          <rect width="306" height="126" rx="5" fill="#FFFAFC" stroke="#E6B4C7"/>
          <text x="20" y="26" font-family="'Courier New',monospace" font-size="12" letter-spacing="1" fill="#A66C83">{label}</text>
          <text x="20" y="76" font-size="40" font-weight="700" fill="#94576D">{value:,}</text>
          <text x="20" y="105" font-size="12" fill="#996C7F">{escape(caption)}</text>
        </g>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="244" viewBox="0 0 1000 244" role="img" aria-labelledby="title description">
  <title id="title">Seonjeong's activity diary</title>
  <desc id="description">GitHub contribution summary, {days[0]['date']} to {days[-1]['date']}. {calendar['totalContributions']} contributions, {collection['totalCommitContributions']} commits, {active_days} active days. Public activity when generated with the workflow token.</desc>
  <defs><pattern id="dots" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1" fill="#EDC5D3"/></pattern></defs>
  <rect x="1" y="1" width="998" height="242" rx="8" fill="#FFF5F8" stroke="#DA9DB3"/>
  <path d="M1 49H999" stroke="#E6B4C7"/>
  <rect x="2" y="50" width="996" height="192" fill="url(#dots)"/>
  <g font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
    <text x="26" y="31" font-family="'Courier New',monospace" font-size="14" fill="#94576D">♡ activity diary</text>
    <text x="972" y="31" text-anchor="end" font-size="12" fill="#996C7F">small steps, saved here.</text>
    {tiles}
    <text x="26" y="226" font-size="11" fill="#94576D">GitHub · public activity · past year</text>
    <text x="972" y="226" text-anchor="end" font-size="11" fill="#94576D">{days[0]['date']} — {days[-1]['date']}</text>
  </g>
</svg>
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Render a saved GitHub API response")
    args = parser.parse_args()
    if args.input:
        data = json.loads(args.input.read_text())
    else:
        request = Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY}).encode(),
            headers={"Authorization": f'Bearer {os.environ["GH_TOKEN"]}',
                     "Content-Type": "application/json", "User-Agent": "profile-activity"},
        )
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
    svg = render(data)  # Validate the response before touching the last good card.
    target = Path(__file__).resolve().parents[1] / "assets/github-activity.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(svg, encoding="utf-8")
    temporary.replace(target)


if __name__ == "__main__":
    main()
