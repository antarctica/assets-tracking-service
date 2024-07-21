# BAS Assets Tracking Service - Implementation

## Architecture

## Overview

At a high level, the major components of this project are:

- *assets*: things that have a position (which typically changes but can be static)
- *tracking services*: services that collect asset positions and return them to clients
- *end users*: individuals that want to know the position of one or more assets

End users may access position information through a combination of:

- primary (upstream) tracking services (i.e. that receive data from the GPS device tracking an asset)
- this service, via one of it's exports
- another (downstream) tracking service (either downstream of this service, or of another service)

Assuming an end user is accessing data (in)directly from this service, this data flow can be represented as:

![high](./img/architecture-high.png)

Where:
- a primary tracking service receives data from an asset
- the data is acquired from the primary tracking service by this application
- the data is accessed from this application by an end-user, or by another tracking service (and in turn by end-users)

## Components

At a lower level than the [Overview](#overview), the components used in this project can be broken down into:

- *assets*: things that have a position (which typically changes but can be static)
- *tracking services (primary)*: services that collect asset positions and return them to clients
- [*Providers*](#providers): interfaces between primary tracking services and this application
- [*Database*](#database): store of acquired asset and position information
- [*Exporters*](#exporters): interfaces between this application and an access service
- *access services*: services that allow access to data through a protocol and format (e.g. an OGC Features API)
- *access clients*: tools that allow end users to view and analyse data from an access service (e.g. QGIS)
- *end users*: individuals that want to know the position of one or more assets
- *tracking services (secondary)*: services that collect asset positions from this service for use by end users

This data flow can be represented as:

![low](./img/architecture-low.png)

Where:
- a primary tracking service receives data from an asset
- the data is acquired from the primary tracking service via an application [Provider](#providers)
- the data is stored in the application [Database](#database)
- the data is pushed into access services via an application [Exporter](#exporters)
- the data is accessed by end users using a tool or service, either:
  - directly from this service through an access service
  - indirectly from another tracking service that has acquired data from an access service

**Note:** Providers pull (poll) data from the tracking service. Services that emit events are not currently supported.

## Providers

Providers are interfaces between external tracking services and the application.

See [Providers](./providers.md) documentation for more information and available providers.

See [Infrastructure](./infrastructure.md#providers) documentation for provider credentials.

### Restricted providers

Some providers are restricted, in that they cannot be open sourced. Such providers are contained in separate Python
packages and included as private dependencies from authenticated private Pip indexes.

## Exporters

Exporters are interfaces between the application and services that allow clients and tools that use asset location
information (access services).

See [Exporters](./exporters.md) documentation for more information and available providers.

See [Infrastructure](./infrastructure.md#exporters) documentation for exporter credentials.

## Command line interface

[Typer](https://typer.tiangolo.com/), which builds upon [Click](https://click.palletsprojects.com) is used as the
framework for the [Control CLI](./cli-reference.md).

## Scheduled running

Cron is used to call relevant [CLI](#command-line-interface) commands every 5 minutes.

## Configuration

See [Configuration](./config.md) documentation.

## Database

[PostgreSQL](https://www.postgresql.org) with the [PostGIS](https://postgis.net) geospatial extension is used for
persisting information.

A number of custom functions are used for:

- working with [ULIDs](https://github.com/ulid/spec)
- formatting coordinates in the DDM form
- validating [Labels](./data-model.md#labels-validation)
- setting 'updated_at' values

These functions, and entities to implement the application [Data Model](./data-model.md), are defined in
[Database Migrations](#database-migrations).

### Database client

A basic [psycopg3](https://www.psycopg.org/psycopg3/) based [Database Client](../src/assets_tracking_service/db.py) is
used as an interface between the application and the database.

**Note:** This database client runs a `set timezone to 'UTC'` to ensure all data is returned in the correct timezone.
`
### Database migrations

A basic database migrations implementation is used to manage objects within the application [Database](#database).

Migrations are SQL files defined in [`resources/db_migrations`](../src/assets_tracking_service/resources/db_migrations)
executed by the application [Database Client](#database-client) through the application [CLI](#command-line-interface).

Migrations should be defined in both a forward (create, apply change) and reverse (destroy, revert change) direction
by creating an *up* and *down* migration file.

All migrations are intended to be executed to their full extent - i.e. migrated fully up to the latest set of changes,
or fully down to the base, empty, state. Branching or migrating to points other than the head and base is not supported.

See the [Developing](./dev.md#adding-database-migrations) documentation for how to add a new migration.

### Database permissions

Database access is restricted to a role representing the application, which owns the database.

Direct database access by other users, tools and clients is not supported, except via an [Exporter](#exporters).

## Monitoring

Log messages to *info* level are written to `stderr`.

[Sentry](https://sentry.io) monitors:

- runtime errors
- where cron instances fail or not observed as running for 15 minutes

Alerts are sent via email and to the `#dev` channel in the MAGIC Slack workspace.
