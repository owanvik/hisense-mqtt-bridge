#!/usr/bin/env python3
"""Test volum med riktig volume_type"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HomeAssistant"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

volumes = []

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    global volumes
    try:
        payload = json.loads(msg.payload.decode())
        if "volume_value" in payload:
            vt = payload.get("volume_type", "?")
            vv = payload["volume_value"]
            print(f"   🔊 type={vt} value={vv}")
            if vt == 0:  # Kun TV-volum
                volumes.append(vv)
    except:
        pass

client = mqtt.Client(
    client_id=CLIENT_ID,
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set("hisenseservice", "multimqttservice")
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print(f"🔄 Kobler til...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()
time.sleep(2)

# Hent volum FØR
print("\n📊 Volum FØR:")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1.5)
volum_før = volumes[-1] if volumes else None
print(f"   → TV-volum: {volum_før}")

volumes.clear()

# Send 5x volumeup
print("\n📤 Sender 5x KEY_VOLUMEUP...")
for i in range(5):
    client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
                  json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"}))
    time.sleep(0.3)

time.sleep(1)

# Hent volum ETTER
print("\n📊 Volum ETTER:")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1.5)
volum_etter = volumes[-1] if volumes else None
print(f"   → TV-volum: {volum_etter}")

# Resultat
print("\n" + "="*40)
if volum_før is not None and volum_etter is not None:
    if volum_etter > volum_før:
        print(f"✅ VOLUM ØKTE: {volum_før} → {volum_etter}")
    elif volum_etter == volum_før:
        print(f"❌ VOLUM UENDRET: {volum_før}")
    else:
        print(f"❓ VOLUM SANK: {volum_før} → {volum_etter}")
else:
    print("❌ Kunne ikke lese volum")

client.loop_stop()
