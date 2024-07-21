# BAS Assets Tracking Service - Deployment

## Python package

The application is distributed as a Python (Pip) package.

As part of [Continuous Deployment](#continuous-deployment), this package is:

- built using Poetry
- uploaded to the project [Package Registry 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/packages)
- deployed to the [Central Workstations](#bas-central-workstations)

The package can also be built manually if needed:

```
$ poetry build
```

## BAS central workstations

The application is deployed into a Python virtual environment on
[Application Servers](./infrastructure.md#application-servers) using a shared account.

An environment module is generated to:

- expose the application [CLI](./cli-reference.md)
- set [Configuration Options](./config.md)

**Note:** Most configuration options are read from 1Password items. See the
[Continuous Deployment](#continuous-deployment) configuration file for references.

Once deployed, users can [Load](../README.md#control-cli) this module to access the CLI.

## Deployment workflow

Create a
[deployment issue](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/new?issue[title]=x.x.x%20deploy&issuable_template=deploy)
and follow the instructions.

## Continuous Deployment

Tagged commits created for [Releases](../README.md#releases) will trigger Continuous Deployment using GitLab's
CI/CD platform configured in [`.gitlab-ci.yml`](../.gitlab-ci.yml).
