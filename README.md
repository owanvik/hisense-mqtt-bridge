# Hisense TV MQTT Bridge for Home Assistant

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fowanvik%2Fhisense-mqtt-bridge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Control your Hisense Smart TV via the built-in MQTT broker.

## 🏠 Home Assistant Add-on

Click the button above to install the add-on directly in Home Assistant!

**Features:**
- 🔊 Volume control (slider + buttons)
- 📺 Source selection (TV, HDMI1-3, AV)
- 🎮 Navigation buttons
- ▶️ Media controls (Play, Pause, Stop)
- ⚡ Power on/off
- 🔁 Auto-reconnect when TV powers on/off
- 🔄 Real-time sync with physical remote

## Requirements

- Hisense Smart TV with RemoteNOW/VIDAA support
- Home Assistant with Mosquitto MQTT broker add-on
- Home Assistant Supervisor (for add-on installation)

**Note:** SSL certificates are embedded - no manual extraction needed!

## Installation

1. Click the **Add to Home Assistant** button above, or:
2. Go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
3. Add: `https://github.com/owanvik/hisense-mqtt-bridge`
4. Click **Add** and refresh
5. Find **Hisense TV MQTT Bridge** and click **Install**
6. Configure your TV IP and MQTT credentials
7. **Start** the add-on

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `tv_ip` | IP address of your Hisense TV | *Required* |
| `tv_port` | MQTT port on TV | `36669` |
| `mqtt_host` | MQTT broker hostname | `core-mosquitto` |
| `mqtt_username` | MQTT username | *Optional* |
| `mqtt_password` | MQTT password | *Optional* |
| `device_name` | Friendly name in HA | `Hisense TV` |
| `volume_max` | Maximum volume level | `30` |

## TV Credentials

Hisense TVs have a built-in MQTT broker with these connection details:

| Parameter | Value |
|-----------|-------|
| **Port** | `36669` |
| **Username** | `hisenseservice` |
| **Password** | `multimqttservice` |
| **Client Certificate** | `rcm_certchain_pem.cer` |
| **Client Key** | `rcm_pem_privkey.pkcs8` |

## MQTT Topics

### Publish (send to TV)

| Function | Topic |
|----------|-------|
| Get TV state | `/remoteapp/tv/ui_service/{CLIENT}/actions/gettvstate` |
| Get sources | `/remoteapp/tv/ui_service/{CLIENT}/actions/sourcelist` |
| Get apps | `/remoteapp/tv/ui_service/{CLIENT}/actions/applist` |
| Get volume | `/remoteapp/tv/platform_service/{CLIENT}/actions/getvolume` |
| Change volume | `/remoteapp/tv/platform_service/{CLIENT}/actions/changevolume` |
| Send key | `/remoteapp/tv/remote_service/{CLIENT}/actions/sendkey` |
| Launch app | `/remoteapp/tv/ui_service/{CLIENT}/actions/launchapp` |
| Change source | `/remoteapp/tv/ui_service/{CLIENT}/actions/changesource` |
| Authenticate | `/remoteapp/tv/ui_service/{CLIENT}/actions/authenticationcode` |

### Subscribe (receive from TV)

| Data | Topic |
|------|-------|
| TV state | `/remoteapp/mobile/broadcast/ui_service/state` |
| Volume | `/remoteapp/mobile/broadcast/ui_service/volume` |
| Source list | `/remoteapp/mobile/{CLIENT}/ui_service/data/sourcelist` |
| App list | `/remoteapp/mobile/{CLIENT}/ui_service/data/applist` |

## Available Keys

```
KEY_POWER, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
KEY_OK, KEY_BACK, KEY_MENU, KEY_HOME, KEY_EXIT,
KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE,
KEY_PLAY, KEY_PAUSE, KEY_STOP, KEY_FORWARDS, KEY_BACK,
KEY_0 - KEY_9
```

## Launch Apps

```python
# YouTube
{"name": "YouTube", "urlType": 37, "storeType": 0, "url": "youtube"}

# Netflix
{"name": "Netflix", "urlType": 37, "storeType": 0, "url": "netflix"}

# Amazon Prime Video
{"name": "Amazon", "urlType": 37, "storeType": 0, "url": "amazon"}
```

## Change Source

```python
# TV
{"sourceid": "0", "sourcename": "TV"}

# HDMI 1-4
{"sourceid": "3", "sourcename": "HDMI 1"}
{"sourceid": "4", "sourcename": "HDMI 2"}
{"sourceid": "5", "sourcename": "HDMI 3"}
{"sourceid": "6", "sourcename": "HDMI 4"}
```

## Testing with mosquitto

```bash
# Install mosquitto
brew install mosquitto  # macOS
apt install mosquitto-clients  # Linux

# Subscribe to all topics (with SSL)
mosquitto_sub -h <TV_IP> -p 36669 -u hisenseservice -P multimqttservice \
  --capath /etc/ssl/certs --insecure -t '#' -v

# Get TV status
mosquitto_pub -h <TV_IP> -p 36669 -u hisenseservice -P multimqttservice \
  --capath /etc/ssl/certs --insecure \
  -t '/remoteapp/tv/ui_service/Test/actions/gettvstate' -m ''
```

## Wake-on-LAN

The TV cannot be turned on via MQTT (it's off). Use Wake-on-LAN with the TV's MAC address:

```bash
# macOS
brew install wakeonlan
wakeonlan AA:BB:CC:DD:EE:FF
```

## Compatibility

Tested with:
- Hisense 65P7
- Hisense 75P7
- Hisense VIDAA U 2.5+

## References

- [mqtt-hisensetv](https://github.com/Krazy998/mqtt-hisensetv)
- [hisensetv Python library](https://github.com/newAM/hisensetv) (archived)
- [Hisense MQTT Key Files](https://github.com/d3nd3/Hisense-mqtt-keyfiles)

## License

MIT License - see [LICENSE](LICENSE) for details.
