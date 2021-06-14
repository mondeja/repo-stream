"""Tests for Github related utilities."""

import pytest

from repo_stream.github import get_user_repos, repo_url_to_full_name


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
    "username",
    ("rajednom", "mondeja"),
)
def test_get_user_repos(username):
    repos = get_user_repos(username)
    assert isinstance(repos, list)
    assert len(repos) > 0

    for repo in repos:
        assert repo.startswith(f"{username}/")
        assert (
            len(repo.split("/", 1)[0] + repo.split("/", 1)[1].replace("/", ""))
            == len(repo) - 1
        )
