# BAS Assets Tracking Service

Service to track the location of BAS assets, including ships, aircraft, and vehicles.

## Overview

**Note:** This project is focused on needs within the British Antarctic Survey. It has been open-sourced in case parts
are of interest to others. Some resources, indicated with a '🛡' or '🔒' symbol, can only be accessed by BAS staff or
project members respectively. Contact the [Project Maintainer](#project-maintainer) to request access.

## Purpose

A service to collect, standardise, and then make available, the positions of large assets operated by the British
Antarctic Survey. Data collected by this service can be used in other tools and services, such as GIS applications.

See the original
[Project Proposal 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/locations-register/-/blob/5c0610db5d9e6cf3b85143910320154d26722415/docs/planning/project-proposal.md)
for more information.

## Tracked assets

[Assets tracked](./docs/tracked-assets.md) by this service are:

- 🚢 ships (the SDA)
- ✈️ aircraft (the Dash and Twin Otters)
- 🚜 vehicles (snowmobiles, Pisten Bully's, loaders, etc.)

Assets are tracked using a range of external [Providers](./docs/providers.md). Assets, and their latest positions are
fetched from providers every 5 minutes (providers may update less frequently than we check).

## Data access

**Note:** Data is currently restricted. See the [Permissions](#permissions) section for more information.

### Latest asset positions

For the last known position of all assets (optionally filterable by name or platform type):

- [Overview](https://bas.maps.arcgis.com/home/item.html?id=75fda8d96a334d39aa55fa559d1c9e5b)
- [ArcGIS Feature Service 🔒](https://services7.arcgis.com/tPxy1hrFDhJfZ0Mf/arcgis/rest/services/agol_test13/FeatureServer)
- [OGC API - Features 🔒](https://services7.arcgis.com/tPxy1hrFDhJfZ0Mf/arcgis/rest/services/agol_test13/OGCFeatureServer)

**Note:** These endpoints are provisional, with limited metadata and will be replaced. See
[MAGIC/assets-tracking-service#44 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/44).

### Permissions

The latest positions of all assets is unrestricted.

Previous positions of most asset types is unrestricted but not currently distributed through this service.

### ArcGIS Online

Data made available through ArcGIS Online (AGOL) is contained in an
[Assets Tracking Service](https://bas.maps.arcgis.com/home/group.html?id=46d7a701202442c6abc1b47e4958c0fd&view=list#content)
group, including all the services listed above.

### Historic asset locations

This service focuses on current and recent positions of assets. Long term records of the location and activity of BAS
assets, including retired assets, are held in other systems operated by other teams:

- for ships (inc. the JCR, ES, etc.), contact the [UK Polar Data Centre](https://www.bas.ac.uk/data/uk-pdc/)
- for aircraft, contact the [BAS Air Unit](https://www.bas.ac.uk/team/operational-teams/operational-delivery/air-unit/)
- for vehicles, contact the [BAS Vehicles Section](https://www.bas.ac.uk/team/operational-teams/engineering-and-technology/vehicles/)

## Related projects

This project forms part of a wider set of data, services and tools to provide BAS with trustworthy and timely geospatial
information, including:

- the [BAS Operations Data Store 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/ops-data-store)
  - for BAS Operations datasets such as depots and instruments

Data provided by this project is used in projects including:

- the [BAS Field Operations GIS 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/operations/field-operations-gis-data)
- the [BAS Public Website](https://www.bas.ac.uk)

This project was previously known as the [Locations Register 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/locations-register)
and preceded by other implementations. This iteration was initially developed in this
[Experiment 🛡](https://gitlab.data.bas.ac.uk/felnne/pytest-pg-exp).

## Usage

### Control CLI

A control CLI is available on the central workstations using the `geoweb` user:

```
$ ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl --help
```

See the [CLI Reference](./docs/cli-reference.md) documentation for available commands.

**Note:** You need to be on the BAS network to access the workstations. Contact @felnne if you do not have access to
the `geoweb` user.

### Automatic processing

The CLI commands to fetch and export data are automatically ran every 5 minutes to maintain accurate information.

Automatic monitoring will raise alerts with relevant staff if:

- an error occurs when processing data
  - [Sentry Dashboard 🔒](https://antarctica.sentry.io/issues/?project=4507581411229696)
- processing has not run for 15 minutes
  - [Sentry Dashboard 🔒](https://antarctica.sentry.io/crons/assets-tracking-service/ats-run/)

Processing logs for the last 24 hours are available from `/users/geoweb/cron_logs/assets-tracking-service/`.

## Data and information model

See [Information](./docs/info-model.md) and [Data](./docs/data-model.md) model documentation.

## Implementation

See [Implementation](./docs/implementation.md) documentation.

## Installation and upgrades

See [Installation and Upgrades](./docs/install-upgrade.md) documentation.

## Infrastructure

See [Infrastructure](./docs/infrastructure.md) documentation.

## Development

See [Development](./docs/dev.md) documentation.

## Releases

- [latest release 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/releases/permalink/latest)
- [all releases 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/releases)

### Release workflow

Create a [release issue](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/new?issue[title]=x.x.x%20release&issuable_template=release)
and follow the instructions.

GitLab CI/CD will automatically create a GitLab Release based on the tag, including:

- milestone link
- change log extract
- package artefact
- link to README at the relevant tag

GitLab CI/CD will automatically trigger a [Deployment](#deployment) of the new release.

## Deployment

See [Deployment](./docs/deploy.md) documentation.

## Project maintainer

British Antarctic Survey ([BAS](https://www.bas.ac.uk)) Mapping and Geographic Information Centre
([MAGIC](https://www.bas.ac.uk/teams/magic)). Contact [magic@bas.ac.uk](mailto:magic@bas.ac.uk).

The project lead is [@felnne](https://www.bas.ac.uk/profile/felnne).

## Data protection

This project has had a [Data Protection Impact Assessment](./docs/dpia.md).

## Licence

Copyright (c) 2019-2025 UK Research and Innovation (UKRI), British Antarctic Survey (BAS).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
