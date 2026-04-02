# SDM Meter (Modbus RTU-over-TCP) for Home Assistant

Custom Home Assistant integration for Eastron SDM power meters via Modbus RTU-over-TCP or Modbus TCP.

## Features
- Config flow setup directly in Home Assistant UI
- Support for 3-phase and 1-phase SDM models
- Polling interval configurable in integration options
- Energy sensors are compatible with the Home Assistant Energy Dashboard
- HACS-ready repository structure
- Diagnostics endpoint for easier troubleshooting

## Supported Models
- `SDM630 / SDM72` (3-phase): full phase-level and aggregate measurements
- `SDM120 / SDM230` (1-phase): automatic filtering of unsupported 3-phase registers

## Installation

### Option 1: HACS (recommended)
1. Open HACS in Home Assistant.
2. Go to `Integrations`.
3. Open the menu in the top-right corner and choose `Custom repositories`.
4. Add this repository URL and choose `Integration` as category.
5. Search for `SDM Meter` and install it.
6. Restart Home Assistant.

### Option 2: Manual installation
1. Copy `custom_components/sdm_meter` to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration
1. Open `Settings -> Devices & Services`.
2. Click `Add Integration` and select `SDM Meter`.
3. Enter Host/IP, Port, Slave ID, Connection Type and Update Interval.
4. Submit the form.

## Polling Recommendations
- Start with `10` seconds for most RS485-to-TCP gateways.
- Use `5` seconds only on stable and fast links.
- Increase to `15-30` seconds if you see timeouts or intermittent unavailable sensors.

## Typical Entities
The integration can expose voltage, current, active/reactive/apparent power, frequency, power factor, phase angle, and multiple energy counters.

## Troubleshooting
- Verify that your converter and meter use the same serial settings (baud rate, parity, stop bits).
- Confirm `Host`, `Port`, and `Slave ID` match your converter/meter setup.
- If no data appears, test with a slower poll interval (for example `10-15` seconds).
- Check Home Assistant logs for `sdm_meter` and `pymodbus` messages.

## Known Limitations
- Some SDM variants expose fewer registers than others; unsupported values are filtered where possible.
- Gateway quality varies: low-cost converters can drop requests under high poll rates.
- Register byte order is currently fixed to big-endian float decoding.

## Development
- Syntax check: `python3 -m compileall custom_components/sdm_meter`
- Tests: `pytest -q -o cache_dir=/tmp/pytest_cache`
- Lint: `ruff check --no-cache custom_components tests`
- Type-check: `mypy custom_components/sdm_meter/flow_helpers.py custom_components/sdm_meter/register_map.py tests`

## License
MIT (see [LICENSE](LICENSE)).
