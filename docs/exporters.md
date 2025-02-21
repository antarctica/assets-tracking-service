# BAS Assets Tracking Service - Exporters

Exporters are interfaces between the application and clients and tools that use asset location information.

Exporters make data on tracked assets and their positions available to other applications in a format they require.
They isolate and abstract this logic, containing them within a per-exporter [Classes](#exporter-classes).

Some exporters are more generic and used by other, more specific, exporters to avoid repeating work.

## Exporter classes

Exporters inherit from an abstract [Exporter](../src/assets_tracking_service/exporters/base_exporter.py) base class
which defines a public interface. These public methods typically call private methods to:

- select required data
- format it for use
- output and host data in a suitable file format or push directly into other applications

## Selecting data

Exporters MAY use [Database](./implementation.md#database) views to select relevant data.

Exporters MAY depend on the outputs of other exporters (and so require these to be enabled and suitably configured).

## Exporters manager

A central [ExportersManager](../src/assets_tracking_service/exporters/exporters_manager.py) exports data for all
enabled [Exporters](#exporter-classes) using their common public interface.

## Disabling exporters

See the [Configuration](./config.md) documentation for options to disable one or more exporters.

**Note:** An error will occur if an exporter that another (enabled) exporter depends upon is disabled.

## Test exports

A set of [static exports](https://data.bas.ac.uk/items/809c3299-9e0b-4e22-bc77-5d55d3ded917) are available for testing
downstream services, as the [Embedded Maps Service 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/embedded-maps).

Date and time fields in these exports will not update. If testing values relative to the current time, use a library
which can fake the current time to ensure suitable data is available.

## Available exporters

See [Infrastructure](./infrastructure.md#exporters) documentation for exporter credentials.

### GeoJSON

[GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) is a generic exporter that creates an output file of summary
information. Specifically it returns a GeoJSON feature collection containing the latest position for each asset from
the `summary_geojson` view, which is based on the `summary_export` view.

This export is for use by other exporters and is not directly distributed.

#### GeoJSON schema

A feature collection using:

- a 2D geometry (Z values are included as a feature property)
- the position ID as a feature ID

Feature properties are:

- `asset_id`: asset ID (stable, recommended for filtering)
- `position_id`: asset position ID (stable)
- `name`: asset name (unstable, not suitable for filtering)
- `type_code`: asset platform code using [NERC Vocabulary Service L06](http://vocab.nerc.ac.uk/collection/L06/current)
- `type_label`: corresponding label (name) for `type_code`
- `time_utc`: time of last position in UTC
- `last_fetched_utc`: time position was last checked/fetched in UTC
- `lat_dd`: latitude in DD format
- `lon_dd`: longitude in DD format
- `lat_ddm`: latitude in DDM format
- `lon_ddm`: longitude in DDM format
- `elv_m`: elevation (if present) in metres
- `elv_ft`: elevation (if present) in feet
- `speed_ms`: speed (if present) in metres per second
- `speed_kmh`: speed (if present) in kilometres per hour
- `speed_kn`: speed (if present) in knots
- `heading_d`: heading (if present) in decimal degrees

#### GeoJSON example

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "01J2YKWG91HY7BMDN88KEJKCTK",
      "geometry": {
        "type": "Point",
        "coordinates": [
          -3.44832,
          56.023476
        ]
      },
      "properties": {
        "asset_id": "01J2YKVTYV6KCNZZCYRFTCHFVK",
        "position_id": "01J2YKWG91HY7BMDN88KEJKCTK",
        "name": "G20-RRS Sir David Attenborough",
        "type_code": "31",
        "type_label": "RESEARCH VESSEL",
        "time_utc": "2024-07-16T21:30:14+01:00",
        "last_fetched_utc": "2024-07-16T21:31:10+01:00",
        "lat_dd": 56.0234756,
        "lon_dd": -3.44831991,
        "lat_dms": "56\u00b0 1.408536' N",
        "lon_dms": "3\u00b0 26.899195' W",
        "elv_m": null,
        "elv_ft": null,
        "speed_ms": 0.0,
        "speed_kmh": 0.0,
        "speed_kn": 0.0,
        "heading_d": null
      }
    }
  ]
}
```

#### GeoJSON configuration options

Required options:

- `EXPORTER_GEOJSON_OUTPUT_PATH`:
  - path to the file the exporter should create, typically uses the `.geojson` extension
  - the application will try to create any missing parent directories to this file if needed
  - e.g. `/data/exports/output.geojson`

### ArcGIS

[ArcGIS](https://www.arcgis.com/) is a geospatial data hosting, publishing and analysis platform used by BAS. The
ArcGIS exporter creates a
[feature service](https://enterprise.arcgis.com/en/server/latest/publish-services/windows/what-is-a-feature-service-.htm)
containing the latest position for each asset using the output from the [GeoJSON](#geojson) exporter.

This feature service is hosted in the [BAS ArcGIS Online organisation](`https://bas.maps.arcgis.com`) (AGOL) within an
[Assets Tracking Service 🛡️](https://bas.maps.arcgis.com/home/group.html?id=46d7a701202442c6abc1b47e4958c0fd) group.

It is updated by replacing the contents of an uploaded GeoJSON file using the
[ArcGIS API for Python](https://developers.arcgis.com/python/).

#### ArcGIS schema

The geometry and attributes in the feature service schema are the same as those used in [GeoJSON](#geojson-schema)
features except:

- an `ObjectID` attribute is appended
 - this is automatically assigned by ArcGIS and MUST be considered an implementation detail
 - values are not considered stable and SHOULD be ignored

#### ArcGIS permissions

Content is shared publicly.

#### ArcGIS requirements:

Required exporters (MUST be enabled):

- [GeoJSON](#geojson)

Required in the primary [BAS ArcGIS Online organisation](`https://bas.maps.arcgis.com`):

- a user that will publish content:
  - assigned the `creator` user type
  - assigned the at least the `publisher` role
  - this user MUST NOT have multi-factor authentication enabled (to allow non-interactive authentication)
  - this user SHOULD use the conventional `app_automation_bas` shared automation user
- a folder within the publishing user's account:
  - this folder SHOULD be named `assets-tracking-service`
- a group in the primary [BAS ArcGIS Online organisation](`https://bas.maps.arcgis.com`):
  - with shared update enabled
  - this group SHOULD be named `Assets Tracking Service`
  - group members MUST be limited to the subset of [Authorised Users](../README.md#permissions) with AGOL accounts

#### ArcGIS setup

Before it can be updated automatically, the ArcGIS feature service needs to be created and configured.

Prepare data:

- run the [GeoJSON](#geojson) exporter to generate an output
- rename this output to `ats-all-latest.geojson`

Publish data:

- upload the `ats-all-latest.geojson` output to AGOL and publish as a feature service:
  - name the service: `ats_all_latest`
  - name the item for the service `Latest Asset Positions (Assets Tracking Service)`
- from the new feature service:
  - set the access level for the item to be public accessible
  - set basic default visualisation options:
    - popups: set field order as per [GeoJSON Schema](#geojson-schema)
    - fields:
      - `time_utc`, `last_fetched_utc`: set to use 24 hour time with seconds
      - `lat_dd`, `lon_dd`: show to 8 decimal places
      - `heading_d`: show to 1 decimal place

#### ArcGIS configuration options

Required options:

- `EXPORTER_ARCGIS_USERNAME` -> username of publishing user
- `EXPORTER_ARCGIS_PASSWORD` -> password of publishing user
- `EXPORTER_ARCGIS_ITEM_ID` -> ID of the item for the published feature service

### Data Catalogue

The BAS Data Catalogue is a collection of metadata records describing data produced or used by the British Antarctic
Survey or UK Polar Data Centre. This exporter creates a metadata record to describe the layer created by the
[ArcGIS](#arcgis) exporter.

This metadata record is encoded in JSON using the ISO 19115 BAS Metadata Library
[JSON schema](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas) and complies with the
[BAS MAGIC Discovery Profile (v1)](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1).

This record is updated whenever the [ArcGIS](#arcgis) feature service is updated to reflect any changes to the spatial
and/or temporal extent of the data. Other changes to the record description and other properties may be made on an
ad-hoc basis.

Once exported, this record needs to be imported into the BAS Data Catalogue via the relevant
[Workflow](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/workflow-updating-records.md)
outside of this project.

#### Data Catalogue requirements:

Required exporters (MUST be enabled):

- [ArcGIS](#arcgis)

#### Data Catalogue configuration options

Required options:

- `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`:
  - path to the file the exporter should create, using the `.json` extension
  - the application will try to create any missing parent directories to this file if needed
  - e.g. `/data/exports/record.json`
- `EXPORTER_DATA_CATALOGUE_RECORD_ID` -> Record identifier of the metadata record
