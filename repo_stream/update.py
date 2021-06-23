"""repo-stream update command"""

import json
import os
import subprocess
import sys
import urllib.request
from urllib.error import HTTPError

import yaml
from pre_commit.main import main as pre_commit_run

from repo_stream.git import (
    git_add_all_commit,
    git_add_remote,
    git_push,
    git_random_checkout,
    git_set_remote_url,
    repo_default_branch_name,
    there_are_untracked_changes,
    tmp_repo,
)
from repo_stream.github import (
    add_github_auth_headers,
    create_github_pr,
    download_raw_githubusercontent,
    get_github_prs_number_head_body,
    get_user_repos,
    repo_url_to_full_name,
)


def _parse_repo_stream_hook_args(args):
    response = {}

    _next_is_config, _next_is_updater = (False, False)
    for arg in args:
        if _next_is_config:
            response["config"] = repo_url_to_full_name(arg)
            _next_is_config = False
        elif _next_is_updater:
            response["updater"] = arg
            _next_is_updater = False
        else:
            arg_without_script = arg.replace("-", "")
            if arg_without_script == "config":
                _next_is_config = True
            elif arg_without_script == "updater":
                _next_is_updater = True
            elif "=" in arg:
                argname, value = arg.split("=")
                argname = argname.replace("-", "")
                response[argname] = (
                    repo_url_to_full_name(value) if argname == "config" else value
                )
                _next_is_config = False
                _next_is_updater = False
    return response


def filter_repos_with_repo_stream_hook(repos):
    """Filter repositories which have a pre-commit configuration file and
    repo-stream hook defined inside it.

    Parameters
    ----------

    repos : list
      Repositories of a Github user.
    """
    response = []

    for repo in repos:
        sys.stdout.write(f"Searching repo-stream hooks in {repo}\n")
        default_branch_name = repo_default_branch_name(repo)

        repo_tree_url = (
            f"https://api.github.com/repos/{repo}/git/trees/"
            f"{default_branch_name}?recursive=0"
        )
        req = urllib.request.Request(repo_tree_url)
        add_github_auth_headers(req)
        tree_req = urllib.request.urlopen(req)
        tree_res = json.loads(tree_req.read().decode("utf-8"))

        for file in tree_res["tree"]:
            if file["path"] == ".pre-commit-config.yaml":
                file_url = (
                    f"https://raw.githubusercontent.com/{repo}/"
                    f"{default_branch_name}/.pre-commit-config.yaml"
                )

                file_req = urllib.request.urlopen(file_url)
                file_content = file_req.read().decode("utf-8")

                pc_config = yaml.safe_load(file_content)

                for pc_repo in pc_config["repos"]:
                    if pc_repo["repo"] == "https://github.com/mondeja/repo-stream":
                        for hook in pc_repo["hooks"]:
                            if hook["id"] == "repo-stream":
                                hook_args = _parse_repo_stream_hook_args(hook["args"])

                                sys.stdout.write(
                                    f" - Found: config={hook_args['config']}"
                                    f" updater={hook_args['updater']}\n"
                                )
                                response.append(
                                    {
                                        "repo": repo,
                                        "default_branch_name": default_branch_name,
                                        **hook_args,
                                    }
                                )
                break

    return response


def get_stream_config_pre_commit_configurations(repos_stream_config):
    """Add to repo-stream configurations for all collected repositories the
    content of the pre-commit configuration file that will be used to perform
    the update.

    Parameters
    ----------

    repos_stream_config : list
      Collected repositories with repo-stream configurations searching in
      Github repositories for users.
    """
    for i, repo in enumerate(repos_stream_config):
        try:
            repos_stream_config[i]["updater_content"] = download_raw_githubusercontent(
                repo["config"],
                repo["default_branch_name"],
                repo["updater"],
            )
        except HTTPError as err:
            if err.code == 404:
                sys.stderr.write(
                    f"Configuration repository '{repo['config']}' or"
                    f" file '{repo['updater']}.yaml' for repo-stream"
                    f" pre-commit hooks defined at '{repo['repo']}'"
                    " not found.\n"
                )
                return None
            raise err
    return repos_stream_config


def check_pr_already_opened(repo, branch_prefix):
    """Check if a repo-stream update pull request is already opened given a
    configuration.

    Parameters
    ----------

    repo : dict
      Repository object. This must contain the fields ``repo`` with the name
      of the repository to check, a ``config`` with the repository used to
      extract the pre-commit configuration for this update and a ``updater``
      value with a file path where the configuration is located.

    branch_prefix : str
      Prefix that must starts with the head reference of the pull request to
      consider that is a repo-stream update pull request.

    Returns
    -------

    bool : Indicates if the pull request is already opened, so there is no
      need to open another.
    """
    # get pull requests to see if there is one already open
    response = False
    prs = get_github_prs_number_head_body(repo["repo"])
    for number, head, body in prs:
        if not head.startswith(branch_prefix):
            continue

        config, updater = (None, None)
        for line in body.splitlines():
            if "config=" in line:
                config = line.split("config=")[1].strip()
            elif "updater=" in line:
                updater = line.split("updater=")[1].strip()
        if config == repo["config"] and updater == repo["updater"]:
            sys.stdout.write(
                f"Pull request #{number} already opened"
                f" for update using '{config}/"
                f"{updater}.yaml' configuration.\n"
            )
            response = True

    return response


