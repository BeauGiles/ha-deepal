# Archived

Please see **[BeauGiles/ha-deepal-cloud](https://github.com/BeauGiles/ha-deepal-cloud)** instead, with support for email logins, other Deepal models including the S05, and remote actions (eg, changing the target state of charge).

You will need to remove your current Deepal setup in Home Assistant, remove this integration from HACS, and install the new integration above.

## Why move?

This repo was a read-only, single-vehicle (S07) integration that required manually capturing login tokens with a proxy tool (mitmproxy/HTTP Toolkit). The new integration is a full rebase with a much bigger feature set:

- **Native login** — email-code or phone/SMS login through Home Assistant itself. No more proxy tools or manual token capture.
- **Remote control** — lock/unlock doors, open/close windows and the boot, control cabin climate, set charge limit and charging schedule, flash the lights, and honk the horn, all from Home Assistant.
- **Deepal S05 support** — read-only telemetry, alongside full S07 support.
- **Everything this repo had, restored and fixed** — the vehicle image, VIN as the device serial number, and OTA firmware status are all back, plus corrected charge-connection and charging-status logic, and friendly AU/UK entity names throughout (Odometer, Tyre, Boot).

Because entity keys differ between the two integrations, this is a fresh setup rather than an in-place upgrade — see the [new repo's README](https://github.com/BeauGiles/ha-deepal-cloud#readme) and [CHANGELOG](https://github.com/BeauGiles/ha-deepal-cloud/blob/main/CHANGELOG.md) for full details.

## Migration steps

1. In Home Assistant, go to **Settings → Devices & services**, remove the existing **Deepal** integration entry.
2. In **HACS → Integrations**, remove this repository (`BeauGiles/ha-deepal`) as a custom repository.
3. Follow the installation instructions at [BeauGiles/ha-deepal-cloud](https://github.com/BeauGiles/ha-deepal-cloud) to add and configure the new integration.

---

*The original README for this (now archived) integration follows below, for historical reference.*

# Deepal Unofficial — Home Assistant Integration

An unofficial Home Assistant integration for Deepal electric vehicles, using the Deepal app API.

## Supported vehicles

Currently tested on the **Deepal S07**. Other Deepal models may work but are untested.

## Features

- Battery state of charge and estimated range
- Odometer and power status
- Charge status, charge gun connection, charge current, remaining charge time
- Cabin temperature and humidity
- Door and boot open/closed status (binary sensors)
- Tyre pressures with warning status
- HVAC A/C and defrost status
- OTA firmware update status
- Lock status
- Vehicle image

## Setup

This integration required tokens from the Deepal app, captured using a proxy tool such as [mitmproxy](https://mitmproxy.org/) or [HTTP Toolkit](https://httptoolkit.com/). The replacement integration no longer needs this — see the link at the top of this README.

## Disclaimer

This integration is not affiliated with or endorsed by Deepal or Changan Automobile. Use at your own risk.
