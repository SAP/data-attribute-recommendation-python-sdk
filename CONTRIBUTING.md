# How to report an issue

You can report any issues with the SDK in the
[issues] section on Github. We appreciate your feedback!

Once you have created the issue, we will try to get back to
you as soon as possible.

For other concerns, such as questions on the Data Attribute
Recommendation service, please refer to the
["How to obtain support"][support] section in the main README.

If you would like to report a security issue, please see [SECURITY.md].

[issues]: https://github.com/SAP/data-attribute-recommendation-python-sdk
[support]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/README.md#how-to-obtain-support
[SECURITY.md]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/SECURITY.md
# How to contribute

This project welcomes outside contributions. For small contributions, such
as corrections of typos, please open a [pull request] on Github with your
change.

[pull request]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare

Once you have created the PR, we will try to get back to
you as soon as possible.

For larger changes, please open an [issue][issues] first to discuss. We will be happy
to give our feedback on the proposed design! This includes new features, but also
larger refactoring efforts.

## Tests and Style Checks

### The short version

To install pre-commit and run all code checks:

```shell script
$ pip install -r requirements-dev.txt
$ pre-commit install
$ pre-commit run --all
```

See below for details on
[Code Style and Pre-Commit Checks](#code-style-and-pre-commit-checks).

To run the tests:

```shell script
$ pip install -r requirements-test.txt
$ tox
```

To run the system tests against a live instance of the Data Attribute Recommendation
service, provide the [credentials] as environment variables and run:

```shell script
$ tox -e system_tests
```

See below for more information on [Running Tests](#running-tests).

## Code Quality

### Code Style and Pre-Commit Checks

This project uses the black code formatter for Python. Additionally, we use
several code linting and static analysis tools to ensure that our code base
remains high-quality and maintainable.

We maintain this collection of checks with [pre-commit]. All the checks are
configured inside of [.pre-commit-config.yaml]. This allows you to check every
change you commit automatically.

[pre-commit]: https://pre-commit.com/
[.pre-commit-config.yaml]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/.pre-commit-config.yaml

To set up `pre-commit`, run the following:

```shell script
$ pip install -r requirements-dev.txt
$ pre-commit install
```

Optionally, to verify your installation, you can execute `pre-commit`
manually to check all files:

```shell script
$ pre-commit run --all
```

Now, every time you run `git commit`, the checks will run. If a check fails,
the `git commit` operation is aborted and you can fix the problem. Once the issue
is resolved, you can run `git add` to add your changes to the commit
and try `git commit again`.

Some checks will automatically fix any issues that they find. The `black` formatter,
for example, will automatically format your changes correctly. For other checks,
you will have to fix the issue manually. Nevertheless,
you still have to commit the updated version explicitly.

If you experience problems with a single check, you can disable it as follows:

```shell script
$ SKIP=pylint git commit
```

The values for `SKIP` can be taken from the `id` field in [.pre-commit-config.yaml].

To disable *all* checks for a commit, use the following:

```shell script
$ git commit --no-verify
```

In general, do not hesitate to submit a PR if the checks fail. We will be happy to
help you resolve any issues.

## Running tests

We use [tox] to execute tests.

[tox]: https://tox.readthedocs.io/en/latest/

To install tox, execute the following:

```shell script
$ pip install -r requirements-test.txt
```

To run the unit tests, simply call `tox`:

```shell script
$ tox
```

By default, `tox` will run tests against Python 3.8, 3.9, and 3.10.
If you do not have all of these versions installed, you can select only
those versions that you have installed:

```shell script
$ tox -e py38,py39,py310
```

The unit tests live in the [tests/] directory.

[tests/]: https://github.com/SAP/data-attribute-recommendation-python-sdk/tree/master/tests

See our `tox` configuration file at [tox.ini] for details.

[tox.ini]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/tox.ini

### System Tests

The system tests are a separate set of tests which run and end-to-end scenario against
a real instance of the Data Attribute Recommendation service. The system tests
live in [system_tests/].

[system_tests/]: https://github.com/SAP/data-attribute-recommendation-python-sdk/tree/master/system_tests

To run the system tests locally, you will need to supply the [credentials as
environment variables][credentials]. However, it is often sufficient to run just the
unit tests, which is much faster.

To execute the system tests, invoke `tox` with the corresponding environment:

```shell script
$ tox -e system_tests
```

It is not required to run the system tests before submitting your PR.  The system tests
are executed by the [Travis CI] system once your PR is merged.

[credentials]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/f3883f2b56efefb704b0af58811261b4cb6d9b87/system_tests/conftest.py#L17

### Checks on Pull Requests

The checks above - both code quality and unit tests - are run automatically
for every PR on [Travis CI]. See our [travis configuration] for details.

For security reasons, the system tests are not executed from forked repositories.
Users with write access to the main repository will typically create PRs directly from
the main repository, in which case the system tests actually run also for PRs.

[Travis CI]: https://travis-ci.com/github/SAP/data-attribute-recommendation-python-sdk
[travis configuration]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/.travis.yml

This setup is a great safety net: all your proposed changes will be automatically
checked to make sure no regression is introduced.

### Tests and Code Coverage

We require that meaningful tests are added along each new feature.

Tests are implemented with [pytest].

[pytest]: https://docs.pytest.org/en/stable/

We aim not to reduce test coverage. We currently have over 96% test coverage
and we have a check which fails the test if the coverage falls
below this threshold (see [tox.ini]).

If you get a message similar to the following:

```
FAIL Required test coverage of 96% not reached. Total coverage: 92.54%
```

Then it is likely you added code without adding sufficient tests. If you don't know
how to add tests, please open a PR with your code and we will be happy to assist.

### Traceability

As stated above, we like to have tests that show that our project
- including new features - works correctly. For every release, we generate
a Test Evaluation Report which shows the features delivered and the successful
execution of tests covering this feature.

If you add a new feature, we'd like to ask that you link the Github issue to
the (system) tests covering this feature. The Test Evaluation Report of the next
release will then include both the feature and its test.

Please see the documentation we have on the [maintenance of Test Evaluation Reports].

[maintenance of Test Evaluation Reports]: https://data-attribute-recommendation-python-sdk.readthedocs.io/en/latest/traceability.html
## Build Documentation using Sphinx

The documentation generation tool Sphinx is used to create and build the 
[Data Attribute Recommendation SDK Documentation].

[Data Attribute Recommendation SDK Documentation]: https://data-attribute-recommendation-python-sdk.readthedocs.io/en/latest/

This is usually done and published automatically, but if you are working on
documentation parts and want to build it locally with Sphinx, you can follow the below steps.

To navigate to the [docs] folder where the source files and configuration file
of the documentation exists:

[docs]: https://github.com/SAP/data-attribute-recommendation-python-sdk/tree/main/docs
```shell script
$ cd docs
```
To install Sphinx:
```shell script
$ pip install -r requirements.txt
```
To generate the HTML documentation:
```shell script
$ make html
```
After a successful build, the HTML pages will be available in **docs/build/html** folder.

## Developer Certificate of Origin (DCO)

Due to legal reasons, contributors will be asked to accept a DCO before they submit
the first pull request to this projects, this happens in an automated fashion during
the submission process. SAP uses
[the standard DCO text of the Linux Foundation](https://developercertificate.org/).