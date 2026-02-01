# Hisense TV MQTT Controller

Kontroller din Hisense Smart TV via den innebygde MQTT brokeren.

## Din TV

| Parameter | Verdi |
|-----------|-------|
| **Navn** | Stue |
| **IP** | `10.0.0.109` |
| **MAC (Ethernet)** | `a0:62:fb:1b:f2:e1` |
| **MAC (WiFi)** | `30:32:35:dc:e9:f8` |
| **transport_protocol** | `2152` |
| **VIDAA Support** | Ja |

## Developer Credentials

Hisense TV-er har en innebygd MQTT broker med følgende tilkoblingsdetaljer:

| Parameter | Verdi |
|-----------|-------|
| **Port** | `36669` |
| **Username** | `hisenseservice` |
| **Password** | `multimqttservice` |
| **Klientsertifikat** | `rcm_certchain_pem.cer` |
| **Klientnøkkel** | `rcm_pem_privkey.pkcs8` |

## Installasjon

```bash
cd Hisense
pip install -r requirements.txt
```

## Bruk

1. Finn IP-adressen til TV-en din (Innstillinger → Nettverk)
2. Rediger `TV_IP` i `hisense_mqtt.py`
3. Kjør scriptet:

```bash
python hisense_mqtt.py
```

## Autentisering

Noen nyere Hisense TV-er krever autentisering:

1. Kjør scriptet og koble til
2. TV-en vil vise en 4-sifret kode
3. Velg "Autentiser" og skriv inn koden
4. Deretter kan du sende kommandoer

## MQTT Topics

### Publish (send til TV)

| Funksjon | Topic |
|----------|-------|
| Hent TV-status | `/remoteapp/tv/ui_service/{CLIENT}/actions/gettvstate` |
| Hent kilder | `/remoteapp/tv/ui_service/{CLIENT}/actions/sourcelist` |
| Hent apper | `/remoteapp/tv/ui_service/{CLIENT}/actions/applist` |
| Hent volum | `/remoteapp/tv/platform_service/{CLIENT}/actions/getvolume` |
| Endre volum | `/remoteapp/tv/platform_service/{CLIENT}/actions/changevolume` |
| Send tastetrykk | `/remoteapp/tv/remote_service/{CLIENT}/actions/sendkey` |
| Start app | `/remoteapp/tv/ui_service/{CLIENT}/actions/launchapp` |
| Bytt kilde | `/remoteapp/tv/ui_service/{CLIENT}/actions/changesource` |
| Autentiser | `/remoteapp/tv/ui_service/{CLIENT}/actions/authenticationcode` |

### Subscribe (motta fra TV)

| Data | Topic |
|------|-------|
| TV-status | `/remoteapp/mobile/broadcast/ui_service/state` |
| Volum | `/remoteapp/mobile/broadcast/ui_service/volume` |
| Kildeliste | `/remoteapp/mobile/{CLIENT}/ui_service/data/sourcelist` |
| Appliste | `/remoteapp/mobile/{CLIENT}/ui_service/data/applist` |

## Tilgjengelige taster

```
KEY_POWER, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
KEY_OK, KEY_BACK, KEY_MENU, KEY_HOME, KEY_EXIT,
KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE,
KEY_PLAY, KEY_PAUSE, KEY_STOP, KEY_FORWARDS, KEY_BACK,
KEY_0 - KEY_9
```

## Start apper

```python
# YouTube
{"name": "YouTube", "urlType": 37, "storeType": 0, "url": "youtube"}

# Netflix
{"name": "Netflix", "urlType": 37, "storeType": 0, "url": "netflix"}

# Amazon Prime Video
{"name": "Amazon", "urlType": 37, "storeType": 0, "url": "amazon"}
```

## Bytt kilde

```python
# TV
{"sourceid": "0", "sourcename": "TV"}

# HDMI 1
{"sourceid": "3", "sourcename": "HDMI 1"}

# HDMI 2
{"sourceid": "4", "sourcename": "HDMI 2"}

# HDMI 3
{"sourceid": "5", "sourcename": "HDMI 3"}

# HDMI 4
{"sourceid": "6", "sourcename": "HDMI 4"}
```

## Testing med mosquitto

Hvis du vil teste manuelt med `mosquitto_sub`/`mosquitto_pub`:

```bash
# Installer mosquitto
brew install mosquitto

# Subscribe til alle topics (med SSL)
mosquitto_sub -h <TV_IP> -p 36669 -u hisenseservice -P multimqttservice \
  --capath /etc/ssl/certs --insecure -t '#' -v

# Hent TV-status
mosquitto_pub -h <TV_IP> -p 36669 -u hisenseservice -P multimqttservice \
  --capath /etc/ssl/certs --insecure \
  -t '/remoteapp/tv/ui_service/Test/actions/gettvstate' -m ''
```

## Wake-on-LAN

TV-en kan ikke slås på via MQTT (den er av). Bruk Wake-on-LAN med TV-ens MAC-adresse:

```bash
# macOS
brew install wakeonlan
wakeonlan AA:BB:CC:DD:EE:FF
```

## Kompatibilitet

Testet med:
- Hisense 65P7
- Hisense 75P7
- Hisense VIDAA U 2.5+

## Referanser

- [mqtt-hisensetv](https://github.com/Krazy998/mqtt-hisensetv)
- [hisensetv Python library](https://github.com/newAM/hisensetv) (arkivert)
