import re
import json
import urllib.request
import os
from datetime import date
from dateutil.relativedelta import relativedelta

# Age / uptime
born = date(2001, 9, 27)
today = date.today()
rd = relativedelta(today, born)
uptime = f"{rd.years} years, {rd.months} months, {rd.days} days"

token = os.environ["GITHUB_TOKEN"]
username = os.environ.get("GITHUB_USERNAME", "sanzserif")

headers = {
    "Authorization": "Bearer " + token,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def gh_get(url, extra_headers=None):
    h = {**headers, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


user = gh_get(f"https://api.github.com/users/{username}")
followers = user.get("followers", 0)
public_repos = user.get("public_repos", 0)

stars = 0
page = 1
while True:
    repos = gh_get(
        f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
    )
    if not repos:
        break
    stars += sum(r.get("stargazers_count", 0) for r in repos)
    if len(repos) < 100:
        break
    page += 1

commits_data = gh_get(
    f"https://api.github.com/search/commits?q=author:{username}&per_page=1",
    {"Accept": "application/vnd.github.cloak-preview+json"},
)
commits = commits_data.get("total_count", 0)

with open("README.md", "r") as f:
    content = f.read()


def replace_between(text, tag, value):
    pattern = rf"<!--{tag}-->.*?<!--/{tag}-->"
    return re.sub(pattern, f"<!--{tag}-->{value}<!--/{tag}-->", text, flags=re.DOTALL)


content = replace_between(content, "UPTIME", uptime)
content = replace_between(content, "REPOS", str(public_repos))
content = replace_between(content, "STARS", f"{stars:,}")
content = replace_between(content, "COMMITS", f"{commits:,}")
content = replace_between(content, "FOLLOWERS", f"{followers:,}")

with open("README.md", "w") as f:
    f.write(content)

print(
    f"Done: uptime={uptime}, repos={public_repos}, stars={stars}, commits={commits}, followers={followers}"
)
