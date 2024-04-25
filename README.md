# Data Attribute Recommendation Python SDK

A client SDK for the Data Attribute Recommendation service on SAP Business Technology Platform (SAP BTP).
Part of [SAP AI Business Services].

# Description

[![Build Status](https://travis-ci.com/SAP/data-attribute-recommendation-python-sdk.svg?branch=master)](https://travis-ci.com/SAP/data-attribute-recommendation-python-sdk)
[![Coverage Status](https://coveralls.io/repos/github/SAP/data-attribute-recommendation-python-sdk/badge.svg?branch=master)](https://coveralls.io/github/SAP/data-attribute-recommendation-python-sdk?branch=master)
[![Documentation Status](https://readthedocs.org/projects/data-attribute-recommendation-python-sdk/badge/?version=latest)](https://data-attribute-recommendation-python-sdk.readthedocs.io/en/latest/?badge=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/data-attribute-recommendation-sdk)
[![PyPI version](https://badge.fury.io/py/data-attribute-recommendation-sdk.svg)](https://badge.fury.io/py/data-attribute-recommendation-sdk)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![REUSE status](https://api.reuse.software/badge/github.com/SAP/data-attribute-recommendation-python-sdk)](https://api.reuse.software/info/github.com/SAP/data-attribute-recommendation-python-sdk)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/4514/badge)](https://bestpractices.coreinfrastructure.org/projects/4514)

Goals of this SDK:

* Enable easy consumption of the Data Attribute Recommendation service
* Provide convenient higher-level abstraction on top of the service APIs
* Serve as reference implementation for other programming languages
* Provide sample notebooks for reference usage of various templates provided by DAR

## Release Notes

See [CHANGELOG.md].

Note that this project follows [Semantic Versioning](https://semver.org/). Versions
below `1.0.0` are not guaranteed to have a stable API. For this reason, please
pay attention to the [CHANGELOG.md].

## Resources

* NEW: [TechED 2020 workshop materials], including a Jupyter notebook!
* [Tutorials on Data Attribute Recommendation] - **Free Trial Available**
* [Tutorials on this SDK][SDK tutorials]
* [Data Attribute Recommendation documentation]
* [Blog Articles on Data Attribute Recommendation]
* [Documentation for this SDK][SDK documentation]

# Requirements

To use the SDK, you will need a recent version of Python. We actively support
and test Python ~~3.5~~ 3.6 up to Python 3.11. We aim to support all officially supported
Python version. This includes any Python version not
listed as `end-of-life` in the
[Python Developer's Guide](https://devguide.python.org/#branchstatus). You can check
the [Travis builds] to see which environments are actively tested.

Additionally, the `pip` and `virtualenv` tools should be installed. See
the [installation instructions][pip and virtual environments].

To use the SDK, you will need to have a service instance of the
Data Attribute Recommendation service. For existing users of
SAP BTP, please see the [Initial Setup].

If you are new to SAP BTP and Data Attribute Recommendation,
consider one of the following options:

* Free Trial via [Tutorials on Data Attribute Recommendation]
* [SAP Store]
* Contact your Sales Representative

# Download and Installation

The SDK is installable from the Python Package Index ([PyPI]). The easiest way
to install the SDK is via [pip and virtual environments]. With a virtual environment
(`virtualenv`), the installation process is isolated to a single directory and will
not influence any other projects you may have.

If you are familiar with Python and associated tooling, simply execute:

```shell script
$ python3 -m virtualenv dar-sdk-venv
$ source dar-sdk-venv/bin/activate/
(dar-sdk-venv) $ pip install data-attribute-recommendation-sdk
```

In case you prefer more detailed instructions, please see [step-by-step](#step-by-step)
instructions below. A separate, more detailed tutorial
[is also available at developers.sap.com][SDK Setup Tutorial].

## Step by Step

The following instructions assume a Linux or macOS environment. For Windows, the
process is similar, but the commands may differ slightly. If in doubt, refer
to the [Python documentation][pip and virtual environments].

First, create a working directory in your home directory.

```
$ cd $HOME
$ mkdir data-attribute-recommendation-python-sdk/
$ cd data-attribute-recommendation-python-sdk/
```

Now, create a virtualenv named `dar-sdk-venv`.

```
$ python3 -m virtualenv dar-sdk-venv
```

If you receive a message `command not found: python3`, then try using the `python`
command instead. If you still receive a message about `command not found`, please
ensure that [python is installed][python.org downloads].

If you observe `No module named virtualenv` error messages, make sure that [`virtualenv`
is installed.][installing virtualenv]

Now, activate the newly created environment:

```shell script
$ source dar-sdk-venv/bin/activate
(dar-sdk-venv) $
```

The name of the virtualenv is now part of your shell prompt.

Finally, install the SDK and its dependencies:

```shell script
(dar-sdk-venv) $ pip install data-attribute-recommendation-sdk
```

If you receive an error message `command not found: pip`, then refer to
[installing pip].

Congratulations! You have sucessfully installed the SDK. You may now import the
SDK package as a first test:

```
(dar-sdk-venv) $ python3
>>> from sap.aibus.dar.client.data_manager_constants import DataManagerPaths
>>> DataManagerPaths.ENDPOINT_DATASET_COLLECTION
'/data-manager/api/v3/datasets'
```

To use the SDK, please refer to the [SDK documentation]. In particular, consider 
the [SDK security guide].

# How to obtain support

For issues with the SDK itself, such as installation problems, please file
an [issue in Github][github issues].

For questions on how to best use the SDK, consider asking a question in the
SAP Community at **answers.sap.com** with the [`Data Attribute Recommendation` tag].
When creating your question, add `Data Attribute Recommendation` as a primary tag.

For issues experienced using the service, please refer to [Getting Support] in
the main documentation on the SAP Help Portal.

# License

Copyright (c) 2020 SAP SE or an SAP affiliate company. All rights reserved.
This file and all other files in this repository are licensed under the
Apache License, v 2.0 except as noted otherwise in the [LICENSE] file.

[TechED 2021 workshop materials]: https://github.com/SAP-samples/teched2021-INT360
[TechED 2020 workshop materials]: https://github.com/SAP-samples/teched2020-INT260
[Tutorials on Data Attribute Recommendation]: https://developers.sap.com/mission.cp-aibus-data-attribute.html
[SDK tutorials]: https://developers.sap.com/group.cp-aibus-data-attribute-sdk.html
[SAP AI Business Services]: https://help.sap.com/viewer/product/SAP_AI_BUS/SHIP/en-US
[SDK Setup Tutorial]: https://developers.sap.com/tutorials/cp-aibus-dar-sdk-setup.html
[Data Attribute Recommendation documentation]: https://help.sap.com/viewer/product/Data_Attribute_Recommendation/SHIP/en-US
[Blog Articles on Data Attribute Recommendation]: https://blogs.sap.com/tags/73554900100800002858/
[SAP Store]: https://www.sapstore.com/solutions/43157/Data-Attribute-Recommendation
[Initial Setup]: https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/e8d18fbd1c0445e4a39dd1b66d942962.html
[PyPI]: https://pypi.org/project/data-attribute-recommendation-sdk/
[pip and virtual environments]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
[python.org downloads]: https://www.python.org/downloads/
[installing virtualenv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
[installing pip]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-pip
[SDK documentation]: https://data-attribute-recommendation-python-sdk.readthedocs.io/en/latest/
[SDK security guide]: https://data-attribute-recommendation-python-sdk.readthedocs.io/en/latest/security.html
[github issues]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues
[Getting Support]: https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/08625005de8049c180a108765f63fcdb.html
[Travis builds]: https://travis-ci.com/SAP/data-attribute-recommendation-python-sdk
[CHANGELOG.md]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/CHANGELOG.md
[LICENSE]: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/LICENSE
[`Data Attribute Recommendation` tag]: https://answers.sap.com/tags/73554900100800002858
