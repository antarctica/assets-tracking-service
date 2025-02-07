# BAS Assets Tracking Service - Deployment

## Python package

The application is distributed as a Python (Pip) package. [Continuous Deployment](#continuous-deployment) will:

- build this package using UV
- upload it to the project [Package Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/packages)

The package can also be built manually if needed:

```
% uv build
```

## Environment module

The application [CLI](../README.md#control-cli) is deployed as a custom environment module on the central workstations.

This module:

- adds the control CLI to the $PATH
- sets [Configuration Options](./config.md)

A separate module version is created for each [Release](../README.md#releases), the latest version will be loaded by
default. Each module version uses a separate Python virtual environment, created from a common Conda environment.

## BAS IT Ansible

An Ansible [Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/assets-tracking-service.yml)
in the BAS IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/) project:

- creates underpinning Conda and Python environments
- generates the [Environment Module](#environment-module)
- runs [Database Migrations](implementation.md#database-migrations) via the control [CLI](../README.md#control-cli)
- configures cron jobs for [Scheduled Tasks](./implementation.md#scheduled-tasks)

This playbook is run automatically via [Continuous Deployment](#continuous-deployment).

## Manual deployment

To manually deploy version 1.2.3 to the staging or production [Environment](./infrastructure.md#environments):

- environment: `staging` / `prod`
- app: `magic/assets-tracking-service`
- additional variables: `app_version=1.2.3`

[General Instructions](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/README.MAGIC.md#run-a-playbook)

## Continuous Deployment

Tagged commits created for [Releases](../README.md#releases) will trigger Continuous Deployment using GitLab's
CI/CD platform configured in [`.gitlab-ci.yml`](../.gitlab-ci.yml).

## Clean prerelease virtual environments

```
% ssh geoweb@bslws01.nerc-bas.ac.uk
$ /data/magic/.conda/envs/python311/bin/python bin/clean-ats-venvs.py
```
