# Deepal Unofficial — Home Assistant Integration

An unofficial Home Assistant integration for Deepal electric vehicles, using the Deepal app API.

Currently read only, with no ability to make changes to the car settings or do any actions.

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
- Lock status (the status will reflect your car lock status, but the lock/unlock button will not do anything)
- Vehicle image

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Install "Deepal Unofficial"
3. Restart Home Assistant
4. Go to Settings → Integrations → Add Integration → search for "Deepal"

### Manual

1. Copy the `custom_components/deepal` folder to your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Settings → Integrations → Add Integration → search for "Deepal"

## Setup

This integration requires tokens from the Deepal app. You will need to capture these using a proxy tool such as [mitmproxy](https://mitmproxy.org/) or [HTTP Toolkit](https://httptoolkit.com/).

### Getting your tokens

1. Install and configure a proxy tool on your device
2. Open the Deepal app and log in
3. Capture the login request to `https://m.iov.changanauto.sg/appgw/intl-app-auth/api/login/email-pass-in`
4. From the response, copy the `token` and `refreshToken` values (including the `Bearer ` prefix)

### Configuration

1. Select your country
2. Paste your `token` and `refreshToken`
3. Optionally paste your phone's `deviceId` from the captured request headers — you may need to do this if you're having trouble with HA sharing your phone's session without logging it out. Leave blank to auto-generate a new device ID.
4. Your vehicle will be discovered automatically

## Token refresh

Tokens are automatically refreshed by the integration. They expire after approximately 1 hour but the refresh token is valid for ~90 days.

If your tokens become invalid (e.g. you logged in on another device), a repair notification will appear in HA. Click **Fix** to paste new tokens.

## Notes

- The integration polls the API every 60 seconds by default
- Tyre pressures are retained at their last known value when the car is off (the API returns 0 when the car is parked)
- Credential-based login is not currently supported due to the app using a proprietary encryption scheme

## Disclaimer

This integration is not affiliated with or endorsed by Deepal or Changan Automobile. Use at your own risk.

## Screenshots

<img width="808" height="361" alt="Screenshot 2026-06-08 at 00 35 51" src="https://github.com/user-attachments/assets/29f72b8a-53b3-40cb-aa7f-a52908d81983" />
<img width="512" height="923" alt="Screenshot 2026-06-08 at 00 34 59" src="https://github.com/user-attachments/assets/8f285238-98d4-46ce-88b4-0229740551b9" />

