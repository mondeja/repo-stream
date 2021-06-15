"""GIT utilities for repo-stream."""

import contextlib
import os
import subprocess
import tempfile
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
def tmp_repo(repo, username=None, token=None, platform="github.com"):
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
            auth_str = f"{username}:{token}@" if (username and token) else ""
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--depth=1",
                    f"https://{auth_str}{platform}/{repo}.git",
                ]
            )

            repo_dirpath = os.path.join(dirname, repo.split("/")[1])
            os.chdir(repo_dirpath)
            yield repo_dirpath
    finally:
        os.chdir(prev_cwd)


def git_random_checkout(quiet=True, length=8, prefix=""):
    """Create a new branch with a random name of certain length.

    Parameters
    ----------

    quiet : bool, optional
      When enabled, creates the new branch without printing to STDOUT.

    length : int, optional
      Length for the name of the new branch.

    prefix : str, optional
      Prepended at the beginning of the new branch name.

    Returns
    -------

    str : New branch name.
    """
    new_branch_name = f"{prefix}{uuid.uuid4().hex[:length]}"
    cmd = ["git", "checkout", "-b", new_branch_name]
    if quiet:
        cmd.append("--quiet")
    subprocess.check_call(cmd)
    return new_branch_name


def there_are_untracked_changes():
    """Indicate if in the current GIT repository there are files with
    untracked changes.
    """
    return subprocess.check_output(["git", "diff", "--shortstat"]) != b""


def git_add_remote(repo, username, token, remote="origin"):
    """Add a remote to the current GIT repository."""
    return subprocess.check_call(
        [
            "git",
            "remote",
            "add",
            remote,
            f"https://{username}:{token}@github.com/{repo}.git",
        ]
    )


def git_set_remote_url(repo, username, token, remote="origin"):
    """Set the URL of a remote for the current GIT repository."""
    return subprocess.check_call(
        [
            "git",
            "remote",
            "set-url",
            remote,
            f"https://{username}:{token}@github.com/{repo}.git",
        ]
    )


def git_add_all_commit(title="repo-stream update", description=""):
    """Run ``git add .`` and ``git commit -m`` commands.

    Parameters
    ----------

    title : str, optional
      Commit title.

    description : str, optional
      Commit description.
    """
    subprocess.check_call(["git", "add", "."])

    commit_args = []
    if title:
        commit_args.extend(["-m", title])
    commit_args.extend(["-m", description])
    return subprocess.check_call(["git", "commit", *commit_args])


def git_push(remote, target):
    """Run ``git push <remote> <target>`` command.

    Parameters
    ----------

    remote : str
      Remote name.

    target : str
      Branch to be pushed.
    """
    subprocess.check_call(["git", "push", remote, target])
