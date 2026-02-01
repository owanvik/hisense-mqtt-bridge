# Hisense TV MQTT Bridge for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Control your Hisense Smart TV from Home Assistant via MQTT Discovery.

## Features

- 🔊 **Volume Control** - Slider, up/down buttons, and mute
- 📺 **Source Selection** - Switch between TV, HDMI1-3, AV
- 🎮 **Navigation** - Up, Down, Left, Right, OK, Back, Home, Menu
- ▶️ **Media Controls** - Play, Pause, Stop, Rewind, Fast Forward
- ⚡ **Power Control** - Turn TV on/off
- 🔄 **Real-time Sync** - Volume and source changes from physical remote are reflected in HA

## Requirements

- Hisense Smart TV with RemoteNOW/VIDAA support
- Home Assistant with MQTT broker (Mosquitto recommended)
- Python 3.8+

**Note:** SSL certificates are embedded in the script - no manual extraction needed!

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/YOUR_USERNAME/hisense-mqtt-bridge` as an **Integration**
4. Search for "Hisense TV MQTT Bridge" and install

### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/hisense-mqtt-bridge.git
cd hisense-mqtt-bridge

# Install dependencies
pip install -r requirements.txt
Run the setup wizard
python3 hisense_bridge.py --setupxample config.yaml
nano config.yaml
```

## Configuration

Edit `config.yaml` with your settings:
Run the interactive setup wizard:

```bash
python3 hisense_bridge.py --setup
```

Or manually create `config.yaml`
```yaml
# TV Connection
tv:
  ip: "192.168.1.100"      # Your TV's IP address
  port: 36669              # Default MQTT port
  client_id: "HomeAssistant"

# Home Assistant MQTT
mqtt:
  host: "192.168.1.50"     # HA/MQTT broker IP
  port: 1883
  username: "mqtt_user"
  password: "mqtt_password"

# Device Settings
device:
  id: "hisense_living_room"
  name: "Hisense Living Room"
  topic_prefix: "hisense/living_room"

# Volume
volume:
  max: 30
  step: 1
```

## Usage

### Running Manually

```bash
python3 hisense_bridge.py
```

### Running as a Service (Recommended)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/hisense-bridge.service
```

```ini
[Unit]
Description=Hisense TV MQTT Bridge
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/hisense-mqtt-bridge
ExecStart=/usr/bin/python3 hisense_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable hisense-bridge
sudo systemctl start hisense-bridge
```

### Running with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "hisense_bridge.py"]
```

```bash
docker build -t hisense-bridge .
docker run -d --name hisense-bridge \
  -v /path/to/config.yaml:/app/config.yaml \
  -v /path/to/certs:/app/certs \
  hisense-bridge
```

## Home Assistant Entities

After starting the bridge, the following entities will appear in Home Assistant:

| Entity | Type | Description |
|--------|------|-------------|
| `select.hisense_tv_source` | Select | Input source selector |
| `number.hisense_tv_volume` | Number | Volume slider (0-30) |
| `button.hisense_tv_volume_up` | Button | Increase volume |
| `button.hisense_tv_volume_down` | Button | Decrease volume |
| `button.hisense_tv_mute` | Button | Toggle mute |
| `button.hisense_tv_power` | Button | Toggle power |
| `button.hisense_tv_up/down/left/right` | Button | Navigation |
| `button.hisense_tv_ok/back/home/menu` | Button | Navigation |
| `button.hisense_tv_play/pause/stop` | Button | Media controls |
| `button.hisense_tv_rewind/fastforward` | Button | Media controls |

## Lovelace Card Example

Create a custom card for easy TV control:

```yaml
type: entities
title: Hisense TV
entities:
  - entity: select.hisense_tv_source
  - entity: number.hisense_tv_volume
  - entity: button.hisense_tv_volume_up
  - entity: button.hisense_tv_volume_down
  - entity: button.hisense_tv_mute
  - entity: button.hisense_tv_power
  - type: divider
  - entity: button.hisense_tv_up
  - entity: button.hisense_tv_down
  - entity: button.hisense_tv_left
  - entity: button.hisense_tv_right
  - entity: button.hisense_tv_ok
```

## Troubleshooting

### Can't connect to TV

- Ensure your TV is on the same network
- Check that port 36669 is not blocked by firewall
- Verify the TV IP address is correct
- Make sure certificates are valid

### Volume commands not working

- Some Hisense TVs require specific volume command formats
- The bridge uses plain number strings (e.g., `"15"`) which works on most models

### Entities not appearing in HA

- Check MQTT broker connection
- Verify MQTT Discovery is enabled in HA
- Check Home Assistant logs for errors

### Debug Mode

Run with debug logging:

```bash
python3 hisense_bridge.py --debug
```

## Contributing

Contributions are welcome! Please open an issue or pull request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- Inspired by [hiern/HiSense-MQTT](https://github.com/Krazy998/HiSense-MQTT)
- Built for the Home Assistant community
