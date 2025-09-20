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

Assets are tracked using a range of external [Providers](./docs/providers.md). Latest positions are checked every 5
minutes. Providers and individual assets may update less frequently than we check, if they are in storage for example.

## Data access

See the [Assets Tracking Service](https://data.bas.ac.uk/collections/assets-tracking-service) collection in the
BAS Data Catalogue for available datasets. See also the
[Assets Tracking Service](https://www.bas.ac.uk/project/assets-tracking-service) project on the BAS website.

### Permissions

The latest positions of all assets is unrestricted.

Previous positions of most asset types is unrestricted but not currently distributed through this service.

### ArcGIS Online

Data made available through ArcGIS Online (AGOL) is contained in an
[Assets Tracking Service](https://bas.maps.arcgis.com/home/group.html?id=3d7f9fac347e413e8528656dfc3ab325#overview)
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
- the [BAS Embedded Maps Service 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/embedded-maps-service)
  - for easily showing the latest position of an asset as a map in other applications

Data provided by this project is used in projects including:

- the [BAS Field Operations GIS 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/operations/field-operations-gis-data)
- the [BAS Public Website](https://www.bas.ac.uk/)
  - via the Embedded Maps Service

This project was previously known as the [Locations Register 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/locations-register)
and preceded by other implementations. This iteration was initially developed in this
[Experiment 🛡](https://gitlab.data.bas.ac.uk/felnne/pytest-pg-exp).

## Usage

### Control CLI

A control CLI is available on the BAS central workstations:

```
% ssh geoweb@bslws01.nerc-bas.ac.uk
$ module load assets-tracking-service
$ ats-ctl --help
```

See the [CLI Reference](./docs/cli-reference.md) documentation for available commands.

**Note:** You need to be on the BAS network to access these workstations. Contact @felnne if you do not have access to
the `geoweb` user.

### Advanced usage

To load the staging/preview version of the CLI, load the `0.0.0.STAGING` version:

```
$ module load assets-tracking-service/0.0.0.STAGING
```

**Note:** The staging version may not be stable and SHOULD NOT be used for routine tasks.

### Automatic processing

The `data run` [CLI Command](./docs/cli-reference.md#data-commands) is run via cron to keep data current.

Automatic alerts from [Monitoring](./docs/implementation.md#monitoring) tools will be sent if processing fails
repeatedly. Processing logs for the last 24 hours are available from `/users/geoweb/cron_logs/assets-tracking-service/`.

## Data and information model

See [Information](./docs/info-model.md) and [Data](./docs/data-model.md) model documentation.

## Configuration

See [Configuration](./docs/config.md) documentation.

## Implementation

See [Implementation](./docs/implementation.md) documentation.

## Installation and upgrades

See [Installation and Upgrades](./docs/setup) documentation.

## Infrastructure

See [Infrastructure](./docs/infrastructure.md) documentation.

## Development

See [Development](./docs/dev.md) documentation.

## Releases

- [latest release 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/releases/permalink/latest)
- [all releases 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/releases)

### Release workflow

Create a
[release issue 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/new?issue[title]=x.x.x%20release&issuable_template=release) and follow its instructions.

## Deployment

See [Deployment](./docs/deploy.md) documentation.

## Project maintainer

Mapping and Geographic Information Centre ([MAGIC](https://www.bas.ac.uk/teams/magic)), British Antarctic Survey
([BAS](https://www.bas.ac.uk)).

Project lead: [@felnne](https://www.bas.ac.uk/profile/felnne).

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
