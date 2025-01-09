# BAS Assets Tracking Service - Infrastructure

## Environments

Available environments:

- *development* - for prototyping and making changes (see [Development](./dev.md) documentation)
- *staging* - for pre-release testing and experimentation
- *production* - for real-world use

Development environments run locally and may be created and destroyed as needed. Staging and Production environments
are long-lived and run centrally (on the BAS workstations, managed by BAS IT as general infrastructure).

## Application servers

- [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=a7uzak2xbbmpwaisjnzanmbqom&h=magic.1password.eu)
  - [Authorised key 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=yz7atvgoxivazyvx2blzcxysbu&h=magic.1password.eu)
  - for running the app as a CLI
  - see [MAGIC/assets-tracking-service#8 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/8) for initial setup

## Databases

- [Staging 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=fqyqeoxzt6vmosuxowqdj7rgoq&h=magic.1password.eu)
  - defunct
  - hosted using Neon
  - for storing initial test data
  - see [MAGIC/assets-tracking-service#8 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/8) for initial setup
- [Staging 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=qmhl6un36h3gxnjzlqtkahgqqy&h=magic.1password.eu)
  - for testing / non-production use
  - see [MAGIC/assets-tracking-service#48 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/48) for initial setup
- [Production 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=qmhl6un36h3gxnjzlqtkahgqqy&h=magic.1password.eu)
  - for testing / non-production use
  - see [MAGIC/assets-tracking-service#48 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/48) for initial setup
  - has a [Read Only](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=64uzvr6vsnfkrdtfv25lsb3jxe&h=magic.1password.eu) user

## 1Password

- [Service Account 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=k34cpwfkqaxp2r56u4aklza6ni&i=4rxxeaa2spr6b5vmykxfucmbu4&h=magic.1password.eu)
  - to allow access to secrets in [Continuous Integration](./dev.md#continuous-integration)
  - see [MAGIC/assets-tracking-service#1 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/1)
    for initial setup

## Sentry

- [Project 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=j2opzqdqbw3m67iem2424psdta&h=magic.1password.eu)
  - for error monitoring
  - see [MAGIC/assets-tracking-service#1 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/assets-tracking-service/-/issues/1)
    for initial setup

## Providers

- [Aircraft Tracking 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=liud3ek4uff2hpqrpanif4ofu4&h=magic.1password.eu)
  - for [Aircraft Tracking](./providers.md#aircraft-tracking) provider
  - see [MAGIC/locations-register#21 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/locations-api/-/issues/21) for initial setup
- [Geotab 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=quma35mabndrdjnbef3cywt46i&h=magic.1password.eu)
  - for [Geotab](./providers.md#geotab) provider

## Exporters

- [ArcGIS 🔒](https://start.1password.com/open/i?a=QSB6V7TUNVEOPPPWR6G7S2ARJ4&v=ffy5l25mjdv577qj6izuk6lo4m&i=6xrlrpt5iteml2lk5ycrn3gucq&h=magic.1password.eu)
  - for [ArcGIS](./exporters.md#arcgis) provider
  - see [MAGIC/esri#84 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/esri/-/issues/84) for initial setup