def update(
    usernames,
    include_forks=False,
    branch_prefix="repo-stream--",
    repositories_to_ignore=[],
    dry_run=False,
):
    """Update repositories which have a repo-stream pre-commit config searching
    for certain users' repos, creating pull requests with the changes.


    Parameters
    ----------

    usernames : list
      Users for which to get repositories.

    include_forks : bool, optional
      Include forks of repositories stored by the user in its Github account.

    branch_prefix : str, optional
      Branch name prefix used for creating the patches. Opened pull requests
      will use that branch name to make changes.

    repositories_to_ignore : list, optional
      Repositories full names to ignore from being checked for repo-stream
      pre-commit hooks.

    dry_run : bool, optional
      Don't make pull requests, just prints to STDOUT when pull requests would
      be opened.

    Returns
    -------

    int : ``0`` if no errors happened, ``1`` otherwise.
    """
    update_exitcode = 0

    gh_username = os.environ.get("GITHUB_USERNAME")
    gh_token = os.environ.get("GITHUB_TOKEN")

    for user_i, username in enumerate(usernames):
        sys.stdout.write(f"Processing '{username}' user: ")
        try:
            user_repos = get_user_repos(
                username,
                fork=False if not include_forks else None,
                repositories_to_ignore=repositories_to_ignore,
            )
        except HTTPError as err:
            if err.code == 404:
                sys.stderr.write(f"User '{username}' does not exists in Github.\n")
                update_exitcode = 1
                continue
            raise err

        n_user_repos = len(user_repos)
        if n_user_repos:
            msg = f"{n_user_repos}"
            if not include_forks:
                msg += " non forked"
            msg += " repositories will be checked.\n"
            sys.stdout.write(msg)
        else:
            msg = "No repositories will be checked.\n"
            sys.stdout.write(msg)
            continue

        # get repositories repo-stream pre-commit hook configurations
        repos_stream_config = get_stream_config_pre_commit_configurations(
            filter_repos_with_repo_stream_hook(user_repos)
        )
        if repos_stream_config is None:
            update_exitcode = 1  # error
            continue

        sys.stdout.write("\n")

        for repo in repos_stream_config:
            sys.stdout.write(f"Cloning '{repo['repo']}'...\n")

            with tmp_repo(
                repo["repo"], username=gh_username, token=gh_token
            ) as repo_dirpath:
                config_filepath = os.path.join(
                    os.path.abspath(os.path.dirname(repo_dirpath)),
                    "._pre-commit-config.yaml",
                )

                with open(config_filepath, "w") as f:
                    f.write(repo["updater_content"])

                new_branch_name = git_random_checkout(prefix=branch_prefix)

                sys.stdout.write(
                    f"Running pre-commit using '{repo['config']}/"
                    f"{repo['updater']}.yaml' config\n"
                )
                pre_commit_exitcode = pre_commit_run(
                    [
                        "run",
                        "-c",
                        config_filepath,
                    ]
                )
                if pre_commit_exitcode != 0 and there_are_untracked_changes():
                    # get pull requests to see if there is one already open
                    _pull_request_opened = check_pr_already_opened(
                        repo,
                        branch_prefix,
                    )

                    if not _pull_request_opened:
                        # pull request
                        try:
                            git_add_remote(
                                repo["repo"],
                                gh_username,
                                gh_token,
                                remote="origin",
                            )
                        except subprocess.CalledProcessError:
                            pass
                        git_set_remote_url(
                            repo["repo"],
                            gh_username,
                            gh_token,
                            remote="origin",
                        )
                        git_add_all_commit(title="repo-stream update")
                        git_push("origin", new_branch_name)
                        sys.stdout.write(f"Pushed branch '{new_branch_name}'")

                        if dry_run:
                            sys.stdout.write(
                                "Pull request would be created for repository"
                                f" '{repo['repo']}' (triggered by"
                                f" '{repo['config']}/{repo['updater']}.yaml')\n"
                            )
                        else:
                            sys.stdout.write(
                                f"Creating pull request for repository"
                                f" '{repo['repo']}' (triggered by"
                                f" '{repo['config']}/{repo['updater']}.yaml')\n"
                            )
                            created_pr = create_github_pr(
                                repo["repo"],
                                "repo-stream update",
                                (
                                    "<!--\nThis comment is autogenerated. Please,"
                                    " don't edit it.\n\n"
                                    f"config={repo['config']}\n"
                                    f"updater={repo['updater']}\n"
                                    "-->\n\n"
                                    f"> Opened by {repo['config']}/"
                                    f"{repo['updater']}.yaml\n"
                                ),
                                new_branch_name,
                                repo["default_branch_name"],
                            )
                            sys.stdout.write(
                                "Pull request created by user"
                                f" '{created_pr['user']['login']}'.\n  You can"
                                f" see it at {created_pr['html_url']}\n"
                            )

                else:
                    sys.stdout.write("Repository is updated\n")

        if user_i < (len(usernames) - 1):
            sys.stdout.write("\n")

    return update_exitcode
