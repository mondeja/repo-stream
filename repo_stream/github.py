"""Github related utilities."""

import json
import os
import time
import urllib.request


def repo_url_to_full_name(url):
    """Converts a repository absolute URL to ``full_name`` format used by
    Github.

    Parameters
    ----------

    url : str
      URL of the repository.

    Returns
    -------

    url : str
      Full name of the repository accordingly with Github API.
    """
    return "/".join(url.split("/")[3:])


def get_user_repos(username):
    """Returns all the repositories of a Github user.

    Parameters
    ----------

    username : str
      Github user whose repositories will be returned.

    Returns
    -------

    list : All the full names of the user repositories.
    """
    repos = []

    page = 1
    while True:
        get_user_repos_url = (
            f"https://api.github.com/users/{username}/repos?per_page=100"
            f"&sort=updated&page={page}&type=owner"
            "&accept=application/vnd.github.v3+json"
        )

        req = urllib.request.urlopen(get_user_repos_url)
        res = json.loads(req.read().decode("utf-8"))

        n_repos = len(res)
        if not n_repos:
            break
        elif n_repos < 100:
            repos.extend([repo["full_name"] for repo in res])
            break
        else:
            repos.extend([repo["full_name"] for repo in res])
            page += 1

        time.sleep(0.1)

    return repos


def install_github_auth():
    """Install Github authentication headers as request opener for urllib."""
    GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

    if GITHUB_USERNAME is not None and GITHUB_TOKEN is not None:
        opener = urllib.request.build_opener()
        opener.addheaders = [("Authorization", f"token {GITHUB_TOKEN}")]
        urllib.request.install_opener(opener)
