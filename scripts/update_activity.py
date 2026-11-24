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
    repositories(privacy: PUBLIC, isFork: false) { totalCount }
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
    maximum = max(max(counts), 1)
    points = " ".join(
        f"{315 + i * 350 / (len(days) - 1):.2f},{155 - count * 85 / maximum:.2f}"
        for i, count in enumerate(counts)
    )
    labels = [
        (82, f'{calendar["totalContributions"]:,} Contributions'),
        (111, f'{collection["totalCommitContributions"]:,} Commits'),
        (140, f'{user["repositories"]["totalCount"]:,} Public Repos (non-fork)'),
    ]
    rows = "".join(f'<text x="30" y="{y}" font-size="14">{escape(label)}</text>' for y, label in labels)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="200" viewBox="0 0 700 200" role="img" aria-labelledby="title description">
  <title id="title">seonjeong20 — GitHub Activity</title>
  <desc id="description">GitHub contribution calendar, {days[0]['date']} to {days[-1]['date']}. Contributions include commits, pull requests, issues and reviews. Public activity only when generated with the workflow token.</desc>
  <rect x="1" y="1" width="698" height="198" rx="5" fill="#FAFAFD" stroke="#DDDDE9"/>
  <g font-family="'Segoe UI',Ubuntu,Arial,sans-serif" fill="#5E5A70">
    <text x="30" y="39" font-size="22" fill="#7C3AED">seonjeong20 — GitHub Activity</text>
    {rows}
    <path d="M315 70V155H665" fill="none" stroke="#DDDDE9"/>
    <polygon points="315,155 {points} 665,155" fill="#EDE9FE"/>
    <polyline points="{points}" fill="none" stroke="#A78BFA" stroke-width="1.5" stroke-linejoin="round"/>
    <g font-size="10" fill="#7F7A90">
      <text x="315" y="173">{days[0]['date']}</text>
      <text x="665" y="173" text-anchor="end">{days[-1]['date']}</text>
      <text x="30" y="180">GitHub API · past year</text>
      <text x="665" y="57" text-anchor="end">Daily contributions · max {maximum}</text>
    </g>
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
