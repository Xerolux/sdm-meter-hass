# SDM Meter Modbus RTU-over-TCP for Home Assistant

A custom component for Home Assistant to read from Eastron SDM meters (like SDM630) via Modbus RTU over TCP.

## Installation

### HACS
1. Open HACS in Home Assistant.
2. Go to "Integrations" and click the three dots in the top right corner.
3. Select "Custom repositories".
4. Add the URL of this repository and select "Integration" as the category.
5. Search for "SDM Meter" and install it.
6. Restart Home Assistant.

### Manual
1. Copy the `custom_components/sdm_meter` directory to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **SDM Meter**.
3. Enter the IP address, Port, and Slave ID of your Modbus converter.
4. Click **Submit**.

## Supported Entities
This integration supports reading extensive real-time data from SDM meters, including voltages, currents, active and reactive power, power factors, and phase angles for all 3 phases.
