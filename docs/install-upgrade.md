# BAS Assets Tracking Service - Installation and Upgrades

## Requirements

Generic requirements:

- a service or server for running Python command line applications (Python version: 3.11)
- a service or server for hosting Postgres databases (minimum Postgres version: 12, with PostGIS extension)
- a [1Password](https://1password.com) account for storing application secrets and infrastructure details
- a [Sentry](http://sentry.io) account for application [Monitoring](./implementation.md#monitoring)
- requirements for [Providers](./providers.md) and [Exporters](./exporters.md) as needed

Specific requirements:

- access to the BAS central workstations with a shared user and project authorised key
- a dedicated database in the BAS central Postgres server
  - an additional read only user, with delegated permissions for the database owner role to grant select privileges
- a project in the [BAS Sentry 🛡️](http://antarctica.sentry.io) account
- a project in the [BAS GitLab 🛡️](https://gitlab.data.bas.ac.uk) server with:
  - a deployment token configured:
    - name: "Public Access"
    - username: "public-access"
    - scopes: *read_package_registry*
  - an access token configured:
    - name: "gitlab_ci"
    - role: "reporter"
    - scopes: *read_api*
- access to the [MAGIC 1Password 🔒](https://magic.1password.eu/) account with:
  - a service account that can access the *Infrastructure* vault

In addition:

- any requirements listed by [Providers](./providers.md) and [Exporters](./exporters.md)

## Installation

**Note:** These steps are specific to the BAS central workstations running as the `geoweb` user.

### Setup Python environment

```
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load hpc/python/conda3
$ conda init
$ source .bashrc
$ conda create -n assets-tracking-service python=3.11
$ conda activate assets-tracking-service
$ mkdir -p ~/.venv
$ python -m venv ~/.venv/assets-tracking-service
$ conda deactivate
$ module unload hpc/python/conda3
$ source ~/.venv/assets-tracking-service/bin/activate
$ python -m pip install --upgrade pip
$ python -m pip install --no-deps arcgis
$ exit
```

### Perform a manual deployment

Manually perform the steps in the `deploy` [GitLab CD](../.gitlab-ci.yml) job (this process is not well-defined but is
not expected to be performed regularly).

**Note:** Pip may give warnings over incompatible dependencies. These can be ignored.

### Setup app directory

```
$ mkdir -p ~/projects/assets-tracking-service/
```

### Verify installation

```
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl --version
$ ats-ctl config check
$ ats-ctl config show
$ ats-ctl db check
```

### Run database migrations

```
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl db migrate
```

### Setup providers and exporters

Follow any setup instructions for [Providers](./providers.md) and [Exporters](./exporters.md).

### Verify usage

```
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl data fetch
$ ats-ctl data export
```

### Setup Sentry monitoring

Create a Sentry cron monitor within the relevant project and subscription:

- project: *assets-tracking-service*
- name/slug: `ats-run`
- schedule type: *cron*
- cron pattern: `*/5 * * * *`
- cron timezone: *UTC*
- grace period: `2` minutes
- max runtime: `5` minutes
- notify: `#magic`
- failure tolerance: `3`
- recovery tolerance: `1`
- environment: *production*

Once created, edit the monitor's associated alert to set:

- conditions: post message to `#dev` channel in MAGIC Slack (in addition to regular team notification)
- action interval: *5 minutes*
- alert owner: `#magic`

Install the [Sentry CLI](https://docs.sentry.io/product/cli/):

```
$ mkdir ~/bin
$ export INSTALL_DIR=./bin
$ curl -sL https://sentry.io/get-cli/ | sh
```

**Note:** The CLI can also be installed [manually](https://docs.sentry.io/product/cli/installation/#manual-download).

### Setup cron

Create cron script `~/cron_bin/assets_tracking_service`:

```shell
#!/usr/bin/env bash
set -e -u -o pipefail

source /etc/profile.d/modules.sh
export MODULEPATH=/users/geoweb/Modules/modulefiles:$MODULEPATH

module load assets-tracking-service
ats-ctl data fetch
ats-ctl data export
module unload assets-tracking-service
```

Set permissions:

```
$ chmod +x ~/cron_bin/assets_tracking_service
```

Create directory for cron logs:

```
$ mkdir -p ~/cron_logs/ats-run
```

Add crontab entry:

```shell
## Assets Tracking Service automated fetch/export - https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/tree/main#automatic-processing
*/5 * * * SENTRY_DSN=https://57698b6483c7ac43b7c9c905cdb79943@o39753.ingest.us.sentry.io/4507581411229696 /users/geoweb/bin/sentry-cli monitors run -e production ats-run -- /users/geoweb/cron_bin/ats-run >> /users/geoweb/cron_logs/assets-tracking-service/ats-run-$(date +\%Y-\%m-\%d-\%H-\%M-\%S-\%Z).log 2>&1
0 0 * * * /usr/bin/find /users/geoweb/cron_logs/assets-tracking-service -name 'ats-run-*.log' -type f -mtime +0 -delete
```
