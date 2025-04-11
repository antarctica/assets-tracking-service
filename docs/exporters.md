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

## Exporter Credentials

See [Infrastructure](./infrastructure.md#exporters) documentation for credentials required by these exporters.

## Available exporters

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

[ArcGIS](https://www.arcgis.com/) is a geospatial data hosting, publishing and analysis platform used by BAS.

The ArcGIS exporter publishes each [Layer](./data-model.md#layer) to [ArcGIS Online](https://www.arcgis.com) using the
[BAS Esri Utilities](./libraries.md#bas-esri-utilities) library as a:

- [Hosted Feature Layer](https://doc.arcgis.com/en/arcgis-online/reference/feature-layers.htm#ESRI_SECTION1_26EBAE21F63042B9A51A4312A08A1B25)
- [OGC API Features](https://enterprise.arcgis.com/en/server/latest/publish-services/linux/ogc-features-service.htm) layer

These are intended for use by end-users and downstream services (such as the
[Embedded Maps Service 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/embedded-maps)).

Feature Layer items are associated with an underlying Feature Service, which for this project are seeded from a
GeoJSON item. Items and services are hosted in an ArcGIS Online subscription for each
[Environment](./infrastructure.md#environments).

A folder within the publishing user's account, and a group within each ArcGIS subscription will be created automatically
to organise content:

- [Production Group]()
- [Staging Group](https://bas-test.maps.arcgis.com/home/group.html?id=abe005474c74419abc7671cdfd7f5d56)

#### ArcGIS schemas

Feature layer's schemas are based on the source view for each [Layer](./data-model.md#layer).

An additional `ObjectID` attribute is automatically included in each schema by ArcGIS. This attribute MUST be
considered an implementation detail and values MUST be hidden from end-users to the extent possible.

**WARNING!** `ObjectID` values MUST NOT be considered stable and MAY change or reused/reassigned without warning.

#### ArcGIS permissions

Content is shared publicly, except for underlying GeoJSON items, as they are implementation detail that should not be
relied upon.

#### ArcGIS requirements

Required exporters (MUST be enabled):

- [Data Catalogue](#data-catalogue)

Within each ArcGIS Online organisation a user for publishing content MUST be provisioned, which:

- MUST be assigned the `creator` user type
- MUST be assigned the `administrator` role (to create restricted groups)
- MUST NOT have multi-factor authentication enabled (to allow non-interactive authentication)
- SHOULD be the conventional `app_automation_bas` / `app_automation_bas_test`  shared automation user

#### ArcGIS configuration options

Required options:

- `EXPORTER_ARCGIS_USERNAME` -> username of publishing user
- `EXPORTER_ARCGIS_PASSWORD` -> password of publishing user
- `EXPORTER_ARCGIS_BASE_ENDPOINT_PORTAL` -> base endpoint for the ArcGIS portal instance
- `EXPORTER_ARCGIS_BASE_ENDPOINT_SERVER` -> base endpoint for the ArcGIS hosting server associated with the portal
- `EXPORTER_ARCGIS_FOLDER_NAME` -> folder exporter will publish content within
- `EXPORTER_ARCGIS_GROUP_INFO` -> information needed to create the group published content will be shared with

The base endpoints are currently assumed to be ArcGIS Online organisations which use the form:

- `https://<org>.maps.arcgis.com`
- `https://services<hive>.arcgis.com/<org>/arcgis/`

See the [Infrastructure](./infrastructure.md#exporters) documentation for values to use for BAS AGOL organisations.

The folder name and group information are hard-coded values and do not need to be set. File references within the
group information are relative to: `src/assets_tracking_service/resources/arcgis_group/`

### Data Catalogue

The BAS Data Catalogue is data discovery tool used to find, evaluate and access datasets, products, services and other
resources produced, managed or used by the British Antarctic Survey and UK Polar Data Centre.

This exporter creates and maintains metadata records for each [Layer](./data-model.md#layer) using an associated
[Record](./data-model.md#record), and lists these within a [Collection](#data-catalogue-collection).

#### Data Catalogue collection

Records are grouped by a collection record representing all outputs from this project.

See the [README](/README.md#data-access) for more information.

#### Metadata record standards

Records created by this exporter use the ISO 19115
[JSON schema](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139#json-schemas), maintained as part of
the BAS Metadata Library.

Records additionally confirm to the
[BAS MAGIC Discovery Profile (v1)](https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1).

#### Metadata record sources

Metadata records combine information from multiple sources:

- [Layers](./data-model.md#layer), managed by the [ArcGIS](#arcgis) exporter, define distribution options ad extents
- [Records](./data-model.md#record) provide static values for properties such as title, abstract, etc.

#### Data Catalogue publishing

Metadata records are exported to a directory specified by the `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH` config option.

Records need to be imported into the BAS Data Catalogue via the relevant
[Workflow](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/docs/workflow-updating-records.md).

#### Data Catalogue setup

After running [Database Migrations](./implementation.md#database-migrations), set the
`EXPORTER_DATA_CATALOGUE_COLLECTION_RECORD_ID` config option to the result of:

```sql
SELECT id from public.record where slug='ats_collection';
```

#### Data Catalogue configuration options

Required options:

- `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`:
  - path to the directory metadata records will be exported to
  - the application will try to create any missing parent directories to this directory if needed
  - e.g. `/data/exports/records`
- `EXPORTER_DATA_CATALOGUE_COLLECTION_RECORD_ID` -> Record identifier for the
  [Collection Record](#data-catalogue-collection), see [Setup](#data-catalogue-setup)
- `EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT`
  - [BAS Embedded Maps Service](https://github.com/antarctica/embedded-maps) endpoint
  - can/should be omitted to use production endpoint as a default
- `EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT`
  - action to use for the item contact form
  - should be set the endpoint for Power Automate flow used for processing item messages
