#!/usr/bin/env python3
"""Hisense TV Bridge for Home Assistant - Full kontroll!"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

# === KONFIGURASJON ===
TV_IP = "10.0.0.109"
TV_PORT = 36669
TV_CLIENT_ID = "HomeAssistant"

HA_MQTT_HOST = "10.0.0.50"
HA_MQTT_PORT = 1883
HA_MQTT_USER = "hisense"
HA_MQTT_PASS = "hisense"

VOLUME_MAX = 30
VOLUME_STEP = 1

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

# === KNAPPER ===
# Volum
VOLUME_BUTTONS = [
    ("volume_up", "Volum Opp", "mdi:volume-plus"),
    ("volume_down", "Volum Ned", "mdi:volume-minus"),
    ("mute", "Mute", "mdi:volume-mute"),
]

# Navigasjon
NAV_BUTTONS = [
    ("up", "Opp", "mdi:arrow-up", "KEY_UP"),
    ("down", "Ned", "mdi:arrow-down", "KEY_DOWN"),
    ("left", "Venstre", "mdi:arrow-left", "KEY_LEFT"),
    ("right", "Høyre", "mdi:arrow-right", "KEY_RIGHT"),
    ("ok", "OK", "mdi:check-circle", "KEY_OK"),
    ("back", "Tilbake", "mdi:arrow-left-circle", "KEY_BACK"),
    ("home", "Hjem", "mdi:home", "KEY_HOME"),
    ("menu", "Meny", "mdi:menu", "KEY_MENU"),
]

# Power
POWER_BUTTONS = [
    ("power", "Power", "mdi:power", "KEY_POWER"),
]

# Media
MEDIA_BUTTONS = [
    ("play", "Play", "mdi:play", "KEY_PLAY"),
    ("pause", "Pause", "mdi:pause", "KEY_PAUSE"),
    ("stop", "Stop", "mdi:stop", "KEY_STOP"),
    ("rewind", "Spol tilbake", "mdi:rewind", "KEY_REWIND"),
    ("fastforward", "Spol fremover", "mdi:fast-forward", "KEY_FASTFORWARD"),
]

# Apper (kommentert ut - aktiver ved behov)
# APP_BUTTONS = [
#     ("netflix", "Netflix", "mdi:netflix", "Netflix"),
#     ("youtube", "YouTube", "mdi:youtube", "YouTube"),
#     ("disney", "Disney+", "mdi:filmstrip", "Disney+"),
#     ("prime", "Prime Video", "mdi:amazon", "Prime Video"),
# ]

# === STATE ===
current_volume = 0
is_muted = False
current_source = None
tv_client = None
ha_client = None
app_list = {}

def tv_topic(service, action):
    return f"/remoteapp/tv/{service}/{TV_CLIENT_ID}/actions/{action}"

# === TV CALLBACKS ===
def on_tv_connect(client, userdata, flags, rc, props=None):
    print("✅ Tilkoblet TV")
    client.subscribe("#")
    # Hent volum ved oppstart
    client.publish(tv_topic("platform_service", "getvolume"), "")

def on_tv_message(client, userdata, msg):
    global current_volume, is_muted, current_source, app_list
    try:
        payload = json.loads(msg.payload.decode())
        
        # Volum-endring fra TV eller fjernkontroll
        if "volumechange" in msg.topic and payload.get("volume_type") == 0:
            current_volume = payload.get("volume_value", 0)
            print(f"🔊 Volum: {current_volume}")
            publish_ha_state()
            
        # Mute status (volume_type 2)
        elif "volumechange" in msg.topic and payload.get("volume_type") == 2:
            is_muted = payload.get("volume_value") == 1
            print(f"🔇 Muted: {is_muted}")
            publish_ha_state()
        
        # Kilde-endring
        elif "state" in msg.topic and payload.get("statetype") == "sourceswitch":
            current_source = payload.get("sourcename")
            print(f"📺 Kilde: {current_source}")
            publish_ha_state()
        
        # App-liste (lagres for senere bruk)
        elif "applist" in msg.topic and isinstance(payload, list):
            app_list = {app.get("name"): app for app in payload}
            print(f"📱 Hentet {len(app_list)} apper")
            
    except:
        pass

# === HA CALLBACKS ===
def on_ha_connect(client, userdata, flags, rc, props=None):
    print("✅ Tilkoblet Home Assistant MQTT")
    
    device_info = {
        "identifiers": ["hisense_soverom"],
        "name": "Hisense Soverom",
        "manufacturer": "Hisense",
        "model": "Smart TV"
    }
    
    # === 1. KILDEVALG (Select) ===
    source_config = {
        "name": "Kilde",
        "unique_id": "hisense_soverom_source",
        "command_topic": "hisense/soverom/source/set",
        "state_topic": "hisense/soverom/source",
        "options": ["TV", "HDMI1", "HDMI2", "HDMI3", "AV"],
        "icon": "mdi:video-input-hdmi",
        "device": device_info
    }
    client.publish("homeassistant/select/hisense_soverom_source/config", json.dumps(source_config), retain=True)
    
    # === 2. VOLUM SLIDER ===
    volume_slider_config = {
        "name": "Volum",
        "unique_id": "hisense_soverom_volume_slider",
        "command_topic": "hisense/soverom/volume/set",
        "state_topic": "hisense/soverom/volume",
        "min": 0,
        "max": 30,
        "step": 1,
        "icon": "mdi:volume-high",
        "device": device_info
    }
    client.publish("homeassistant/number/hisense_soverom_volume/config", json.dumps(volume_slider_config), retain=True)
    
    # === 3. VOLUM OPP ===
    client.publish("homeassistant/button/hisense_soverom_volume_up/config", json.dumps({
        "name": "Volum Opp",
        "unique_id": "hisense_soverom_volume_up",
        "command_topic": "hisense/soverom/button/volume_up",
        "icon": "mdi:volume-plus",
        "device": device_info
    }), retain=True)
    
    # === 4. VOLUM NED ===
    client.publish("homeassistant/button/hisense_soverom_volume_down/config", json.dumps({
        "name": "Volum Ned",
        "unique_id": "hisense_soverom_volume_down",
        "command_topic": "hisense/soverom/button/volume_down",
        "icon": "mdi:volume-minus",
        "device": device_info
    }), retain=True)
    
    # === 5. MUTE ===
    client.publish("homeassistant/button/hisense_soverom_mute/config", json.dumps({
        "name": "Mute",
        "unique_id": "hisense_soverom_mute",
        "command_topic": "hisense/soverom/button/mute",
        "icon": "mdi:volume-mute",
        "device": device_info
    }), retain=True)
    
    # === 6. POWER ===
    client.publish("homeassistant/button/hisense_soverom_power/config", json.dumps({
        "name": "Power",
        "unique_id": "hisense_soverom_power",
        "command_topic": "hisense/soverom/button/power",
        "icon": "mdi:power",
        "device": device_info
    }), retain=True)
    
    # === 7. NAVIGASJONSKNAPPER ===
    for btn_id, name, icon, key in NAV_BUTTONS:
        btn_config = {
            "name": name,
            "unique_id": f"hisense_soverom_{btn_id}",
            "command_topic": f"hisense/soverom/button/{btn_id}",
            "icon": icon,
            "device": device_info
        }
        client.publish(f"homeassistant/button/hisense_soverom_{btn_id}/config", json.dumps(btn_config), retain=True)
    
    # === 8. MEDIA KNAPPER ===
    for btn_id, name, icon, key in MEDIA_BUTTONS:
        btn_config = {
            "name": name,
            "unique_id": f"hisense_soverom_{btn_id}",
            "command_topic": f"hisense/soverom/button/{btn_id}",
            "icon": icon,
            "device": device_info
        }
        client.publish(f"homeassistant/button/hisense_soverom_{btn_id}/config", json.dumps(btn_config), retain=True)
    
    # === APP KNAPPER (kommentert ut) ===
    # for btn_id, name, icon, app_name in APP_BUTTONS:
    #     btn_config = {
    #         "name": name,
    #         "unique_id": f"hisense_soverom_app_{btn_id}",
    #         "command_topic": f"hisense/soverom/app/{btn_id}",
    #         "icon": icon,
    #         "device": device_info
    #     }
    #     client.publish(f"homeassistant/button/hisense_soverom_app_{btn_id}/config", json.dumps(btn_config), retain=True)
    
    # Subscribe til kommandoer
    client.subscribe("hisense/soverom/button/#")
    client.subscribe("hisense/soverom/source/set")
    client.subscribe("hisense/soverom/volume/set")
    # client.subscribe("hisense/soverom/app/#")
    
    # Send online status
    client.publish("hisense/soverom/available", "online", retain=True)
    
    # Publiser nåværende state
    publish_ha_state()
    
    print("📡 Enheter registrert i Home Assistant")

def on_ha_message(client, userdata, msg):
    global current_volume, is_muted
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    print(f"📥 HA kommando: {topic} = {payload}")
    
    # === VOLUM ===
    if "button/volume_up" in topic:
        new_vol = min(current_volume + VOLUME_STEP, VOLUME_MAX)
        print(f"🔊 Volum opp: {current_volume} -> {new_vol}")
        tv_client.publish(tv_topic("platform_service", "changevolume"), str(new_vol))
        
    elif "button/volume_down" in topic:
        new_vol = max(current_volume - VOLUME_STEP, 0)
        print(f"🔉 Volum ned: {current_volume} -> {new_vol}")
        tv_client.publish(tv_topic("platform_service", "changevolume"), str(new_vol))
        
    elif "button/mute" in topic:
        print(f"🔇 Mute toggle")
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_MUTE")
    
    # === NAVIGASJON ===
    elif "button/up" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_UP")
    elif "button/down" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_DOWN")
    elif "button/left" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_LEFT")
    elif "button/right" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_RIGHT")
    elif "button/ok" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_OK")
    elif "button/back" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_BACK")
    elif "button/home" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_HOME")
    elif "button/menu" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_MENU")
    
    # === POWER ===
    elif "button/power" in topic:
        print("⚡ Power")
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_POWER")
    
    # === MEDIA ===
    elif "button/play" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_PLAY")
    elif "button/pause" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_PAUSE")
    elif "button/stop" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_STOP")
    elif "button/rewind" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_REWIND")
    elif "button/fastforward" in topic:
        tv_client.publish(tv_topic("remote_service", "sendkey"), "KEY_FASTFORWARD")
    
    # === VOLUM SLIDER ===
    elif "volume/set" in topic:
        try:
            new_vol = int(float(payload))
            new_vol = max(0, min(VOLUME_MAX, new_vol))
            print(f"🎚️ Volum slider: {new_vol}")
            tv_client.publish(tv_topic("platform_service", "changevolume"), str(new_vol))
        except:
            pass
    
    # === KILDEVALG ===
    elif "source/set" in topic:
        source = payload
        print(f"📺 Bytter kilde til: {source}")
        # Kildene har spesielle ID-er
        source_map = {
            "TV": {"sourceid": "TV", "sourcename": "TV"},
            "HDMI1": {"sourceid": "HDMI1", "sourcename": "HDMI1"},
            "HDMI2": {"sourceid": "HDMI2", "sourcename": "HDMI2"},
            "HDMI3": {"sourceid": "HDMI3", "sourcename": "HDMI3"},
            "AV": {"sourceid": "AVS", "sourcename": "AV"},
        }
        if source in source_map:
            tv_client.publish(tv_topic("ui_service", "changesource"), json.dumps(source_map[source]))
    
    # === APPER (kommentert ut) ===
    # elif "app/" in topic:
    #     app_id = topic.split("/")[-1]
    #     app_names = {"netflix": "Netflix", "youtube": "YouTube", "disney": "Disney+", "prime": "Prime Video"}
    #     if app_id in app_names and app_names[app_id] in app_list:
    #         app = app_list[app_names[app_id]]
    #         payload = json.dumps({"appId": app.get("appId"), "name": app.get("name"), "url": app.get("url")})
    #         tv_client.publish(tv_topic("ui_service", "launchapp"), payload)

def publish_ha_state():
    if ha_client:
        ha_client.publish("hisense/soverom/volume", str(current_volume))
        if current_source:
            ha_client.publish("hisense/soverom/source", current_source)

# === MAIN ===
def main():
    global tv_client, ha_client
    
    print("🚀 Starter Hisense TV Bridge...")
    
    # TV Client
    tv_client = mqtt.Client(
        client_id=TV_CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    tv_client.username_pw_set("hisenseservice", "multimqttservice")
    tv_client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
    tv_client.tls_insecure_set(True)
    tv_client.on_connect = on_tv_connect
    tv_client.on_message = on_tv_message
    
    # HA Client
    ha_client = mqtt.Client(
        client_id="HisenseBridge",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    ha_client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)
    ha_client.on_connect = on_ha_connect
    ha_client.on_message = on_ha_message
    
    # Koble til
    print("🔄 Kobler til TV...")
    tv_client.connect(TV_IP, TV_PORT, 60)
    tv_client.loop_start()
    
    time.sleep(2)
    
    print("🔄 Kobler til HA MQTT...")
    ha_client.connect(HA_MQTT_HOST, HA_MQTT_PORT, 60)
    ha_client.loop_start()
    
    print("\n" + "="*50)
    print("✅ Bridge kjører! Ctrl+C for å stoppe")
    print("="*50 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopper...")
        ha_client.publish("hisense/soverom/available", "offline", retain=True)
        tv_client.loop_stop()
        ha_client.loop_stop()

if __name__ == "__main__":
    main()
