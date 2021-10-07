# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.8.3]

### Added

* Support for Business blueprint id in `create_job` and `create_job_and_wait` methods. [#114]

### Note: 
* This feature is **not supported** in DAR service it is added for internal testing purpose. 
* Either model_template_id or business_blueprint_id has to be specified in `create_job` method.
* Both model_template_id and business_blueprint_id are not allowed

[#114]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/114

## [0.8.2]

### Fixed

* HTTP errors sent by the Data Attribute Recommendation service are now reported correctly
  as a `DARHTTPException` (including debug information) even when the request was retried. [#109]
  Fixes [#104]

[#109]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/109
[#104]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/104

### Changed

* Remove passing of external deployment ID and job ID from SDK API. This functionality
  never materialized in the Data Attribute Recommendation service and is now also removed in
  the SDK.
  This is an API change in the SDK because it changes the method signature of some
  methods to remove the optional `job_id` and `deployment_id` arguments. Passing these arguments
  always resulted in an error returned by the Data Attribute Recommendation service. For this
  reason, this change is not a breaking change.
  This change effectively reverts [#98].
* Plain-text `http://` URLs are now allowed for `localhost`. This is useful for local
  development. [#108]

[#107]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/107
[#108]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/108

## [0.8.1]

### Fixed

* Fix specification of dependencies. The SDK package was incorrectly depending
  on an older version of the requests package. If you have installed 0.8.0, it is
  recommended to update to 0.8.1 and also ensure you have the latest dependencies. [#102]

[#102]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/102

## [0.8.0]

### Added

* Add [CONTRIBUTING.md] and [SECURITY.md] [#92]
* This project is now following the [Best Practices] set forth by the
  Core Infrastructure Initiative! See [CII badge details]. [#92]
* Add `construct_from_cf_env` method to construct client instances from
  Data Attribute Recommendation service binding on SAP Business Technology
  Platform. [#97]
* Add support for user-specified Job and Deployment IDs when creating the
  respective Job and Deployment resources. This change is not yet generally
  available in the Data Attribute Recommendation service. [#98]

[CONTRIBUTING.md]: /CONTRIBUTING.md
[SECURITY.md]: /SECURITY.md
[Best Practices]: https://www.coreinfrastructure.org/programs/best-practices-program/
[CII badge details]: https://bestpractices.coreinfrastructure.org/en/projects/4514

[#92]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/92
[#97]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/97
[#98]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/98

### Deprecated

* Python 3.5 has reached [end-of-life in September 2020](https://www.python.org/downloads/release/python-3510/).
  Support for Python 3.5 will be removed in one of the upcoming releases.

### Changed

* Documentation updated to include reference to TechED 2020 workshop [#93]
* Tests: report branch coverage [#93]
* Tests: run tests with Python 3.9

[#93]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/93

## [0.7.1]

### Added

* Added links to new tutorial [#72]
* CI: Enable CodeQL Analysis on Github [#88]

[#72]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/72
[#88]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/88

### Changed

* Improve logging: quieten OnlineCredentialsSource, make polling explicit [#81]

[#81]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/81

* Log job progress in ModelManagerClient.wait_for_job [#87]

[#87]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/87

## [0.7.0]

### Added

* Mark package as type-annotated (PEP-561) [#46], [#63]

### Changed

* Documentation: add link to SAP community [#58]
* `ModelCreator.create` performs an initial check if the model name is already used
  and raises `ModelAlreadyExists` in this case [#60], [#64]
* `ModelManager.wait_for_job` now logs with level INFO while polling [#66]
* Change default `retry` parameter in `InferenceClient.do_bulk_inference` from
  `False` to `True`. Please check the updated documentation for implications on
   charging. [#67], [#62]

### Fixed

* Log message missing model deployment ID [#59]
* Expose a Dataset's `validationMessage` in `DatasetValidationFailed` [#33], [#69]

[#33]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/33
[#46]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/46
[#58]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/58
[#59]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/59
[#60]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/60
[#62]: https://github.com/SAP/data-attribute-recommendation-python-sdk/issues/62
[#63]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/63
[#64]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/64
[#66]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/66
[#67]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/67
[#69]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/69

## [0.6.8]

### Changed

* Improvements to build process [#55], [#56], [#57]
* No functional changes.

[#55]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/55
[#56]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/56
[#57]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/57

## [0.6.7]

### Changed

* Improvements to build process [#53]
* No functional changes.

[#53]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/53

## [0.6.6]

### Changed

* Improvements to build process [#52]
* No functional changes.

[#52]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/52

## [0.6.5]

### Changed

* Improvements to Documentation [#41], [#50]
* Generation of Traceability Reports [#48], [#49]

[#41]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/41
[#50]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/50
[#48]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/48
[#49]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/49

## [0.6.4]

### Changed

* Update links in README and setup.py [#27]
* Update documentation [#35]
* Fix links in documentation and switch the readthedocs.org theme [#37]
* Make documentation more consistent [#40]

## [0.6.3] - 2020-07-02

### Changed

* Improvements to build process
  * Coveralls integration [#16]
  * CI builds on windows [#8]
  * CI builds on macOS [#10]
  * Move `flake8` and `bandit` entirely to `pre-commit` [#6]
  * Fix description on pypi.org and update README [#14]
  * System tests added [#18]
  * System tests executed on Windows [#21]
  * Mail notifications for broken master builds [#20]


## [0.6.2] - 2020-06-30

### Added

* First public release

[Unreleased]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.8.3...HEAD
[0.8.3]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.8.2...rel/0.8.3
[0.8.2]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.8.1...rel/0.8.2
[0.8.1]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.8.0...rel/0.8.1
[0.8.0]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.7.1...rel/0.8.0
[0.7.1]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.7.0...rel/0.7.1
[0.7.0]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.8...rel/0.7.0
[0.6.8]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.7...rel/0.6.8
[0.6.7]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.6...rel/0.6.7
[0.6.6]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.5...rel/0.6.6
[0.6.5]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.4...rel/0.6.5
[0.6.4]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.3...rel/0.6.4
[#40]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/40
[#39]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/39
[#37]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/37
[#35]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/35
[#27]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/27
[0.6.3]: https://github.com/SAP/data-attribute-recommendation-python-sdk/compare/rel/0.6.2...rel/0.6.3
[#21]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/21
[#20]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/20
[#18]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/18
[#14]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/14
[#6]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/6
[#10]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/10
[#8]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/8
[#16]: https://github.com/SAP/data-attribute-recommendation-python-sdk/pull/16
[0.6.2]: https://github.com/SAP/data-attribute-recommendation-python-sdk/tree/rel/0.6.2
