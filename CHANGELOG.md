# BAS Assets Tracking Service - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Wherever possible, a reference to an issue in the project issue tracker should be included to give additional context.

## [Unreleased]

## [0.3.2] - 2024-07-21

### Fixed

* Outdated private key reference in Continuous Deployment
  [#59](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/59)

## [0.3.1] - 2024-07-21

### Fixed

* Outdated private key reference in Continuous Deployment
  [#59](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/59)

## [0.3.0] - 2024-07-21

### CHANGED [BREAKING!]

* resetting project based on experiments from [Pytest-postgres](https://gitlab.data.bas.ac.uk/felnne/pytest-pg-exp)

### Added

* CLI command to run providers manager fetch methods
  [#31](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/31)
* Basic Sentry integration
  [#10](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/10)
* GeoJSON exporter
  [#39](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/39)
* Initial ArcGIS exporter
  [#11](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/11)
* Preparing for deployment
  [#8](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/8)
* Project documentation
  [#2](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/2)

### Fixed

* `updated_at` DB column did not automatically update
  [#22](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/22)
* `ruff` linting settings and subsequent fixes to code
  [#32](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/32)
* Incorrect timezone in GeoJSON export
  [#41](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/41)
* Changing `psycopg` dependency to binary variant to avoid installation issues
  [#49](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/49)
* Migrations could not be run if already migrated
  [#51](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/51)

### Changed

* Derived units in latest asset positions export database view
  [#36](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/36)
* Downgrading to Python 3.11 due to `arcgis` dependency
  [#11](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/11)
* Provider configs refactored to use main config class
  [#43](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/43)

## [0.2.2] - 2024-04-30

### Fixed

* Temporarily disabling timezone checks for positions
  [#160](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/160)
* Updating dependencies to address Safety vulnerabilities
  [#162](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/162)
* Updating CI Python image to match version used in deployment environment
  [#165](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/165)

## [0.2.1] - 2023-02-15

### Fixed

* Adding missing documentation on deployment packages
  [#151](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/151)
* Adding missing documentation for testing deployment packages
  [#152](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/152)
* Adding missing config options for Geotab provider
  [#150](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/150)
* Adding v0.1.0 -> v0.2.0 specific upgrade guidance
  [#149](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/149)
* Improving upgrade and installation documentation
  [#149](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/149)

## [0.2.0] - 2023-02-10 [BREAKING!]

### Changed [BREAKING!]

* Replacing 'ship' with 'research vessel' in platform types enumeration
  [#128](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/128)

### Added

* Setup documentation
  [#111](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/111)
* Application CLI and `--version` command
  [#116](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/116)
* Conformation prompt when using the `migrate downgrade` command (dangerous action)
  [#117](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/117)
* `migrate history` command to list available migrations
  [#118](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/118)
* Command reference examples
  [#121](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/121)
* Initial provider implementation, as a set of base classes for use in per-provider implementations
  [#112](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/112)
* Initial documentation on providers
  [#125](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/125)
* 'provider' Identifier relation code list term and associated documentation on provider identifiers
  [#134](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/134)
* Initial Geotab provider
  [#131](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/131)

### Fixed

* System architecture documentation to reflect the current state of the project and project vision to be more realistic
  [#111](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/111)
* Ensuring latest position logic in store selects the most recent position, rather than the last inserted row
  [#121](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/121)

### Changed

* Updating Python dependencies to latest minor/patch versions
  [#115](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/115)
* Refactoring Alembic configuration file into application package
  [#71](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/71)
* Refactoring prototype application to a CLI command
  [#117](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/117)
* Refactoring prototype application to use a provider
  [#127](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/127)
* Refactoring test for CLI command used to run prototype application
  [#129](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/129)
* Replaced placeholder provider with example provider, using faker to generate random assets and positions
  [#130](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/130)
* Updating documentation generally
  [#142](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/142)
* Heading/velocity in asset positions now accepts a Quantity for expressing values in different units
  [#147](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/147)

## [0.1.2] - 2023-01-30

### Added

* Installation documentation for Unix/Linux
  [#106](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/106)

## [0.1.1] - 2023-01-30

### Fixed

* Continuous Deployment job to publish Python package used incorrect `before_script` step
  [#109](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/109)

## [0.1.0] - 2023-01-30

###  Added

* Initial information and data model documentation
* Initial data sources documentation
* Project boilerplate (README, CHANGELOG, LICENSE, etc.)
  [#66](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/66)
* Alembic DB migrations for implementing the Postgres data model
  [#70](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/70)
* Automatically populated inserted/updated Postgres columns
  [#74](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/74)
* Python linting tools (Flake8 and various plugins, Safety)
  [#78](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/78)
* GitLab CI, for tests, linting and verifying package building
  [#78](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/78)
* Python class for Asset, AssetPosition entities
  [#79](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/79)
* Doc blocks, `__repr__` methods, type annotations and flake8 tests
  [#85](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/85)
* Sprint/release retrospective issue template
  [#85](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/85)
* 1st pass of README and other documentation
  [#85](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/85)
* Tests for Alembic migrations
  [#86](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/86)
* Tests information model minimum precision requirements are met by Postgres implementation
  [#92](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/92)
* Database Store class to bridge from SQLAlchemy DB access to main application models
  [#91](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/91)
* Temporary main application to prove assets and asset positions can be written to and from the database
  [#85](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/85)

### Fixed

* Using correct test database when running application tests
  [#87](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/87)
* Using class properties in main models to prevent attributes changes outside init method not being validated
  [#102](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/102)
* Running Alembic CLI commands outside of tests (missing DB engine)
  [#104](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/104)

### Changed

* Poetry config updated based on project changes
  [#70](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/70)
* Technical proposal and system architecture updated to address assumptions made previously
  [#69](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/69)
* Project proposal updated to move field party tracking to a future version
  [#67](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/67)
* Data/information model updated to improve consistency, clarity and fix spelling / bad wording
  [#36](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/36)
* Magic methods in Identifiers class improved (bulk appending items changed to extend)
  [#84](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/84)
* `position.datetime` renamed in Information Model to `position.time` to avoid shadowing clashes
  [#82](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/82)
* Name of linting doit task changed to be more abstract in case tools change
  [#88](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/88)
* Precision for asset positions updated in data/information model to be more realistic
  [#90](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/90)
* Centralising ULID parsing into a utils method
  [#94](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/94)
* Changing approach to loading test and non-test dot-env files for use in `Config` class
  [#103](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/103)
* Pinning SQLAlchemy dependency to < 2.0 release
  [#107](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/107)

### Removed

* Removing asset validity from data/information model until this can be thought through more
  [#36](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/36)
* Cleaning up old experimental files
  [#65](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/65)
