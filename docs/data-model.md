# BAS Assets Tracking Service - Data Model

## Overview

This data model implements the abstract [Information Model](./info-model.md) using a relational database, specifically
PostgreSQL and PostGIS as an [Application Database](./implementation.md#database).

[Database Migrations](./implementation.md#database-migrations) represent the normative/authoritative definition of
this model. This documentation is for information only.

## Summary

In general:

- the Asset and Asset Position entities, and Layer and Record meta-entities, are mapped to database tables
- the Labels entity is implemented as a JSONB column (with labels encoded as JSON) within relevant tables
- an additional `nvs_l06_lookup` table is used to support views
- an additional `meta_migration` table is used to track [Database Migrations](./implementation.md#database-migrations)

## Asset

Entity type: *table*

Entity name/reference: `public.asset`

| Property (Abstract) | Property (Database)         | Data Type   | Constraints                                                |
|---------------------|-----------------------------|-------------|------------------------------------------------------------|
| -                   | `pk`                        | INTEGER     | Primary key                                                |
| `id`                | `id`                        | UUID        | Not null, unique                                           |
| `labels`            | `labels`                    | JSONB       | Check (`are_labels_v1_valid`, `are_labels_v1_valid_asset`) |
| -                   | [`created_at`](#created-at) | TIMESTAMPTZ | Not null                                                   |
| -                   | [`updated_at`](#updated-at) | TIMESTAMPTZ | Not null                                                   |

## Asset Position

Entity type: *table*

Entity name/reference: `public.position`

| Property (Abstract) | Property (Database)         | Data Type              | Constraints                                       |
|---------------------|-----------------------------|------------------------|---------------------------------------------------|
| -                   | `pk`                        | INTEGER                | Primary key                                       |
| `id`                | `id`                        | UUID                   | Not null, unique                                  |
| -                   | `asset_id`                  | UUID                   | Not null, Foreign key against (`public.asset.id`) |
| `geom`              | `geom`                      | GEOMETRY(PointZ, 4326) | Not null                                          |
| -                   | `geom_dimensions`           | INTEGER                | Check (value in list `[2, 3]`)                    |
| `time`              | `time_utc`                  | TIMESTAMPZ             | Not null                                          |
| `velocity`          | `velocity_ms`               | FLOAT                  | -                                                 |
| `heading`           | `heading`                   | FLOAT                  | -                                                 |
| `labels`            | `labels`                    | JSONB                  | Check (`are_labels_v1_valid`)                     |
| -                   | [`created_at`](#created-at) | TIMESTAMPTZ            | Not null                                          |
| -                   | [`updated_at`](#updated-at) | TIMESTAMPTZ            | Not null                                          |

### Asset position geometry

`position.geometry` (`AssetPosition.geometry` in the Information Model), is implemented as a PostGIS 3D Point (using
the 4326 SRID).

As PostGIS requires all dimensions (X, Y and Z) to be specified:

- where the Z (elevation) dimension is unknown, a value cannot be omitted or set to null
- a `position.geom_dimensions` column indicates whether the geometry value is a 3D or 2D to overcome this limitation
- values for this column MUST be either `2` or `3`
- for 2D points:
  - the `geom` Z dimension SHOULD be set to `0` to avoid affecting automatically calculated bounding boxes
  - `geom_dimensions` MUST be set to `2`
- this workaround is an implementation detail, the `geom_dimensions` column MUST NOT be exposed to end users

**Note:** Other dimensions (such as 4D points with measure values, etc.) are not supported.

**Note:** With this workaround, the Z value cannot be trusted within Postgres and spatial queries.

## Label

Entity type: *column* in select tables

Entity names/references:

- `public.asset.labels`
- `public.position.labels`

| Property (Abstract) | Property (JSONPath)     | Occurrence  | Data Type                |
|---------------------|-------------------------|-------------|--------------------------|
| -                   | `$`                     | 1           | Object                   |
| -                   | `$.values`              | 1           | Array                    |
| -                   | `$.version`             | 1           | String                   |
| `rel`               | `$.values.*.rel`        | 1           | String                   |
| `scheme`            | `$.values.*.scheme`     | 1           | String                   |
| `scheme_uri`        | `$.values.*.scheme_uri` | 0-1         | String                   |
| `value`             | `$.values.*.value`      | 1           | String, Integer or Float |
| `value_uri`         | `$.values.*.value_uri`  | 0-1         | String                   |
| `creation`          | `$.values.*.creation`   | 1           | Integer                  |
| `expiration`        | `$.values.*.expiration` | 0-1         | Integer                  |

### Labels JSON schema

This schema is for reference only, it is not used as part of [Validation](#labels-validation).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "values": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "rel": {
            "type": "string"
          },
          "scheme": {
            "type": "string"
          },
          "scheme_uri": {
            "type": "string"
          },
          "value": {
            "oneOf": [
              {
                "type": "string"
              },
              {
                "type": "number"
              }
            ]
          },
          "value_uri": {
            "type": "string"
          },
          "creation": {
            "type": "integer"
          },
          "expiration": {
            "type": "integer"
          }
        },
        "required": ["rel", "scheme", "value", "creation"],
        "additionalProperties": false
      }
    },
    "version": {
      "type": "string",
      "enum": ["1"]
    }
  },
  "required": ["values", "version"],
  "additionalProperties": false
}
```

### Labels validation

Custom postgres functions validate labels have the required structure:

- `public.are_labels_v1_valid` is a base function that checks for a wrapper object and values have a scheme and value
- `public.are_labels_v1_valid_assets` additionally checks one label is present using the `skos:prefLabel` scheme

## NVS L06 lookup

Entity type: *table*

Entity name/reference: `public.nvs_l06_lookup`

Provides a key, value (code, label) lookup for use in DB views. It allows a human-readable label to be returned for a
NVS L06 code (e.g. a code of '31' is returned as 'RESEARCH VESSEL').

## Migration

Entity type: *table*

Entity name/reference: `public.meta_migration`

Records the currently applied [Database Migration](./implementation.md#database-migrations), a concept specific to this
data model.

| Property (Abstract) | Property (Database)         | Data Type   | Constraints |
|---------------------|-----------------------------|-------------|-------------|
| -                   | `pk`                        | INTEGER     | Primary key |
| -                   | `migration_id`              | INTEGER     | Not null    |
| -                   | `migration_label`           | TEXT        | Not null    |
| -                   | [`created_at`](#created-at) | TIMESTAMPTZ | Not null    |
| -                   | [`updated_at`](#updated-at) | TIMESTAMPTZ | Not null    |

## Layer

Entity type: *table*

Entity name/reference: `public.layer`

| Property (Abstract) | Property (Database)         | Data Type   | Constraints                                                |
|---------------------|-----------------------------|-------------|------------------------------------------------------------|
| -                   | `pk`                        | INTEGER     | Primary key                                                |
| `slug`              | `slug`                      | TEXT        | Not null, unique                                           |
| `source`            | `source_view`               | TEXT        | Check (`are_labels_v1_valid`, `are_labels_v1_valid_asset`) |
| -                   | `agol_id_geojson`           | TEXT        | -                                                          |
| -                   | `agol_id_feature`           | TEXT        | -                                                          |
| -                   | `agol_id_feature_ogc`       | TEXT        | -                                                          |
| -                   | `data_last_refreshed`       | TIMESTAMPTZ | -                                                          |
| -                   | `metadata_last_refreshed`   | TIMESTAMPTZ | -                                                          |
| -                   | [`created_at`](#created-at) | TIMESTAMPTZ | Not null                                                   |
| -                   | [`updated_at`](#updated-at) | TIMESTAMPTZ | Not null                                                   |

### Layer source view

A reference to a view containing the source data for a layer.

### Layer AGOL IDs

Set when a layer is published to ArcGIS Online, recorded as a ArcGIS item ID for relevant layer types
(GeoJSON, Feature Service, OGC API Features).

### Data last refreshed

Records when data in a layer was last published to a hosting platform, which is assumed to be ArcGIS Online.

### Metadata last refreshed

Records when metadata for a layer was last updated in a hosting platform, which is assumed to be ArcGIS Online.

## Record

Entity type: *table*

Entity name/reference: `public.record`

A subset of the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139) information model.

| Property (Abstract) | Property (Database)         | Data Type   | Constraints                                                |
|---------------------|-----------------------------|-------------|------------------------------------------------------------|
| -                   | `pk`                        | INTEGER     | Primary key                                                |
| -                   | `id`                        | UUID        | Not null, unique                                           |
| -                   | `slug`                      | TEXT        | Not null, unique                                           |
| -                   | `edition`                   | TEXT        | Check (`are_labels_v1_valid`, `are_labels_v1_valid_asset`) |
| -                   | `title`                     | TEXT        | Not null                                                   |
| -                   | `summary`                   | TEXT        | Not null                                                   |
| -                   | `publication`               | TIMESTAMPTZ | Not null                                                   |
| -                   | `released`                  | TIMESTAMPTZ | Not null                                                   |
| -                   | `update_frequency`          | TEXT        | Not null                                                   |
| -                   | `gitlab_issue`              | TEXT        | -                                                          |
| -                   | [`created_at`](#created-at) | TIMESTAMPTZ | Not null                                                   |
| -                   | [`updated_at`](#updated-at) | TIMESTAMPTZ | Not null                                                   |

### Record slug

A value corresponding to the `slug` of a [Layer](#layer) used as a foreign key.

### Record ISO 19115 properties

| Property (Database) | Property (Resource File) | Property (ISO 19115)                                           | Required |
|---------------------|--------------------------|----------------------------------------------------------------|----------|
| `title`             | -                        | `identification.title.value`                                   | Yes      |
| `edition`           | -                        | `identification.edition`                                       | Yes      |
| `summary`           | -                        | `identification.purpose`                                       | Yes      |
| -                   | `abstract.md`            | `identification.abstract`                                      | Yes      |
| `publication`       | -                        | `identification.dates.publication`                             | Yes      |
| `released`          | -                        | `identification.dates.released`                                | Yes      |
| `update_frequency`  | -                        | `identification.maintenance.update_frequency`                  | Yes      |
| `gitlab_issue`      | -                        | `identification.identifiers[namespace='gitlab.data.bas.ac.uk]` | No       |
| -                   | `lineage.md`             | `data_quality.lineage.statement`                               | No       |

Values for `update_frequency` MUST be taken from the ISO 19915
[`MD_MaintenanceFrequencyCode`](https://wiki.esipfed.org/ISO_19115-3_Codelists#MD_MaintenanceFrequencyCode) code list.

Values for `abstract` and `lineage` are stored as Markdown files in a resource directory
(`assets_tracking_service.resources/records/`) for ease of composition.

## Common properties

### Primary keys

For simplicity, standalone `pk` columns using auto-incrementing integer keys are used as primary keys. These keys are
an implementation detail and:

- MUST NOT be exposed to end users
- their values or structure MUST NOT be relied upon

### Created at

`created_at` columns are an implementation detail included for information only. Values:

- MUST NOT be relied upon existing or being correct
- values are set automatically to the current time in UTC when a row is added

### Updated at

`updated_at` columns are an implementation detail included for information only. Values:

- MUST NOT be relied upon existing or being correct
- values are set automatically to the current time in UTC when data in a row is changed via a trigger

## Views

### `v_util_basic`

A view returning minimal information on the latest position for each asset (based on position time).

- selects from `position` joined against `asset` to return asset ID
- returns position ID, time, raw geometry and dimensions count, velocity and heading

Intended as a basic, low level, sanity check of the data model.

Not intended for any particular purpose, or to be used as the basis for other views.

### `v_latest_assets_pos`

A view returning information on the latest position for each asset (based on position time).

- selects from `position` joined against:
  - `asset` to return asset ID
  - `nvs_l06_lookup` to return asset platform type code/label
- returns:
  - position ID, time and 2D geometry
  - lat/lon derived from geometry in DD and DDM formats
  - elevation derived from geometry in metres and feet, if applicable - otherwise `null`
  - velocity in metres/second, kilometres/hour and knots
  - heading in degrees
  - seconds from position time to current_time, time asset was last checked, current_time

Intended as the source of latest position layer.

### `v_latest_assets_pos_geojson`

A view returning results of [`v_latest_asset_pos`](#v_latest_assets_pos) as a GeoJSON feature collection.

Where each row is a feature with a point geometry and identifier based on the position ID.
