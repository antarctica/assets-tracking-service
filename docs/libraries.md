# BAS Assets Tracking Service - Libraries

Extensions to, or code closely associated with, third-party libraries relied on by this application.

## BAS Esri Utilities

> [!TIP]
> These are rough/working notes that will be written up properly when this module is extracted.

Package: `assets_tracking_service.lib.bas_esri_utils`

A prototype of a library based on the [ArcGIS Python API](https://developers.arcgis.com/python/latest/) for:

- abstracting and simplifying common workflows into high-level methods within ArcGIS Enterprise/Online
- deriving ArcGIS item metadata from BAS discovery metadata (based on ISO 19115 information model)

### Limitations

- group descriptions cannot contain emoji.

### ArcGIS system

Within ArcGIS, items represent information about a resource (file, service, map, application, etc.) related to each
other based on how are they composed (e.g. a service may be used in (and so related to) one or more maps).

Items themselves act as metadata records using an internal information model to represent things such as description,
terms of use, categories, etc.

### Comparison to ISO 19115

From the perspective of ISO 19115, ArcGIS items represent resource formats, meaning a resource described by ISO 19115
may relate to multiple items, depending on its distribution options. By extension, a Catalogue Record and Item (which
are based on the ISO 19115 information model) may relate to multiple ArcGIS Items.

For example a vector dataset may be distributed as an ArcGIS feature layer and vector tile layer, in which case an Item
for that resource would relate to two ArcGIS items.

The relationship between these entities can be summarised as:

```text
[Resource] -> [Record] -> [Item]                  # ISO 19115 model
                            ├── [ArcGIS Item]     # ArcGIS model
                            └── ...
```

An ArcGIS specific `Item` subclass (`assets_tracking_service.lib.bas_esri_utils.models.item.Item`) is used to implement
this hierarchy. It is intended as a lossy, one way, mapping of properties from the ISO 19115 model against the ArcGIS
item model, combined with ArcGIS specific information, such as:

- the ID of the item within ArcGIS (if yet known)
- the item type (distribution format)

For example: a combination of the abstract, lineage and other information are mapped to the ArcGIS `item.description`
property, and so cannot easily be separated later.

When Items from both ArcGIS and the Data Catalogue / ISO 19115 are used, it is suggested to use these aliases:

- `arcgis.gis.Item` as `ArcGisItem`
- `assets_tracking_service.lib.bas_esri_utils.models.item.Item` as `CatalogueItemArcGis`

(The term `Catalogue` in `CatalogueItemArcGis` is not completely accurate in this context, but is clearer as to which
information model it relates as preferred).
