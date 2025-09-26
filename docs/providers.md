# BAS Assets Tracking Service - Providers

Providers are interfaces between external tracking services and this application.

Providers fetch data on available assets and their positions using per-provider SDKs, APIs and/or other mechanisms.

## Provider clients

Provider clients inherit from an abstract `assets_tracking_service.providers.base_provider.Provider` class which
defines a public interface and general structure/conventions. Clients typically call private, per-provider, methods to
implement this interface.

Providers return [Assets](/docs/info-model.md#asset) and [Asset Positions](/docs/info-model.md#asset-position) from the
[Information Model](/docs/info-model.md) through their corresponding application (Python) model classes.

Providers are versioned (using calendar based versioning) to allow implementation changes to be made safely.

## Provider data conversion

A `assets_tracking_service/units.Conversion` utility class MUST be used to convert position information not using
required [Units](/docs/info-model.md#asset-position-units). Additional conversions SHOULD be added as needed.

## Provider labels

[Provider Clients](#provider-clients) add [Labels](/docs/info-model.md#labels) to record:

- the provider that created each asset or position (using the 'provider' relation and `ats:provider_id` scheme)
- the version of the provider used (using the 'provider' relation and `ats:provider_version` scheme)

In addition, clients add labels to assets for:

- provider specific data such as serial numbers that can [Distinguish](#provider-distinguishing-labels) assets

In addition, clients add labels to positions for:

- original values where data has been [Converted](#provider-data-conversion)
- data quality information such as whether a value should be, or has been, ignored
- provider specific data that can [Distinguish](#provider-distinguishing-labels) positions

> [!NOTE]
> Each client MUST determine the provider values to be captured as labels.

## Provider distinguishing labels

[Provider Clients](#provider-clients) use provider values to determine whether assets or their positions are new or
have changed.

These values will naturally vary provider to provider and are ideally a simple unique ID value. Where this isn't
available, multiple values may need to be combined and/or hashed together as a substitute.

> [!IMPORTANT]
> The public interface for Providers requires the schemes for labels that distinguish assets and positions. This is
> needed by the [Providers Manager](#providers-manager).

## Providers manager

A central `assets_tracking_service/providers/providers_manager.ProvidersManager` fetches assets and providers from all
enabled [Provider Clients](#provider-clients) using their common public interface.

> [!TIP]
> To indicate when assets were last checked, a label with the `ats:last_fetched` scheme is updated.

## Disabling providers

See the [Configuration](/docs/config.md) documentation for options to disable providers.

## Available providers

See [Infrastructure](/docs/infrastructure.md#providers) documentation for provider credentials.

### Aircraft tracking

> [!IMPORTANT]
> The provider used by BAS for aircraft tracking is subject to an NDA and cannot be discussed publicly.
> A private [GitLab project 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sextpqiz6qcqb6icpy4b7un5wq&h=magic.1password.eu)
> provides more information to authorised users.

#### Aircraft tracking configuration options

Required options:

- `PROVIDER_AIRCRAFT_TRACKING_USERNAME`
- `PROVIDER_AIRCRAFT_TRACKING_PASSWORD`
- `PROVIDER_AIRCRAFT_TRACKING_API_KEY`

> [!IMPORTANT]
> Details about these configuration options are restricted. See the private provider project for more information.

### Geotab

[Geotab](https://www.geotab.com/uk/) are a fleet/vehicle management and telematics provider. They supply tracking
hardware that attach to vehicles and report data back to Geotab's cloud over either cellular or Iridium connections.

Reports include position information, engine information, fuel use and other parameters. Over Iridium, reports are sent
every ~15 minutes (unless emergency or crevasse mode is enabled in which data is sent more frequently).

BAS has partnered with Geotab for a number of years, primarily for tracking vehicles used in traverses. It's use has
since expanded to a large number of vehicles, including the SDA.

Geotab provides a Python SDK (`mygeotab`) that wraps around their API. Geotab uses RBAC with a user assigned to MAGIC
for tracking assets. The SDK is used by this app in the `assets_tracking_service.providers.geotab.GeotabProvider` class.

- [SDK Documentation](http://mygeotab-python.readthedocs.io)
- [API Documentation](https://developers.geotab.com/myGeotab/introduction)

#### Geotab configuration options

Required options:

- `PROVIDER_GEOTAB_USERNAME` -> `username` SDK parameter
- `PROVIDER_GEOTAB_PASSWORD` -> `password` SDK parameter
- `PROVIDER_GEOTAB_DATABASE` -> `database` SDK parameter

See the [Geotab Python SDK](https://mygeotab-python.readthedocs.io/en/latest/api.html#mygeotab.api.API.__init__)
documentation for more information on how to configure these values.

### RVDAS

[RVDAS](https://rvdas.org/), the (Open) Research Vessel Data Acquisition System, is used on the RRS Sir David
Attenborough (SDA) to collect data from various sensors including (multiple) GPS and heading feeds.

A 'latest position, heading and depth' database view is made available from this system through an OGC API Features
service. This view is used to populate a single fixed asset representing the SDA in the
`assets_tracking_service.providers.rvdas.RvdasProvider` class.

#### RVDAS configuration options

Required options:

- `PROVIDER_RVDAS_URL`: Items endpoint for the relevant layer within an OGC API Features service
