# BAS Assets Tracking Service - Deployment

## Python package

The application is distributed as a Python (Pip) package. [Continuous Deployment](#continuous-deployment) will:

- build this package using Poetry
- upload it to the project [Package Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/packages)
- deploy it the [Application Servers](./infrastructure.md#application-servers)

The package can also be built manually if needed:

```
$ poetry build
```

## Environment module

An environment module is used to access the application [CLI](../README.md#control-cli). This module:

- adds the CLI to the $PATH
- sets [Configuration Options](./config.md)

[Continuous Deployment](#continuous-deployment) will generate the module file, typically reading configuration option
values from 1Password items.

## Continuous Deployment

Tagged commits created for [Releases](../README.md#releases) will trigger Continuous Deployment using GitLab's
CI/CD platform configured in [`.gitlab-ci.yml`](../.gitlab-ci.yml).

This includes:

- installing/upgrading the [Python Package](#python-package)
- generating the [Environment Module](#environment-module)
- running [Database Migrations](./implementation.md#database-migrations)
- ...
