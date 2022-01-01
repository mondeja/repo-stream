<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/images/repo-stream.png" alt="repo-stream" width="90%">
</p>

Cron-based remote [pre-commit][pre-commit] executions by opening pull requests.

- Do you've a lot of old projects that are using deprecated configuration?
- Do you want to test a small change in a lot of projects at the same time
 without adding them one by one?

Those are the reasons behind **repo-stream**.

[![PyPI version][pypi-version-image]][pypi-link]
[![Test][test-image]][test-link]
[![Coverage status][coverage-image]][coverage-link]

## How does it work?

Scans your repositories looking for pre-commit ``repo-stream`` hooks and run
pre-commit using another remote configuration file, which location is specified
in this hook. If this execution edits file contents, opens a pull request
against the repository.

So you can use **repo-stream** to run one-time pre-commit hooks for all your
repositories without have to define them inside the configuration of each one. 

## Usage

1. Create a `repo-stream` hook in the pre-commit configuration of your project.
 If this is found, **repo-stream** will search a pre-commit configuration file
 at `updater` under `config` repository arguments and will run pre-commit using
 that configuration against the current repository.

   ```yaml
   - repo: https://github.com/mondeja/repo-stream
     rev: v1.3.1
     hooks:
       - id: repo-stream
         args:
           - -config=https://github.com/<your-username>/repo-stream-config
           - -updater=upstream
   ```
   > You don't need to specify the extension ``.yaml`` in the ``updater``
    argument.

2. Create your `repo-stream` configuration files repository, for example at
 `https://github.com/<your-username>/repo-stream-config`.
3. Create the pre-commit configuration file, following this example would be
 at `upstream.yaml`, for example:

   ```yaml
   repos:
     - repo: https://github.com/mondeja/pre-commit-hooks
       rev: v1.5.2
       hooks:
         - id: add-pre-commit-hook
           args: 
             - -repo=https://github.com/mondeja/pre-commit-hooks
             - -id=dev-extras-required
             - -rev=v1.5.2
   ```
   
   > For more information about this hook see
    [add-a-pre-commit-hook][add-a-pre-commit-hook].

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

> Consult `repo-stream --help` for documentation about valid arguments.

### Usage as Github Action

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
      - uses: actions/setup-python@v2
        with:
          python-version: 3.x
      - uses: mondeja/repo-stream@v1.3.1
        with:
          usernames: <your-username> <other-username>
          args: --dry-run
        env:
          GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
          GITHUB_USERNAME: <your-username>
```

## Common workflows

### Add a pre-commit hook

You can use the pre-commit hook
[`mondeja/pre-commit-hooks#add-pre-commit-hook`][add-pre-commit-hook] to add a
new pre-commit hook to the pre-commit configuration of a project.

> Note that this hook only makes sense executed from outside, using a workflow
 like **repo-stream**. So **repo-stream** allows you to create pre-commit hooks
 for other things than its main workflow mechanism.

For example:

```yaml
# upstream.yaml
repos:
  - repo: https://github.com/mondeja/pre-commit-hooks
      rev: v1.5.2
      hooks:
        - id: add-pre-commit-hook
          args: 
            - -repo=https://github.com/mondeja/pre-commit-hooks
            - -id=dev-extras-required
            - -rev=v1.5.2
```

This would add the hook [`dev-extras-required`][dev-extras-required] to the
pre-commit configuration of your project, if it isn't already defined.

## Current limitations

- Only works with Github repositories.

<br>
<p align="center">
  <img src="https://raw.githubusercontent.com/mondeja/repo-stream/master/images/sep1.png" width="82%">
</p>


[pypi-version-image]: https://img.shields.io/pypi/v/repo-stream?label=version&logo=pypi&logoColor=white
[pypi-link]: https://pypi.org/project/repo-stream
[test-image]: https://img.shields.io/github/workflow/status/mondeja/repo-stream/CI?label=tests&logo=github
[test-link]: https://github.com/mondeja/repo-stream/actions?query=workflow%3ACI
[coverage-image]: https://img.shields.io/coveralls/github/mondeja/repo-stream?logo=coveralls
[coverage-link]: https://coveralls.io/github/mondeja/repo-stream

[pre-commit]: https://pre-commit.com
[add-pre-commit-hook]: https://github.com/mondeja/pre-commit-hooks#add-pre-commit-hook
[add-a-pre-commit-hook]: https://github.com/mondeja/repo-stream#add-a-pre-commit-hook
[dev-extras-required]: https://github.com/mondeja/pre-commit-hooks#dev-extras-required
