"""Tests for GIT related functionalities."""

import os
import subprocess
import tempfile

import pytest

from repo_stream.git import (
    git_random_checkout,
    repo_default_branch_name,
    tmp_repo,
)


@pytest.mark.parametrize(
    ("repo", "expected_result"),
    (
        ("mondeja/mdpo", "master"),
        ("mondeja/repo-stream", "master"),
        ("PyCQA/isort", "main"),
        ("mondeja/impossibleandcrazyfooname", subprocess.CalledProcessError),
    ),
)
def test_repo_default_branch_name(repo, expected_result):
    if hasattr(expected_result, "__traceback__"):
        with pytest.raises(expected_result):
            repo_default_branch_name(repo, protocol="ssh")
    else:
        assert repo_default_branch_name(repo, protocol="ssh") == expected_result


@pytest.mark.parametrize(
    ("repo"),
    (
        "mondeja/pre-commit-hooks",
        "mondeja/pre-commit-po-hooks",
    ),
)
def test_tmp_repo(repo):
    prev_cwd = os.getcwd()

    with tmp_repo(repo) as dirname:
        git_dir = os.path.join(dirname, ".git")
        assert os.path.isdir(git_dir)

        assert len(os.listdir(dirname))
        assert os.getcwd() != prev_cwd

    assert not os.path.isdir(dirname)
    assert os.getcwd() == prev_cwd


def test_git_random_checkout():
    prev_cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as dirpath:
        os.chdir(dirpath)

        subprocess.check_call(["git", "init", "--quiet"])

        stdout = subprocess.check_output(["git", "branch", "--show-current"])
        assert stdout.decode("utf-8") == "master\n"

        git_random_checkout()

        stdout = subprocess.check_output(["git", "branch", "--show-current"])
        assert stdout != "master\n"
        assert len(stdout.decode("utf-8").replace("\n", "")) == 8

        os.chdir(prev_cwd)
