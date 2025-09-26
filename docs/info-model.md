# BAS Assets Tracking Service - Information Model

## Background

This model is bespoke to this project rather than using a model from a standard such as SensorML which was considered
unsuitable. Alignments with any standards should be possible through an [Exporter](/docs/implementation.md#exporters).

This information model is abstract and requires a concrete implementation through the [Data Model](/docs/data-model.md).

## Entities

There are 4 entities:

1. **Provider**: automated services that give information on assets and their positions
2. **Asset**: something that has a position (which typically changes but can be static)
3. **Asset Position**: where something was at a point in time (and optionally elevation, speed and bearing/heading)
4. **Label**: annotations for Assets or Asset Positions, such as when the position of an asset was last checked

## Entity relationships

- many-to-many relationship between **Provider** and **Asset** (providers track many assets)
- one-to-many relationship between **Provider** and **Asset Position** (providers give many positions for each asset)
- one-to-many relationship between **Asset** and **Asset Position** (a position relates to a single asset)
- one-to-many relationship between **Asset** and **Label** (an asset has multiple labels)
- one-to-many relationship between **Asset Position** and **Label** (a position has multiple labels)

## Example

- the SDA is an asset (a ship) that is tracked by multiple providers (Geotab and RVDAS)
- the SDA has multiple asset positions as it moves around
- the asset (ship) and it's positions use labels to record, for example, which provider the data is from

From a geospatial perspective:

- an asset position combined with it's related asset information form geospatial features
- multiple positions for the same asset, or positions for multiple assets, form feature collections

## Provider

[Providers](/docs/implementation.md#providers) are services that give access to asset and asset position information.

Providers are not represented directly/separately in this information model but are referenced from [Assets](#asset)
and [Asset Positions](#asset-position) via [Provider Labels](#provider-labels).

### Provider labels

[Assets](#asset) and [Asset Positions](#asset-position) MUST include labels using the 'provider' relation for:

- recording the provider an asset or position came from (i.e. how it was acquired) using the `ats:provider_id` scheme
- recording the version of the provider implementation used, using the `ats:provider_version` scheme

Labels SHOULD also be added using the 'self' relation for:

- the foreign ID for the asset or position assigned by the provider
- original values returned by the provider for position information in their native units (e.g. elevation in feet)

## Asset

Assets are things that have a position (which typically changes but can be static).

| Property | Name   | Occurrence | Data Type         | Data Form | Description       |
|----------|--------|------------|-------------------|-----------|-------------------|
| `id`     | ID     | 1          | String            | -         | Unique Identifier |
| `labels` | Labels | 0-n        | [Labels](#labels) | -         | Annotations       |

### Asset identifiers

Asset IDs:

- MUST uniquely identify an entity
- MUST be stable across the life of an entity (i.e. MUST NOT change)
- MAY use any format/scheme (integers, UUIDs, ULIDs, etc.), non-sequential schemes SHOULD be preferred
- SHOULD use the same scheme consistently all entities
- SHOULD NOT use or relate to identifiers from another, external, system or database (i.e. not a foreign identifier)

### Asset name

Assets MUST contain a [Label](#labels) to record a preferred/common name (e.g. fleet number, registered name, etc.).

This label:

- MUST use [`skos:prefLabel`](https://www.w3.org/2012/09/odrl/semantic/draft/doco/skos_prefLabel.html) as the scheme

### Asset platform type

Assets MUST contain a [Label](#labels) to record a platform type (e.g. ship, airplane, etc.).

This label:

- MUST use [`nvs:l06`](http://vocab.nerc.ac.uk/collection/L06/current/0) as the scheme
- MUST use a value from the [SeaVoX Platform Categories](http://vocab.nerc.ac.uk/collection/L06/current/0) vocabulary
  - where no suitable term (yet) exists, use the '([unknown](http://vocab.nerc.ac.uk/collection/L06/current/0/))' term
  - additional vocabulary terms can be [requested](https://github.com/nvs-vocabs/L06) if needed

### Asset labels

Assets MUST contain labels for:

- when the asset was a last fetched (by any provider):
  - using the `ats:last_fetched` scheme
  - using the current time (in UTC) encoded as a unix timestamp

Assets MAY contain additional [Label](#labels) for:

- identification - distinguishing one asset from another (using a meaningful name, call sign, serial number, etc.)
- characteristics - properties of an asset (such as colour, manufacturer, age, etc.)
- classifications - aligning assets to a taxonomy or policy (such as power level, subject area, etc.)

**Note:** Labels based on characteristics SHOULD be avoided. In general such information SHOULD be held in external
systems, which we SHOULD include a link against using an identifier label.

See also the [Provider Labels](#provider-labels) section.

## Asset Position

Asset positions represent where something was at a point in time (and optionally elevation, speed and bearing/heading).

<!-- pyml disable md013 -->
| Property   | Name     | Occurrence | Data Type         | Data Form                                        | Description         |
|------------|----------|------------|-------------------|--------------------------------------------------|---------------------|
| `id`       | ID       | 1          | String            | -                                                | Unique Identifier   |
| `time`     | Time     | 1          | Date time         | Timezone: *UTC*, Standard: *ISO 8601*            | Temporal position   |
| `geom`     | Geometry | 1          | 2D/3D point       | Projection: *EPSG:4326*, Standard: *ISO 13249-3* | Geographic position |
| `velocity` | Velocity | 0-1        | Float             | Unit: meters per second                          | Speed at position   |
| `heading`  | Heading  | 0-1        | Float             | Unit: degrees                                    | Direction of travel |
| `labels`   | Labels   | 0-n        | [Labels](#labels) | -                                                | Annotations         |
<!-- pyml enable md013 -->

### Asset position units

<!-- pyml disable md013 -->
| Property (Dimension) | Name      | Unit of Measure   | Precision (Minimum) | Min Value                 | Max Value   |
|----------------------|-----------|-------------------|---------------------|---------------------------|-------------|
| `time`               | Time      | Second            | Second              | 0001-01-01T00:00:00+00:00 | [Now (UTC)] |
| `geom` (x)           | Longitude | Decimal degrees   | 7 decimal places    | -180                      | 180         |
| `geom` (y)           | Latitude  | Decimal degrees   | 7 decimal places    | -90                       | 90          |
| `geom` (z)           | Elevation | Metres            | 6 decimal places    | -                         | -           |
| `heading`            | Heading   | Decimal degrees   | 4 decimal places    | 0                         | 360         |
| `velocity`           | Velocity  | Metres per second | 4 decimal places    | -                         | -           |
<!-- pyml enable md013 -->

**Note:** The 'precision (minimum)' column states the precision information model implementations MUST preserve, not a
minimum precision for data values. Data beyond this minimum precision MAY be truncated or generalised and MUST NOT be
relied upon.

### Asset identifier

Asset provider IDs:

- MUST uniquely identify an entity
- MUST be stable across the life of an entity (i.e. MUST NOT change)
- MAY use any format/scheme (integers, UUIDs, ULIDs, etc.), non-sequential schemes SHOULD be preferred
- SHOULD use the same scheme consistently all entities
- SHOULD NOT use or relate to identifiers from another, external, system or database (i.e. not a foreign identifier)

### Asset position time

Asset position times:

- MUST be in the past (future/planned positions are not yet supported)
- MUST be precise to at least the second
- MUST use the UTC timezone
- MUST comply with ISO 8601

**Note:** This minimum _precision_ (1 second) is not the same as a minimum _frequency_. An asset MAY be observed every
4 days providing each observation is precise to at least the second.

### Asset position geometry

Asset position geometries:

- MUST be a point geometry
- MUST use the EPSG:4326 Coordinate Reference System
- MUST use the WGS84 Ellipsoidal datum, if elevation is available
- MAY be 3-dimensional (3D) if elevation is available

### Asset position labels

Assets MAY contain additional [Label](#labels) for:

- data quality information (e.g. values treated as unknown)
- original values from providers (e.g. before units standardisation)

See also the [Provider Labels](#provider-labels) section.

## Labels

Labels record additional information about an entity. Labels are intended to be generic and used across multiple
entities, with some unique, others common.

This concept:

- are essentially key value pairs with additional metadata (such as whether a label currently applies)
- is similar to ISO 19115 keywords
- aligns with and extends the OGC Records
  [`externalIds` property](https://github.com/opengeospatial/ogcapi-records/issues/350) property

### Labels versioning

The definition of labels is versioned to allow changes to their structure and or meaning to be made safely.

The current and supported labels version, that MUST be used, is "1".

### Labels version 1

<!-- pyml disable md013 -->
| Property     | Name       | Occurrence | Data Type                | Data Form                                 | Description                              |
|--------------|------------|------------|--------------------------|-------------------------------------------|------------------------------------------|
| `rel`        | Relation   | 1          | String                   | -                                         | How label relates to entity              |
| `scheme`     | Scheme     | 1          | String                   | -                                         | Label 'key'                              |
| `scheme_uri` | Scheme URI | 0-1        | String                   | URI                                       | URI of a resource for the scheme         |
| `value`      | Value      | 1          | String, Integer or Float | -                                         | Label 'value'                            |
| `value_uri`  | Value URI  | 0-1        | String                   | URI                                       | URI of a resource for the value          |
| `creation`   | Creation   | 1          | Integer                  | Timezone: *UTC*, Format: *Unix timestamp* | Time label was created                   |
| `expiration` | Expiration | 0-1        | Integer                  | Timezone: *UTC*, Format: *Unix timestamp* | Time after which label no longer applies |
<!-- pyml enable md013 -->

#### Label relation

Label relations describe how a label relates to the entity it's attached to.

Label relations:

- MUST be a value from the `assets_tracking_service/models/label.LinkRelations` enum
  - this enum SHOULD be expanded using values from the
    [IANA Link Relations](https://www.iana.org/assignments/link-relations/link-relations.xhtml) registry
  - local values MAY be used if no suitable value applies

Most labels describe things about the entity (e.g. asset) and SHOULD use the 'self' relation.

#### Label schemes

Label schemes:

- SHOULD include a URI if available
- MUST NOT use `ats` as a scheme namespace except for labels that relate to the Assets Tracking Service itself

For consistency, label schemes:

- SHOULD use alphanumeric characters only
- SHOULD use snake case (e.g. `foo_bar`, not `foo-bar`, etc.)
- SHOULD use a `:` as a separator where a namespace applies (e.g. `x:foo_bar` where `x` is the namespace)
- MUST use `ats` as a namespace for labels that relate to the Assets Tracking Service itself (e.g. `ats:foo_bar`)

#### Label values

Label values:

- SHOULD include a URI if available

#### Label creation

The creation date records when a label was first applied to the resource.

Label creation values:

- MUST be the current datetime at the instant the label was created
- MUST use the UTC timezone
- MUST be formatted as a unix timestamp encoded as an integer number

#### Label expiration

Labels will change over time as the entity they relate to changes. Labels that no longer apply SHOULD be marked
as no longer applicable by setting the expiration property (this MAY be in the future).

Label expiration values:

- MUST use the UTC timezone
- MUST be formatted as a unix timestamp encoded as an integer number

## Common properties

### Unique identifiers

Values:

- MUST uniquely identify an entity
- MUST be stable across the life of an entity (i.e. MUST NOT change)
- MAY use any format/scheme (integers, UUIDs, ULIDs, etc.), non-sequential schemes SHOULD be preferred
- SHOULD use the same scheme consistently all entities
- SHOULD NOT use or relate to identifiers from another, external, system or database (i.e. not a foreign identifier)

## Meta entities

These entities enable this application to function. They are not intended to be exposed to end-users.

### Layers

Layers are subsets of Asset and Asset Position entities for a particular use-case.

A layer may filter Assets to a particular type (e.g. aircraft) and/or Asset Positions to a particular time period. See
the [Data Access](/README.md#data-access) for currently available layers.

| Property | Name   | Occurrence | Data Type                         | Data Form | Description                    |
|----------|--------|------------|-----------------------------------|-----------|--------------------------------|
| `slug`   | Slug   | 1          | String                            | -         | Unique Identifier              |
| `source` | Source | 1          | [Data Source](#layer-data-source) | -         | Filtered Asset / Position data |

#### Layer slug

A [Unique Identifier](#unique-identifiers) which can be represented in each all platforms a layer will be implemented
within.

Slugs MUST:

- be URL safe
- be permitted as an identifier in all in each all platforms a layer will be implemented within

Slugs SHOULD:

- be concise
- be human-readable
- be intuitive
- be prefixed with `ats`

#### Layer data source

A reference to the data that forms the layer. E.g. a database view or equivalent concept.

### Records

Records are subsets of discovery metadata records used to describe resources, such as Layers.

Records SHOULD use the [ISO 19115](https://metadata-standards.data.bas.ac.uk/standards/iso-19115-19139) information
model.
