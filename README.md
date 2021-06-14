<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/repo-stream.png" alt="repo-stream">
</p>

Cron-based remote pre-commit executions by opening pull requests.

Do you've a lot of old projects that are using deprecated configuration? Maybe
you want to do a small change in a lot of projects at the same time, but you
don't want to go one by one? Those are the reasons behind repo-stream.

## How does it work?

Scans your repositories looking for pre-commit repo-stream hooks and run
pre-commit using another remote configuration file. If this execution edit file
contents, opens a pull request against the repository.

<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/sep1.png">
</p>

So you can use **repo-stream** to run one-time pre-commit hooks for all your
repositories without have to define them inside the configuration of each one. 

## Usage

1. Create a `repo-stream` hook in your pre-commit configuration. If this is
 found, repo-stream will search a pre-commit configuration file at
 `upstream.yaml` under `https://github.com/<your-username>/<stream-config-repo>`
 and will run it against the current repository. If a hook makes a change, a
 pull request will be created.

```yaml
- repo: https://github.com/mondeja/repo-stream
  rev: v1.0.0
  hooks:
    - id: repo-stream
      args:
        - -config=https://github.com/mondeja/repo-stream-config
        - -updater=upstream
```

2. Create your `repo-stream` configuration files repository, for example at
 `https://github.com/<your-username>/repo-stream-config`.
3. Create the pre-commit configuration files, following this example would be
 at `upstream.yaml`, for example:

```yaml
- repo: https://github.com/mondeja/pre-commit-hooks
  rev: v1.0.0
  hooks:
    - id: add-pre-commit-hook
      args: 
        - -repo=https://github.com/mondeja/pre-commit-hooks
        - -id=dev-extras-required
        - -rev=v1.0.0
```

4. Create the cron task using some platform like Github Actions:

```yaml
name: repo-stream update

on:
  schedule:
    - cron: 0 4 1/7 * *
  workflow_dispatch:

jobs:
  auto-update:
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
        run: repo-stream update <your-username>
```

> If you want to update other repositories not published under your user, pass
them as parameters of `repo-stream update <your-username> <other-username>`.

![---](sep2.png)