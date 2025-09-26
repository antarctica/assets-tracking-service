# BAS Assets Tracking Service - Setup

## Requirements

Generic requirements:

- a service or server for running Python command line applications (Python version: 3.11)
- a service or server for hosting Postgres databases (minimum Postgres version: 12, with PostGIS extension)
- a [1Password](https://1password.com) account for storing application secrets and infrastructure details
- a [Sentry](http://sentry.io) account for application [Monitoring](/docs/implementation.md#monitoring)
- a GitLab access token for accessing restricted packages during deployment
- requirements for [Providers](/docs/providers.md) and [Exporters](/docs/exporters.md) as needed
- an application in the BAS IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible) project

Specific requirements:

- access to the BAS central workstations with a shared user and project authorised key
- a dedicated database and database owner role in the BAS central Postgres server with:
  - the PostGIS extension enabled, or delegated permissions for the database owner role to enable extensions
  - an additional read only user, with delegated permissions for the database owner role to grant select privileges
- a project in the [BAS Sentry 🛡️](http://antarctica.sentry.io) account
- a project in the [BAS GitLab 🛡️](https://gitlab.data.bas.ac.uk) server with anonymous access to packages:
  - Settings -> General -> Visibility, project features, permissions -> Package registry
  - Allow anyone to pull from Package Registry: *Enabled*
- an access token for the private [Aircraft Tracking Provider project 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sextpqiz6qcqb6icpy4b7un5wq&h=magic.1password.eu):
  - Settings -> Access Tokens
  - name: `ansible`
  - role: *reporter*
  - scopes: *read_api*
  - credential stored in the *Infrastructure* vault in 1Password linked to in [Infrastructure](/docs/infrastructure.md)
- access to the [MAGIC 1Password 🔒](https://magic.1password.eu/) account with:
  - a service account that can access the *Infrastructure* vault

In addition:

- any requirements listed in the GitLab CI/CD configuration (`.gitlab-ci.yml`)
- any requirements listed by [Providers](/docs/providers.md) and [Exporters](/docs/exporters.md)

## Installation

### Perform a manual deployment

As per the [Manual Deployment](/docs/deploy.md#ansible-playbook) instructions.

This will automatically run [Database Migrations](/docs/implementation.md#database-migrations) and configure cron jobs
for [Scheduled Tasks](/docs/implementation.md#scheduled-tasks).

### Setup providers and exporters

Follow any setup instructions for [Providers](/docs/providers.md) and [Exporters](/docs/exporters.md).

### Verify usage

```text
% ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl data run
```

> [!NOTE]
> This will send a check-in to the [Sentry Monitor](/docs/implementation.md#scheduled-tasks). The monitor will be
> created automatically if needed.

### Setup Sentry monitoring

If needed, configuring alerts for the Sentry monitor from the Sentry dashboard:

- notify: `#magic`
- conditions: post message to `#dev` channel in the MAGIC Teams workspace (in addition to email notification)
- action interval: *5 minutes*
- alert owner: `#magic`
