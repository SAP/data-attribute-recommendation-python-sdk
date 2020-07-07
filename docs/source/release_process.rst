.. _release_process:


Creating a new release of the Data Attribute Recommendation SDK
===============================================================

*This document describes how to publish a new release of the SDK
to Pypi and does not apply to simple use of the SDK.*

To create a new release of the Data Attribute Recommendation Python SDK and
publish it to `pypi.org`_, you will need to have *write* access to the
`GitHub repository`_.

Follow these steps to create a release:

- Update `version.txt`_ with the desired version number
- Update the `CHANGELOG.md`_

  - Add a new heading with the new version number below *[Unreleased]*
  - The heading for the new version number should be a link to the
    (non-existing) tag on Github
  - *[Unreleased]* becomes an empty section
  - Update the tag used in the URL for *[Unreleased]* to the new version number
    so that *[Unreleased]* points to the changes between the new version
    and whatever is pushed to master afterwards

- Merge the updated `version.txt`_ and `CHANGELOG.md`_ to master
- Create a tag against the latest master with the desired version number
  and push the tag. This triggers the build and deploy on Travis.

  - No special permissions for pypi.org are required. Travis has access
    to a token which grants permission to publish to `pypi.org`.

.. code-block:: shell

  $ git pull
  $ git tag -a rel/x.y.z -m "Tagging release x.y.z"
  $ git push --tags

- A new build for the tag should appear to `Travis`_. Once the *deploy* stage
  has run successfully, the new version should be available on `pypi.org`_.
- The documentation on `Read The Docs`_ is automatically updated. A new version
  based on the git tag is also added. Note that the default documentation version
  displayed to visitors is always *latest* and is built from *master* on any update
  to the *master* branch.



.. _GitHub repository: https://github.com/SAP/data-attribute-recommendation-python-sdk
.. _pypi.org: https://pypi.org/project/data-attribute-recommendation-sdk/
.. _version.txt: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/version.txt
.. _CHANGELOG.md: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/CHANGELOG.md
.. _Travis: https://travis-ci.com/github/SAP/data-attribute-recommendation-python-sdk
.. _Read The Docs: https://data-attribute-recommendation-python-sdk.readthedocs.io/