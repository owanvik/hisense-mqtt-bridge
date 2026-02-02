# Hisense TV MQTT Bridge

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Control your Hisense Smart TV from Home Assistant via MQTT.

## Features

- 🔊 Volume control with slider and buttons
- 📺 Source selection (TV, HDMI1-3, AV)
- 🎮 Navigation buttons
- ▶️ Media controls
- ⚡ Power on/off
- 🔄 Auto-reconnect when TV powers on/off

## Installation

### Method 1: Add-on Repository (Recommended)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the three dots menu → **Repositories**
3. Add: `https://github.com/owanvik/hisense-mqtt-bridge`
4. Find "Hisense TV MQTT Bridge" and click **Install**

### Method 2: Local Add-on

1. Copy this folder to `/addons/hisense_mqtt_bridge/` on your HA installation
2. Go to **Settings → Add-ons → Add-on Store**
3. Click the refresh button
4. Find "Hisense TV MQTT Bridge" under **Local add-ons**

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `tv_ip` | IP address of your Hisense TV | *Required* |
| `tv_port` | MQTT port on TV | `36669` |
| `tv_client_id` | Client ID for TV authentication | `HomeAssistant` |
| `mqtt_host` | MQTT broker hostname | `core-mosquitto` |
| `mqtt_port` | MQTT broker port | `1883` |
| `mqtt_username` | MQTT username | *Optional* |
| `mqtt_password` | MQTT password | *Optional* |
| `device_id` | Unique device identifier | `hisense_tv` |
| `device_name` | Friendly name in HA | `Hisense TV` |
| `volume_max` | Maximum volume level | `30` |

## Example Configuration

```yaml
tv_ip: "10.0.0.109"
tv_port: 36669
tv_client_id: "HomeAssistant"
mqtt_host: "core-mosquitto"
mqtt_port: 1883
mqtt_username: ""
mqtt_password: ""
device_id: "hisense_stue"
device_name: "Hisense Stue"
volume_max: 30
```

## Support

- [GitHub Issues](https://github.com/owanvik/hisense-mqtt-bridge/issues)

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
