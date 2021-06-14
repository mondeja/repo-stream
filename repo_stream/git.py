"""GIT utilities for repo-stream."""

import contextlib
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
import uuid


def repo_default_branch_name(repo):
    """Get the default branch name of a remote repository.

    Parameters
    ----------

    repo : str
      Github repository owner and name, in the form ``"<username>/<project>"``.

    Returns
    -------

    str : Default branch name of the repository.
    """
    return (
        subprocess.check_output(
            [
                "git",
                "ls-remote",
                "--symref",
                f"https://github.com/{repo}",
                "HEAD",
            ]
        )
        .decode("utf-8")
        .splitlines()[0]
        .split("/")[2]
        .split(" ")[0]
        .split("\t")[0]
    )


@contextlib.contextmanager
def tmp_repo(repo, platform="github.com"):
    """Create a temporal directory where clone a repository and move inside.

    Works as a context manager using ``with`` statement and when exits, comes
    back to the initial working directory.

    Parameters
    ----------

    repo : str
      Repository to clone.

    platform : str
      Platform provider where the repository is hosted.


    Yields
    ------

    str : Temporal cloned repository directory path (current working directory
      inside context).
    """
    prev_cwd = os.getcwd()

    try:
        with tempfile.TemporaryDirectory() as dirname:
            os.chdir(dirname)
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--depth=1",
                    f"https://{platform}/{repo}.git",
                ]
            )

            repo_dirpath = os.path.join(dirname, repo.split("/")[1])
            os.chdir(repo_dirpath)
            yield repo_dirpath
    finally:
        os.chdir(prev_cwd)


def git_random_checkout(quiet=True, length=8):
    """Creates a new branch with a random name of certain length.

    Parameters
    ----------

    quiet : bool, optional
      When enabled, creates the new branch without printing to STDOUT.

    length : int, optional
      Length for the name of the new branch.


    Returns
    -------

    str : New branch name.
    """
    new_branch_name = uuid.uuid4().hex[:length]
    cmd = ["git", "checkout", "-b", new_branch_name]
    if quiet:
        cmd.append("--quiet")
    subprocess.check_call(cmd)
    return new_branch_name


def there_are_untracked_changes():
    """Indicates if in the current GIT repository there are files with
    untracked changes.
    """
    return subprocess.check_output(["git", "diff", "--shortstat"]) != b""


def git_add_all_commit(title="", description=""):
    subprocess.check_call(["git", "add", "."])

    commit_args = []
    if title:
        commit_args.extend(["-m", title])
    commit_args.extend(["-m", description or "Empty commit"])
    return subprocess.check_call(["git", "commit", *commit_args])


def create_github_pr(repo, title, body, head, base):
    url = f"https://api.github.com/repos/{repo}/pulls"

    data = urllib.parse.urlencode(
        {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
    ).encode()

    req = urllib.request.urlopen(urllib.request.Request(url, data=data))
    return json.loads(req.read().encode("utf-8"))


def git_push(source, target):
    subprocess.check_call(["git", "push", source, target])
