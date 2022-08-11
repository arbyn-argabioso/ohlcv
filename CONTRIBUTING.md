# Contributing guidelines

## Pull Request Checklist

Before sending your pull requests, make sure you do the following:

- Read the [contributing guidelines](CONTRIBUTING.md)
- Ensure that the latest code changes are consistent with the [PEP8 Style Guide](https://www.python.org/dev/peps/pep-0008/).
- Ensure that the latest code changes are tested locally
- Run the [unit tests](#running-unit-tests)

## Become a Contributor

### Contribution guidelines and standards

Before sending your pull request for review, make sure your changes are consistent with the guidelines and follow the PEP8 coding style.

#### General guidelines and philosophy for contribution

- Include unit tests when you contribute new features, as they help to a) prove that your code works correctly, and b) guard against future breaking changes to lower the maintenance cost.
- Bug fixes also generally require unit tests, because the presence of bugs usually indicates insufficient test coverage.

#### Checking coding style

Changes to this code base should conform to the PEP8 Style Guide.

Use flake8 to check your Python changes. To install flake8 and check a file:

```shell
$ pip install -r requirements/dev.txt
$ flake8 ohlcv
```

#### Running unit tests

Changes to code base should not break any of the existing unit tests. New features are also required to include their own unit tests.

Use pytest to write your Python changes' unit tests. To install pytest and run the unit tests:

```shell
$ pip install -r requirements/dev.txt
$ pytest
```

Note: commands should be run from the root directory of the repository.
