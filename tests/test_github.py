"""Tests for Github related utilities."""

import pytest

from repo_stream.github import repo_url_to_full_name


@pytest.mark.parametrize(
    ('url', 'expected_result'),
    (
        ("https://github.com/mondeja/mdpo", "mondeja/mdpo"),
        (
            "https://github.com/mondeja/repo-stream.git",
            "mondeja/repo-stream.git",
        ),
    )
)
def test_repo_url_to_full_name(url, expected_result):
    assert repo_url_to_full_name(url) == expected_result
