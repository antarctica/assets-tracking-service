# BAS Assets Tracking Service - Providers

Providers are interfaces between external tracking services and the application.

Providers fetch data on available assets and their positions using per-provider SDKs, APIs or by other means. They
isolate and abstract this logic, containing them within a per-provider [Client](#provider-clients).

## Provider clients

Provider clients inherit from an abstract [Provider](../src/assets_tracking_service/providers/base_provider.py) class
which defines a public interface and general structure/conventions. Clients typically call private, per-provider,
methods to implement this interface.

Providers return [Assets](./info-model.md#asset) and [Asset Positions](./info-model.md#asset-position) from the
[Information Model](./info-model.md) through their corresponding application (Python) model classes.

Providers are versioned (using data based versioning) to allow implementation changes to be made safely.

## Provider data conversion

Position information that does not use the required [Units](./info-model.md#asset-position-units) from the information
model need to be converted.

A [Conversion](../src/assets_tracking_service/units.py) utility class is available to convert between units. Additional
conversion methods can and should be added as needed.

## Provider labels

[Provider Clients](#provider-clients) add [Labels](./info-model.md#labels) to record:

- the provider that created each asset or position (using the 'provider' relation and `ats:provider_id` scheme)
- the version of the provider used (using the 'provider' relation and `ats:provider_version` scheme)

In addition, clients add labels to assets for:

- provider specific data such as serial numbers that can [Distinguish](#provider-distinguishing-labels) assets

In addition, clients add labels to positions for:

- original values where data has been [Converted](#provider-data-conversion)
- data quality information such as whether a value should be, or has been, ignored
- provider specific data that can [Distinguish](#provider-distinguishing-labels) positions

**Note:** It is for each client to determine which values returned by providers should be captured as labels.

## Provider distinguishing labels

[Provider Clients](#provider-clients) need to use values returned by providers to determine whether assets or their
positions are new or have changed.

These values will vary provider to provider. Ideally they are a simple unique ID value. Where not available, another
solution such as hashing multiple values together or using related resources as a proxy.

The public interface for Providers requires the scheme of the labels that contains the distinguishing value for assets
and positions for use by the [Providers Manager](#providers-manager).

## Providers manager

A central [ProvidersManager](../src/assets_tracking_service/providers/providers_manager.py) fetches assets and
providers from all enabled [Provider Clients](#provider-clients) using their common public interface.

To indicate when assets where last checked, a label with the `ats:last_fetched` scheme is updated.

## Disabling providers

See the [Configuration](./config.md) documentation for options to disable one or more providers.

## Available providers

See [Infrastructure](./infrastructure.md#providers) documentation for provider credentials.

### Aircraft tracking

**Note:** The provider used by BAS for aircraft tracking is subject to an NDA and cannot be discussed publicly. A
private [GitLab project 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=sextpqiz6qcqb6icpy4b7un5wq&h=magic.1password.eu)
(which requires specific permission to access) provides more information to authorised users.

#### Aircraft tracking configuration options

Required options:

- `PROVIDER_AIRCRAFT_TRACKING_USERNAME`
- `PROVIDER_AIRCRAFT_TRACKING_PASSWORD`
- `PROVIDER_AIRCRAFT_TRACKING_API_KEY`

**Note:** Details about these configuration options are restricted. If authorised, see the private provider project for
more information.

### Geotab

[Geotab](https://www.geotab.com/uk/) are a fleet/vehicle management and telematics provider. They supply tracking
hardware that attach to vehicles and report data back to Geotab over either cellular or Iridium connections.

Reports include position information, engine information, fuel use and other parameters. Over Iridium, reports are sent
every ~15 minutes (unless emergency or crevasse mode is enabled).

BAS has partnered with Geotab for a number of years, primarily for tracking vehicles used in traverses. It's use has
since expanded to a large number of vehicles, including the SDA.

Geotab provides a Python SDK (`mygeotab`) that wraps around their API. Geotab uses RBAC with a user assigned to MAGIC
for tracking assets. This SDK is used by the app [Geotab Provider](../src/assets_tracking_service/providers/geotab.py).

- [SDK Documentation](http://mygeotab-python.readthedocs.io)
- [API Documentation](https://developers.geotab.com/myGeotab/introduction)

#### Geotab configuration options

Required options:

- `PROVIDER_GEOTAB_USERNAME` -> `username` SDK parameter
- `PROVIDER_GEOTAB_PASSWORD` -> `password` SDK parameter
- `PROVIDER_GEOTAB_DATABASE` -> `database` SDK parameter

See the [Geotab Python SDK](https://mygeotab-python.readthedocs.io/en/latest/api.html#mygeotab.api.API.__init__)
documentation for more information on how to configure these values.
