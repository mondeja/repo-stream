"""Github related utilities."""

import functools
import json
import os
import urllib.request


def repo_url_to_full_name(url):
    """Convert a repository absolute URL to ``full_name`` format used by Github.

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


def get_user_repos(username, fork=None, repositories_to_ignore=[]):
    """Get all the repositories of a Github user.

    Parameters
    ----------

    username : str
      Github user whose repositories will be returned.

    fork : bool, optional
      If is ``True``, only forked repositories will be returned, if is
      ``False``, only non forked repositories will be returned and being
      ``None`` both forked and unforked repositories will be returned.

    repositories_to_ignore : list, optional
      Full name of repositories which will not be included in the response.

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

        req = urllib.request.Request(get_user_repos_url)
        add_github_auth_headers(req)
        req = urllib.request.urlopen(req)
        res = json.loads(req.read().decode("utf-8"))

        n_repos = len(res)
        if not n_repos:
            break
        elif n_repos < 100:
            if fork is not None:
                new_repos = [
                    repo["full_name"]
                    for repo in res
                    if repo["fork"] is fork
                    and repo["full_name"] not in repositories_to_ignore
                    and not repo["archived"]
                ]
            else:
                new_repos = [
                    repo["full_name"]
                    for repo in res
                    if repo["full_name"] not in repositories_to_ignore
                    and not repo["archived"]
                ]

            repos.extend(new_repos)
            break
        else:
            if fork is not None:
                new_repos = [
                    repo["full_name"]
                    for repo in res
                    if repo["fork"] is fork
                    and repo["full_name"] not in repositories_to_ignore
                    and not repo["archived"]
                ]
            else:
                new_repos = [
                    repo["full_name"]
                    for repo in res
                    if repo["full_name"] not in repositories_to_ignore
                    and not repo["archived"]
                ]

            repos.extend(new_repos)
            page += 1

    return repos


def add_github_auth_headers(req):
    """Add Github authentication headers if them are present in environment variables.

    If the environment variable ``GITHUB_TOKEN`` is defined, then an ``Authorization``
    header is added to a :py:class:`urllib.request.Request` object.

    Parameters
    ----------

    req : urllib.request.Request
      HTTP request for which the authentication headers will be included.
    """
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    if GITHUB_TOKEN is not None:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")


@functools.lru_cache(maxsize=None)
def download_raw_githubusercontent(repo, branch, filename):
    """Download a raw text file content from a Github repository.

    Parameters
    ----------

    repo : str
      Repository full name inside which the file is stored.

    branch : str
      Branch name inside the file is stored.

    filename : str
      Path to the file inside the repository tree.


    Returns
    -------

    str : Downloaded content of the file.
    """
    file_url = (
        "https://raw.githubusercontent.com/"
        f"{repo.rstrip('/')}/{branch}/{filename}.yaml"
    )
    return urllib.request.urlopen(file_url).read().decode("utf-8")


def create_github_pr(repo, title, body, head, base):
    """Create a pull request for a Github repository.

    Parameters
    ----------

    repo : str
      Repository for which the pull request will be opened.

    title : str
      Pull request title.

    body : str
      Pull request message body content.

    head : str
      Name of the branch to be merged.

    base : str
      Name of the branch for which the changes will be applied.
    """
    url = f"https://api.github.com/repos/{repo}/pulls"

    data = json.dumps(
        {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
    ).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    add_github_auth_headers(req)

    req = urllib.request.urlopen(req)
    return json.loads(req.read().decode("utf-8"))


def get_github_prs(repo):
    """Get the data for all opened pull requests from a repository.

    Parameters
    ----------

    repo : str
      Repository full name from which the opened pull requests will be returned.
    """
    url = f"https://api.github.com/repos/{repo}/pulls"

    req = urllib.request.Request(url)
    add_github_auth_headers(req)

    req = urllib.request.urlopen(req)
    return json.loads(req.read().decode("utf-8"))


def get_github_prs_number_head_body(repo):
    """Get opened pull requests numbers, head reference name and message body
    content for a repository.

    Parameters
    ----------

    repo : str
      Repository full name from which the opened pull requests will be returned.
    """
    return [
        (pr["number"], pr["head"]["ref"], pr["body"]) for pr in get_github_prs(repo)
    ]
