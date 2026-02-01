#!/usr/bin/env python3
"""Test ny bruker uten auth"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HASoverom"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

volumes = []

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet med {CLIENT_ID}")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "volume_value" in payload:
            vt = payload.get("volume_type", "?")
            vv = payload["volume_value"]
            if vt == 0:
                volumes.append(vv)
                print(f"🔊 Volum: {vv}")
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

print(f"🔄 Tester {CLIENT_ID}...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()
time.sleep(2)

# Hent volum
print("\n📊 Henter volum FØR...")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1.5)
vol_før = volumes[-1] if volumes else None
print(f"   Volum: {vol_før}")

volumes.clear()

# Send volumeup
print("\n📤 Sender KEY_VOLUMEUP x3...")
for _ in range(3):
    client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
                  json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"}))
    time.sleep(0.3)

time.sleep(1)

# Hent volum igjen
print("\n📊 Henter volum ETTER...")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1.5)
vol_etter = volumes[-1] if volumes else None
print(f"   Volum: {vol_etter}")

print("\n" + "="*40)
if vol_før is not None and vol_etter is not None:
    if vol_etter > vol_før:
        print(f"✅ FUNGERER! Volum: {vol_før} → {vol_etter}")
    else:
        print(f"❌ Volum uendret: {vol_før}")
        print("\n💡 TV-en svarer men ignorerer kommandoer.")
        print("   Mulige årsaker:")
        print("   - TV er i standby/screensaver")
        print("   - Noe blokkerer input (f.eks. en dialog)")
        print("   - HDMI-CEC kontrollerer volumet")

client.loop_stop()
