A dataset containing the last known position of large assets operated by the British Antarctic Survey
([BAS](https://www.bas.ac.uk)) including:

- 🚢 ships (the [SDA](https://www.bas.ac.uk/polar-operations/sites-and-facilities/facility/rrs-sir-david-attenborough/))
- ✈️ aircraft (the
  [Dash](https://www.bas.ac.uk/polar-operations/sites-and-facilities/facility/dash-7-aircraft/) and
  [Twin Otters](https://www.bas.ac.uk/polar-operations/sites-and-facilities/facility/twin-otter-aircraft/))
- 🚜 vehicles (
  [snowmobiles](https://www.bas.ac.uk/polar-operations/engineering-and-technology/vehicles/sno-cats/),
  [Pisten Bully's](https://www.bas.ac.uk/polar-operations/sites-and-facilities/facility/rothera/tractor-train-traverse-system/),
  loaders, etc.)

This dataset is designed to show where assets are in maps and other visualisations. Attributes (defined below) are
available in a multiple formats to suit different audiences (metres and feet for elevation for example).

Positions (including speed and direction), are checked every 5 minutes, however assets may not be updated as frequently
depending on where they are, or if they are not in use.

Anyone may use this information under the terms of item licence (shown below). It must not be used for safety critical
purpose. Updates to this dataset may pause during system maintenance or for other operational reasons.

Positions are collected, processed and published to this item by the
[BAS Assets Tracking Service](https://github.com/antarctica/assets-tracking-service), operated by the
Mapping and Geographic Information Centre [(MAGIC)](https://data.bas.ac.uk/teams/magic/). Please
[contact us](mailto:magic@bas.ac.uk) for information about this service, or asset position data.

#### Attributes

<details><summary>👉 Click to expand or hide</summary>
<table>
    <tbody>
    <tr>
        <th>Attribute</th>
        <th>Data Type</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    </tbody>
    <tbody>
    <tr>
        <td><code>asset_id</code></td>
        <td>String</td>
        <td>Unique asset identifier</td>
        <td>'01JDRYA6QHCJYYNGZ9TQ813F0G'</td>
    </tr>
    <tr>
        <td><code>position_id</code></td>
        <td>String</td>
        <td>Unique asset position identifier</td>
        <td>'01JDRYAXQVXBEX3CVFG6EH331S'</td>
    </tr>
    <tr>
        <td><code>name</code></td>
        <td>String</td>
        <td>Descriptive asset identifier</td>
        <td>'VP-FBB'</td>
    </tr>
    <tr>
        <td><code>type_code</code></td>
        <td>String</td>
        <td>Code for asset type (see Asset Types)</td>
        <td>'62'</td>
    </tr>
    <tr>
        <td><code>type_label</code></td>
        <td>String</td>
        <td>Label for asset type (see Asset Types)</td>
        <td>'AEROPLANE'</td>
    </tr>
    <tr>
        <td><code>time_utc</code></td>
        <td>Datetime</td>
        <td>When the asset position was recorded</td>
        <td>'2020-06-30T15:20:03Z'</td>
    </tr>
    <tr>
        <td><code>last_fetched_utc</code></td>
        <td>Datetime</td>
        <td>When we last tried to get a position for the asset</td>
        <td>'2020-06-30T23:05:00Z'</td>
    </tr>
    <tr>
        <td><code>lat_dd</code></td>
        <td>Float</td>
        <td>Asset position latitude in decimal degrees</td>
        <td>-67.56915</td>
    </tr>
    <tr>
        <td><code>lon_dd</code></td>
        <td>Float</td>
        <td>Asset position longitude in decimal degrees</td>
        <td>-68.12881</td>
    </tr>
    <tr>
        <td><code>lat_ddm</code></td>
        <td>String</td>
        <td>Asset position latitude in degrees decimal minutes</td>
        <td>67° 34.1486' S</td>
    </tr>
    <tr>
        <td><code>lon_ddm</code></td>
        <td>String</td>
        <td>Asset position longitude in degrees decimal minutes</td>
        <td>68° 7.7282' W</td>
    </tr>
    <tr>
        <td><code>elv_m</code></td>
        <td>Integer</td>
        <td>Asset elevation in metres</td>
        <td>3</td>
    </tr>
    <tr>
        <td><code>elv_ft</code></td>
        <td>Integer</td>
        <td>Asset elevation in feet</td>
        <td>10</td>
    </tr>
    <tr>
        <td><code>speed_ms</code></td>
        <td>Float</td>
        <td>Asset speed in metres per second</td>
        <td>25.0</td>
    </tr>
    <tr>
        <td><code>speed_kmh</code></td>
        <td>Float</td>
        <td>Asset speed in kilometres per hour</td>
        <td>91.0</td>
    </tr>
    <tr>
        <td><code>speed_kn</code></td>
        <td>Float</td>
        <td>Asset speed in knots</td>
        <td>49.0</td>
    </tr>
    <tr>
        <td><code>heading_d</code></td>
        <td>Float</td>
        <td>Asset heading in degrees</td>
        <td>21.0</td>
    </tr>
    </tbody>
</table>
</details>

**Note:** A `FAKE_OBJECTID` attribute is additionally included in Arc services for this dataset for technical reasons.
This attribute must not be used, see the `asset_id` and `position_id` attributes as appropriate instead.

#### Geometry

Point geometry in WGS 84 (EPSG:4326).

#### Asset Types

Asset types use the [SeaVoX Platform Categories](https://vocab.nerc.ac.uk/collection/L06/current/) vocabulary.
