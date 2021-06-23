<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/images/repo-stream.png" alt="repo-stream" width="90%">
</p>

Cron-based remote pre-commit executions by opening pull requests.

Do you've a lot of old projects that are using deprecated configuration? Maybe
you want to do a small change in a lot of projects at the same time, but you
don't want to go one by one? Those are the reasons behind repo-stream.

[![PyPI version][pypi-version-image]][pypi-link]
[![Test][test-image]][test-link]
[![Coverage status][coverage-image]][coverage-link]

## How does it work?

Scans your repositories looking for pre-commit repo-stream hooks and run
pre-commit using another remote configuration file. If this execution edit file
contents, opens a pull request against the repository.

So you can use **repo-stream** to run one-time pre-commit hooks for all your
repositories without have to define them inside the configuration of each one. 

## Usage

1. Create a `repo-stream` hook in your pre-commit configuration. If this is
 found, repo-stream will search a pre-commit configuration file at
 `updater` under `config` repository and will run it against the current
 repository. If a hook makes a change, a pull request will be created.

```yaml
- repo: https://github.com/mondeja/repo-stream
  rev: v1.1.0
  hooks:
    - id: repo-stream
      args:
        - -config=https://github.com/<your-username>/repo-stream-config
        - -updater=upstream
```

2. Create your `repo-stream` configuration files repository, for example at
 `https://github.com/<your-username>/repo-stream-config`.
3. Create the pre-commit configuration file, following this example would be
 at `upstream.yaml`, for example:

```yaml
repos:
  - repo: https://github.com/mondeja/pre-commit-hooks
    rev: v1.1.0
    hooks:
      - id: add-pre-commit-hook
        args: 
          - -repo=https://github.com/mondeja/pre-commit-hooks
          - -id=dev-extras-required
          - -rev=v1.1.0
```

4. Create the cron task using some platform like Github Actions:

```yaml
name: repo-stream update

on:
  schedule:
    - cron: 0 4 1/7 * *
  workflow_dispatch:

jobs:
  repo-stream-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.x
      - name: Install repo-stream
        run: pip install repo-stream
      - name: Run repo-stream update
        run: repo-stream <your-username>
        env:
          GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
          GITHUB_USERNAME: <your-username>
```

- ``GH_TOKEN`` must be a secret configured for the repository with the Github
 user token of `<your-username>` user.
- If you want to update other repositories not published under your user, pass
them as parameters of `repo-stream <your-username> <other-username>`.

## Current limitations

- Only works with Github repositories.

<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/images/sep1.png" width="82%">
</p>


[pypi-version-image]: https://img.shields.io/pypi/v/repo-stream?label=version&logo=pypi&logoColor=white
[pypi-link]: https://pypi.org/project/repo-stream
[test-image]: https://img.shields.io/github/workflow/status/mondeja/repo-stream/CI?label=tests&logo=github
[test-link]: https://github.com/mondeja/repo-stream/actions?query=workflow%3ACI
[coverage-image]: https://img.shields.io/coveralls/github/mondeja/repo-stream?logo=coveralls
[coverage-link]: https://coveralls.io/github/mondeja/repo-stream
