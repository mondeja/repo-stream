"""repo-stream update command"""

import functools
import json
import os
import sys
import urllib.request

import yaml
from pre_commit.main import main as pre_commit_run

from repo_stream.git import (
    create_github_pr,
    git_add_all_commit,
    git_push,
    git_random_checkout,
    repo_default_branch_name,
    there_are_untracked_changes,
    tmp_repo,
)
from repo_stream.github import get_user_repos, repo_url_to_full_name


def parse_repo_stream_hook_args(args):
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
                response[argname] = (
                    repo_url_to_full_name(value) if argname == "config" else value
                )
                _next_is_config = False
                _next_is_updater = False

    return response


def filter_repos_with_repo_stream_hook(repos):
    
    response = []

    for repo in repos:
        sys.stdout.write(f"Searching repo-stream hooks in {repo}...\n")
        default_branch_name = repo_default_branch_name(repo)

        repo_tree_url = (
            f"https://api.github.com/repos/{repo}/git/trees/"
            f"{default_branch_name}?recursive=0"
        )

        tree_req = urllib.request.urlopen(repo_tree_url)
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
                                sys.stdout.write(f"Found repo-stream at {repo}\n")
                                response.append(
                                    {
                                        "repo": repo,
                                        "default_branch_name": default_branch_name,
                                        **parse_repo_stream_hook_args(hook["args"]),
                                    }
                                )
                break

    return response


@functools.lru_cache(maxsize=None)
def get_stream_config_file_content(config, default_branch_name, updater):
    file_url = (
        f"https://raw.githubusercontent.com/{config}"
        f"/{default_branch_name}/{updater}.yaml"
    )

    file_req = urllib.request.urlopen(file_url)
    return file_req.read().decode("utf-8")


def get_stream_config_pre_commit_configurations(repos_stream_config):
    for i, repo in enumerate(repos_stream_config):
        repos_stream_config[i]["updater_content"] = get_stream_config_file_content(
            repo["config"],
            repo["default_branch_name"],
            repo["updater"],
        )
    return repos_stream_config


def update(usernames, dry_run=False):
    
    for username in usernames:
        sys.stdout.write(f"Processing user '{username}'...\n")
        user_repos = get_user_repos(username)
        
        sys.stdout.write(f"Found {len(user_repos)} repositories.\n")

        # get repositories repo-stream pre-commit hook configurations
        repos_stream_config = get_stream_config_pre_commit_configurations(
            filter_repos_with_repo_stream_hook(user_repos)
        )

        for repo in repos_stream_config:
            with tmp_repo(repo) as repo_dirpath:
                config_filepath = os.path.join(
                    os.path.abspath(os.path.dirname(repo_dirpath)),
                    "._pre-commit-config.yaml",
                )

                with open(config_filepath, "w") as f:
                    f.write(repo["updater_content"])

                new_branch_name = git_random_checkout()

                exitcode = pre_commit_run(
                    [
                        "run",
                        "-c",
                        config_filepath,
                    ]
                )
                if exitcode != 0 and there_are_untracked_changes():
                    # pull request
                    git_add_all_commit()
                    git_push("origin", new_branch_name)

                    if dry_run:
                        sys.stderr.write(
                            "Pull request would be created for repository"
                            f" '{repo}' (triggered by '{repo['config']}/"
                            f"{repo['updater']}.yaml')\n"
                        )
                    else:
                        sys.stdout.write(
                            f"Creating pull request for repository '{repo}'"
                            f" (triggered by '{repo['config']}/"
                            f"{repo['updater']}.yaml')\n"
                        )
                        create_github_pr(
                            repo,
                            "repo-stream update",
                            (
                                f"> Triggered by {repo['config']}/"
                                f"{repo['updater']}.yaml\n"
                            ),
                            new_branch_name,
                            repo["default_branch_name"],
                        )
