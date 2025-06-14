# BAS Assets Tracking Service - Libraries

Extensions to, or code closely associated with, third-party libraries relied on by this application.

## Markdown

Package: `assets_tracking_service.lib.markdown`

### Markdown plain text plugin

A plugin based on https://github.com/kostyachum/python-markdown-plain-text is used to strip Markdown formatting from
text for use in HTML titles for example.

### Markdown automatic links plugin

A plugin based on ... is used to convert URLs and email addresses in Markdown text into HTML links.

### Markdown list formatting plugin

A plugin based on https://gitlab.com/ayblaq/prependnewline/ is used to automatically add additional line breaks to
correctly paragraphs from lists in Markdown and ensure proper formatting.

## BAS Data Catalogue / Metadata Library

**Note:** These are rough/working notes that will be written up properly when this module is extracted.

Package: `assets_tracking_service.lib.bas_data_catalogue`

Includes classes for:

- Items and Records within the BAS Data Catalogue and Metadata Library respectively
- Exporters for building and publishing a static site including static resources, Items and Records

Also includes tests for Jinja2 templates using BeautifulSoup and Playwright.

These redesigned and refactored classes will replace core parts of the BAS Data Catalogue and Metadata Library projects.

### Items and Records

Terms such as 'item', 'record' and 'resource' are widely used across different data/metadata ecosystems with differing
information models etc. Where context is clear, these terms/classes can and are used directly. Where there's ambiguity,
uses should be suitably scoped for clarity (and to avoid conflicting Python references).

Within the BAS data catalogue / metadata ecosystem:

- *resources* represent datasets, products (maps), service, etc.
- *records* are a low-level representation of a resource using the ISO 19115 information model
- *items* are a high-level representation of a resource, with properties and methods aligned to our specific needs

The relationship between these entities can be summarised as:

```
[Resource] -> [Record] -> [Item]
```

Records are implemented as a data class (`assets_tracking_service.lib.bas_data_catalogue.models.record.Record`) based
on the BAS Metadata Library ISO 19115
[JSON Schema (v4)](https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json).

Items are implemented as subclasses of `Record` based on their intended purpose:

- base item (`assets_tracking_service.lib.bas_data_catalogue.models.item.ItemBase`)
  - an abstract/underpinning class with common properties and methods
- catalogue item (`assets_tracking_service.lib.bas_data_catalogue.models.item.ItemCatalogue`)
  - for use in the Data Catalogue website/frontend

For adding a new Record config element:

1. create a new data class for the new element in the relevant top module (i.e. `identification.py`)
2. define enums for code lists if needed
3. define a cattrs (un)structure hook if needed
4. include the new class as a property in the relevant top-level class (i.e. `Identification`)
5. register the cattrs (un)structure hook in the top-level class hooks if needed
6. add tests for the new class testing all permutations, and cattrs hook if needed
7. amend tests for top-level class (i.e. `TestIdentification`) variant:
	1. add variant for minimal instance of the new class if optional
	2. amend all variants with a minimal instance of the new class if required
	3. amend asserts to check new class as required
	4. amend tests for top-level cattrs hooks if changed
8. if new class part of minimal record, update `fx_lib_record_config_minimal` fixture
9. amend tests for root-level class (i.e. `TestRecord`):
	1. amend tests for root-level cattrs hooks if top-level hooks changed (as an integration check)
	2. amend variants in `test_loop` as needed (include all possible options in complete variant)

### Static site

Structure:

```
├── 404.html
├── favicon.ico
├── -/
│     └── index/
│          └── index.html -> 'hidden' index page
├── collections/
│     ├── foo/
│     │    └── index.html -> redirecting to /items/123/
│     └── .../
│          └── index.html -> redirecting to /items/.../
├── datasets/
│     ├── foo/
│     │    └── index.html -> redirecting to /items/123/
│     └── .../
│          └── index.html -> redirecting to /items/.../
├── legal/
│     ├── cookies/
│     │    └── index.html
│     ├── copyright/
│     │    └── index.html
│     ├── privacy/
│     │    └── index.html
├── maps/
│     ├── foo/
│     │    └── index.html -> redirecting to /items/123/
│     └── .../
│          └── index.html -> redirecting to /items/.../
├── items/
│     ├── 123/
│     │    └── index.html
│     └── .../
│          └── index.html
├── records/
│     ├── 123.html
│     ├── 123.json
│     ├── 123.xml
│     └── ...
└── static/
    ├── css/
    │    └── main.css
    ├── fonts
    │    ├── open-sans-italic.ttf
    │    └── open-sans.ttf
    ├── img
    │    ├── favicon-180.png
    │    ├── favicon-512.png
    │    ├── favicon-mask.png
    │    ├── favicon.ico
    │    ├── favicon.svg
    │    └── safari-pinned-tab.svg
    └── txt
         ├── heartbeat.txt
         └── manifest.webmanifest
```

The `main.css` file is generated using the Tailwind CSS CLI from `main.src.css` and scans classes used in templates.

To install the Tailwind CLI via the `pytailwindcss` package, run:

```
% uv run tailwindcss_install
```

If templates are updated with new classes, run:

```
% uv run python scripts/recreate-css.py
```

The prototype site is published to a separate S3 bucket provisioned via Terraform in `provisioning/terraform/main.tf`:

```
% cd provisioning/terraform/
% docker compose run --rm terraform
% terraform init
% terraform validate
% terraform apply
```

Once provisioned:

- create an access key for the `bas-assets-tracking-app` IAM user
- record credentials and bucket name within 1Password in the *infrastructure* vault
- update `tpl/.env.tpl` with 1Password entry references
- update BAS Ansible provisioning vault with 1Password entry references

### Templates testing

Static content in templates is mostly untested (as it can be verified by viewing the static site).

Dynamic HTML content (Jinja conditionals and loops) is tested using BeautifulSoup and pytest
parameterised tests to verify expected content is rendered (e.g. with and without an optional publication date.)

Dynamic JavaScript content (e.g. feedback widget) is tested using Playwright to verify expected behaviour.

Additional setup for Playwright (after setting up main project):

```
% uv run playwright install
```

To run a specific test file with visible output:

```
% uv run pytest --headed tests/lib_tests/bas_data_catalogue_tests/e2e/test_item_e2e.py
```

## BAS Esri Utilities

**Note:** These are rough/working notes that will be written up properly when this module is extracted.

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

```
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
