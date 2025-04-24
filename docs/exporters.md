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

## Exporter Credentials

See [Infrastructure](./infrastructure.md#exporters) documentation for credentials required by these exporters.

## Available exporters

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

- [Production Group](https://bas.maps.arcgis.com/home/group.html?id=3d7f9fac347e413e8528656dfc3ab325#overview)
- [Staging Group](https://bas-test.maps.arcgis.com/home/group.html?id=abe005474c74419abc7671cdfd7f5d56)

**Note:** This exporter is opinionated as it:

- assumes all Layers are vector (and can/should be published as Feature Layers)
- always creates a set of GeoJSON, Feature Service/Layer and OGC API Features Layer items
- always stores items it creates in a `prj-assets-tracking-service` folder
- always adds items to an `Assets Tracking Service` group, except GeoJSON items (as they are an implementation detail)
- items are shared publicly, except GeoJSON items (which are private as they are an implementation detail)
- ArcGIS item metadata is always set from, and linked with, an associated metadata/catalogue record

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

This exporter creates and maintains metadata records and items in various formats for each
[Layer](./data-model.md#layer) using an associated [Record](./data-model.md#record), and lists these within a
[Collection](#data-catalogue-collection).

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

- [Records](./data-model.md#record) provide static values for properties such as title, abstract, etc.
- [Layers](./data-model.md#layer), managed by the [ArcGIS](#arcgis) exporter, define distribution options ad extents

#### Data Catalogue publishing

Metadata records are exported in a variety of supports to:

- the directory specified by the `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH` config option
- the AWS S3 bucket specified by the `EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET` config option

Exported formats:

- ISO 19115/19139 XML
- ISO 19115/19139 XML with HTML XML stylesheet
- Data Catalogue item HTML page
- Data Catalogue item redirect pages for any configured record aliases

**Note:** This exporter bypasses the main Data Catalogue and publishes directly to the catalogue S3 bucket.

#### Data Catalogue configuration options

Required options:

- `EXPORTER_DATA_CATALOGUE_OUTPUT_PATH`:
  - path to the directory that will contain catalogue files
  - the application will try to create any missing parent directories to this directory if needed
  - e.g. `/data/site`
- `EXPORTER_DATA_CATALOGUE_EMBEDDED_MAPS_ENDPOINT`
  - [BAS Embedded Maps Service](https://github.com/antarctica/embedded-maps) endpoint
  - can/should be omitted to use production endpoint as a default
- `EXPORTER_DATA_CATALOGUE_ITEM_CONTACT_ENDPOINT`
  - action to use for the item contact form
  - should be set the endpoint for Power Automate flow used for processing item messages
- `EXPORTER_DATA_CATALOGUE_AWS_ACCESS_ID`
  - AWS IAM credential to use when interacting with AWS
  - should be a suitably scoped user [1]
- `EXPORTER_DATA_CATALOGUE_AWS_ACCESS_SECRET`
  - AWS IAM credential to use when interacting with AWS
  - should be a suitably scoped user [1]
- `EXPORTER_DATA_CATALOGUE_AWS_S3_BUCKET`
  - AWS S3 bucket to use for publishing content

[1] Example minimal IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "MinimalRuntimePermissions",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::{bucket}",
                "arn:aws:s3:::{bucket}/*"
            ]
        }
    ]
}
```
