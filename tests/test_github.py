"""Tests for Github related utilities."""

import os

import pytest

from repo_stream.github import (
    add_github_auth_headers,
    get_user_repos,
    repo_url_to_full_name,
)


@pytest.mark.parametrize(
    ("url", "expected_result"),
    (
        ("https://github.com/mondeja/mdpo", "mondeja/mdpo"),
        (
            "https://github.com/mondeja/repo-stream.git",
            "mondeja/repo-stream.git",
        ),
    ),
)
def test_repo_url_to_full_name(url, expected_result):
    assert repo_url_to_full_name(url) == expected_result


@pytest.mark.parametrize(
    "fork",
    (None, True, False),
    ids=("fork=None", "fork=True", "fork=False"),
)
@pytest.mark.parametrize(
    "username",
    ("rajednom", "mondeja"),
    ids=("username=rajednom", "username=mondeja"),
)
def test_get_user_repos(username, fork):
    repos = get_user_repos(username, fork=fork)
    assert isinstance(repos, list)
    assert len(repos) > 0

    for repo in repos:
        assert isinstance(repo, str)
        assert repo.count("/") == 1
        assert repo.startswith(f"{username}/")
        assert (
            len(repo.split("/", 1)[0] + repo.split("/", 1)[1].replace("/", ""))
            == len(repo) - 1
        )


@pytest.mark.parametrize(
    "github_token",
    (None, "fake"),
    ids=("GITHUB_TOKEN=None", "GITHUB_TOKEN=<str>"),
)
def test_add_github_auth_headers(github_token):
    prev_github_token = os.environ.get("GITHUB_TOKEN")

    class FakeRequest:
        def __init__(self):
            self.headers = []

        def add_header(self, key, value):
            self.headers.append((key, value))

    if github_token is not None:
        os.environ["GITHUB_TOKEN"] = github_token
    else:
        del os.environ["GITHUB_TOKEN"]

    req = FakeRequest()
    add_github_auth_headers(req)

    assert len(req.headers) == (1 if github_token is not None else 0)

    if prev_github_token is not None:
        os.environ["GITHUB_TOKEN"] = prev_github_token
    else:
        del os.environ["GITHUB_TOKEN"]
