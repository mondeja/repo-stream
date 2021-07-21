"""Github related utilities."""

import functools
import json
import multiprocessing
import os
import urllib.parse
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


def parse_github_pagination(link_header):
    """Discover the latest page in a Github pagination response.

    Parameters
    ----------

    link_header : str
      "Link" header returned by a Github API paginated response.

    Returns
    -------

    int : Number of the latest page.
    """
    response = None

    for urldata in link_header.split(","):
        if urldata.split(" ")[-1].split('"')[1] == "last":
            url = urldata.split(";")[0][1:-1]
            response = int(
                urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["page"][0]
            )
            break
    return response


def _get_user_repos__request(url):
    req = urllib.request.Request(url)
    add_github_auth_headers(req)
    req = urllib.request.urlopen(req)
    return json.loads(req.read().decode("utf-8"))


def get_user_repos(username, fork=None, repositories_to_ignore=[], per_page=50):
    """Get all the repositories of a Github user giving certain conditions.

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

    per_page : int, optional
      Number of repositories to retrieve in each request to the Github API.

    Returns
    -------

    list : All the full names of the user repositories.
    """
    response = []

    build_url = lambda page: (
        f"https://api.github.com/users/{username}/repos?per_page={per_page}"
        f"&sort=updated&page={page}&type=owner"
        "&accept=application/vnd.github.v3+json"
    )

    req = urllib.request.Request(build_url(1))
    add_github_auth_headers(req)
    req = urllib.request.urlopen(req)
    link_header = req.getheader("Link")
    last = 1 if not link_header else parse_github_pagination(link_header)
    repos = json.loads(req.read().decode("utf-8"))

    def is_valid_repo(repo_data):
        if fork is not None:
            if repo["fork"] is not fork:
                return False  # booleans must match for this filter
        if repo_data["archived"]:
            return False
        if repo_data["full_name"] in repositories_to_ignore:
            return False
        return True

    for repo in repos:
        if is_valid_repo(repo):
            response.append(repo["full_name"])

    if last > 1:
        num_cores = multiprocessing.cpu_count()
        if last - 1 < num_cores:
            num_cores = last - 1
        pool = multiprocessing.Pool(processes=num_cores)

        urls = [build_url(page) for page in range(2, last + 1)]
        for repos in pool.map(_get_user_repos__request, urls):
            for repo in repos:
                if is_valid_repo(repo):
                    response.append(repo["full_name"])

    return response


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
