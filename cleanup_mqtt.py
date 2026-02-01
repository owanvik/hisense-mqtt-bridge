#!/usr/bin/env python3
"""Slett alle Hisense MQTT discovery-meldinger"""

import paho.mqtt.client as mqtt
import time

HA_MQTT_HOST = "10.0.0.50"
HA_MQTT_PORT = 1883
HA_MQTT_USER = "hisense"
HA_MQTT_PASS = "hisense"

# Alle topics som skal slettes (tom payload = slett)
topics_to_delete = [
    # Gamle entiteter (Hisense Soverom)
    "homeassistant/button/hisense_soverom_volume_up/config",
    "homeassistant/button/hisense_soverom_volume_down/config",
    "homeassistant/button/hisense_soverom_mute/config",
    "homeassistant/button/hisense_soverom_power/config",
    "homeassistant/button/hisense_soverom_up/config",
    "homeassistant/button/hisense_soverom_down/config",
    "homeassistant/button/hisense_soverom_left/config",
    "homeassistant/button/hisense_soverom_right/config",
    "homeassistant/button/hisense_soverom_ok/config",
    "homeassistant/button/hisense_soverom_back/config",
    "homeassistant/button/hisense_soverom_home/config",
    "homeassistant/button/hisense_soverom_menu/config",
    "homeassistant/button/hisense_soverom_play/config",
    "homeassistant/button/hisense_soverom_pause/config",
    "homeassistant/button/hisense_soverom_stop/config",
    "homeassistant/button/hisense_soverom_rewind/config",
    "homeassistant/button/hisense_soverom_fastforward/config",
    "homeassistant/select/hisense_soverom_source/config",
    "homeassistant/number/hisense_soverom_volume/config",
    "homeassistant/sensor/hisense_soverom_volume/config",
    
    # "Hisense TV Soverom" - den gamle enheten
    "homeassistant/media_player/hisense_soverom/config",
    "homeassistant/media_player/hisense_tv_soverom/config",
    "homeassistant/button/hisense_tv_soverom_volume_up/config",
    "homeassistant/button/hisense_tv_soverom_volume_down/config",
    "homeassistant/button/hisense_tv_soverom_mute/config",
    "homeassistant/button/hisense_tv_soverom_power/config",
    "homeassistant/sensor/hisense_tv_soverom_volume/config",
    "homeassistant/number/hisense_tv_soverom_volume/config",
    "homeassistant/select/hisense_tv_soverom_source/config",
    
    # State topics (fjerner retained messages)
    "hisense/soverom/volume",
    "hisense/soverom/source",
    "hisense/soverom/available",
    "hisense/soverom/state",
]

def on_connect(client, userdata, flags, rc, props=None):
    print("✅ Tilkoblet MQTT")

client = mqtt.Client(
    client_id="HisenseCleanup",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)
client.on_connect = on_connect

print("🔄 Kobler til MQTT...")
client.connect(HA_MQTT_HOST, HA_MQTT_PORT, 60)
client.loop_start()
time.sleep(1)

print(f"🗑️ Sletter {len(topics_to_delete)} MQTT topics...")
for topic in topics_to_delete:
    client.publish(topic, "", retain=True)
    print(f"   ❌ {topic.split('/')[-2]}")

time.sleep(2)
client.loop_stop()
client.disconnect()

print("\n✅ Ferdig! Gå til Home Assistant og:")
print("   1. Innstillinger → Enheter og tjenester → MQTT")
print("   2. Finn 'Hisense Soverom' og 'Hisense TV Soverom'")
print("   3. Slett begge enhetene")
print("   4. Start bridge på nytt")
