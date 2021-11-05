.. traceability:


Maintaining Traceability Reports
================================

To fulfill SAP-internal corporate requirements, this project maintains
**Test Evaluation Reports** for each release.

These reports allow the following:

* Understand what **requirements** were tested
* Understand **which tests** were used to validate the requirements
* Understand if those tests were **successful**

Hence, a test evaluation report traces requirements to tests to test execution and
is thus also called a **Traceability Report**.

The reports are generated during ::`release_process<release builds>`
on Travis. Once all tests have passed successfully, the report is published
as an artifact on the `Github release page`_ for the corresponding version
of the SDK.

If the build on Travis is not successful, no artifact is uploaded to Pypi and also
no test evaluation report is uploaded.

.. _Github release page: https://github.com/SAP/data-attribute-recommendation-python-sdk/releases


Linking Tests to Requirements
*****************************

When implementing a new **functional** requirement,
**you must also add a test** to show that it is working. Inside this test, use
the pytest framework to set a special marker which references the Github issue
describing the requirement.

With this marker in place, we know which requirements are tested by which test. The
result of the test execution is collected implicitly by pytest during test execution.

To link a test to requirement `#42`_ on Github, you can use the following
syntax:

.. note::

    Requirements are maintained as GitHub issues.

.. _#42: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/42

.. code-block:: python

    import pytest

    @pytest.mark.requirements(issues=["42"])
    def test_new_feature():
      # implement test
      assert False

It is also possible to reference multiple issues:

.. code-block:: python

    import pytest

    @pytest.mark.requirements(issues=["42", "43", "44"])
    def test_new_feature_2():
      # implement test
      assert False

The marker can also be applied on a class encapsulating several tests. Additionally,
individual tests inside the class may also be linked to other requirements:

.. code-block:: python

  import pytest

  @pytest.mark.requirements(issues=["42", "43"])
  class TestNewFeature:

    def test_feature_1(self):
      # implement test
      assert False


    @pytest.mark.requirements(issues=["44"])
    def test_feature_2(self):
      # implement test
      assert False

    @pytest.mark.requirements(issues=["45"])
    def test_feature_3():
      # implement test
      assert False

The resulting Test Evaluation report would link issues and tests as follows:

Simple table:

===========  =================================
Issues       Tests
===========  =================================
42, 43       ``TestNewFeature.test_feature_1``
42, 43, 44   ``TestNewFeature.test_feature_2``
42, 43, 45   ``TestNewFeature.test_feature_3``
===========  =================================

The test evaluation report is only generated when using pytest's html output. This
requires the ``pytest-html`` plugin and use the ``--html`` option when calling pytest.
On Travis, this is handled via `tox`_.

.. _tox: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/main/tox.ini

.. note::

  Currently, only system tests can be linked to requirements. While it may be useful
  to link unit or integration tests to functional requirements, this is currently
  simply not implemented. Both the required pytest instrumentation, the report
  generation and the report uploaded are only implemented for system tests. See
  pull request `#48`_ for the implementation details.

.. _#48: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/48
