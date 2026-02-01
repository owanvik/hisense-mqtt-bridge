#!/usr/bin/env python3
"""List alle tilgjengelige funksjoner fra TV"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

sources = []
apps = []

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")

def on_message(client, userdata, msg):
    global sources, apps
    try:
        payload = json.loads(msg.payload.decode())
        
        if "sourcelist" in msg.topic and isinstance(payload, list):
            sources = payload
            print(f"\n📺 KILDER ({len(payload)}):")
            for s in payload:
                print(f"   - {s.get('sourcename')} (id: {s.get('sourceid')})")
                
        elif "applist" in msg.topic and isinstance(payload, list):
            apps = payload
            print(f"\n📱 APPER ({len(payload)}):")
            for a in payload[:10]:  # Vis bare 10 første
                print(f"   - {a.get('name')}")
            if len(payload) > 10:
                print(f"   ... og {len(payload)-10} til")
                
    except:
        pass

client = mqtt.Client(
    client_id="HomeAssistant",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set("hisenseservice", "multimqttservice")
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Henter tilgjengelige funksjoner...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()
time.sleep(2)

# Hent kilder
client.publish("/remoteapp/tv/ui_service/HomeAssistant/actions/sourcelist", "")
time.sleep(2)

# Hent apper
client.publish("/remoteapp/tv/ui_service/HomeAssistant/actions/applist", "")
time.sleep(2)

client.loop_stop()

print("\n" + "="*50)
print("🎮 TILGJENGELIGE SENDKEY KOMMANDOER:")
print("="*50)
keys = [
    "KEY_POWER", "KEY_MUTE",
    "KEY_VOLUMEUP", "KEY_VOLUMEDOWN", 
    "KEY_CHANNELUP", "KEY_CHANNELDOWN",
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_OK",
    "KEY_BACK", "KEY_HOME", "KEY_MENU",
    "KEY_0", "KEY_1", "KEY_2", "KEY_3", "KEY_4",
    "KEY_5", "KEY_6", "KEY_7", "KEY_8", "KEY_9",
    "KEY_PLAY", "KEY_PAUSE", "KEY_STOP",
    "KEY_REWIND", "KEY_FASTFORWARD",
    "KEY_RED", "KEY_GREEN", "KEY_YELLOW", "KEY_BLUE",
]
for k in keys:
    print(f"   {k}")
