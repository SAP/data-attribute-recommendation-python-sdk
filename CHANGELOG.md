# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Optional retry for Inference requests (disabled by default!)
* Optional retry for POST HTTP requests (internally used classes)

## [0.6.0] - 2020-04-09

### Added

* API documentation improvements
* Logging added in all relevant cases
* New method: ModelManagerClient.ensure_model_is_undeployed

### Fixed

* Removed retry on `POST`: `POST` is not a retryable method.

## [0.5.0] - 2020-04-01

### Added

* API documentation improvements
* New method: ModelManagerclient.ensure_deployment_exists
