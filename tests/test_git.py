"""Tests for GIT related functionalities."""

import os
import tempfile

import pytest

from repo_stream.git import repo_default_branch_name, tmp_repo


@pytest.mark.parametrize(
    ("repo", "expected_result"),
    (
        ("mondeja/mdpo", "master"),
        ("mondeja/repo-stream", "master"),
        ("PyCQA/isort", "main"),
    ),
)
def test_repo_default_branch_name(repo, expected_result):
    assert repo_default_branch_name(repo) == expected_result


@pytest.mark.parametrize(
    ("repo"),
    (
        "mondeja/pre-commit-hooks",
        "mondeja/pre-commit-po-hooks",
    )
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
        
    