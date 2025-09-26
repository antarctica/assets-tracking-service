# BAS Assets Tracking Service - Deployment

## Python package

This application is distributed as a Python (Pip) package.

[Continuous Deployment](#continuous-deployment) will build the package and publish it to the project
[Package Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/packages) automatically.

> [!TIP]
> The package can be built manually by running the `build` [Development Task](/docs/dev.md#development-tasks).

## Environment module

This application is deployed as a custom [Environment Module](https://modules.readthedocs.io) on the BAS central
workstations for running the application [CLI](/README.md#control-cli).

The module:

- adds the control CLI to the `$PATH` from the [Python Package](#python-package) `bin/` directory
- sets [Configuration Options](/docs/config.md)

Separate modules (and corresponding virtual environments) are created for each project [Release](/README.md#releases)
automatically by the [Ansible Playbook](#ansible-playbook).

## Ansible playbook

This application is deployed using an
[Ansible Playbook 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/playbooks/magic/assets-tracking-service.yml)
as part of the BAS IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/) project.

The playbook:

- creates a Python virtual environment containing the [Python Package](#python-package) for the app version
- generates an [Environment Module](#environment-module) for the app version
- runs [Database Migrations](/docs/implementation.md#database-migrations) via the control [CLI](/README.md#control-cli)
- configures cron jobs for [Scheduled Tasks](/docs/implementation.md#scheduled-tasks)

The playbook is run automatically via [Continuous Deployment](#continuous-deployment).

The playbook can be run manually with these
[General Instructions](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/README.MAGIC.md#run-a-playbook)
and context:

- environment: `staging` or `production`
- app: `magic/assets-tracking-service`
- additional variables: `app_version=1.2.3`

## Continuous Deployment

Tagged commits created for [Releases](/README.md#releases) will trigger a continuous deployment workflow for the release
to the production environment using GitLab's CI/CD configured in [`.gitlab-ci.yml`](/.gitlab-ci.yml).

Pre-releases can optionally be deployed to the staging environment by triggering the relevant CI job manually.

## Clean prerelease virtual environments

Deploy:

```text
$ scp resources/scripts/clean-venvs.py geoweb@bslws01.nerc-bas.ac.uk:/users/geoweb/bin/clean-ats-venvs.py
```

Run:

```text
% ssh geoweb@bslws01.nerc-bas.ac.uk
$ /data/magic/.conda/envs/python311/bin/python bin/clean-ats-venvs.py
```
