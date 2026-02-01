#!/usr/bin/env python3
"""Tving re-autentisering med TV"""

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

auth_needed = False
auth_done = False

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet TV!")
    client.subscribe("#")
    
    # Trigger authentication umiddelbart
    print("🔐 Ber om autentisering...")
    client.publish(f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/gettvstate", "")
    
def on_message(client, userdata, msg):
    global auth_needed, auth_done
    
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
    except:
        payload = {}
    
    if "authentication" in topic and "code" not in topic:
        print(f"\n🔐 Auth status: {payload}")
        
        if not payload or payload == {} or payload.get("result") == 0:
            auth_needed = True
            print("\n" + "="*50)
            print("📺 SE PÅ TV-SKJERMEN FOR EN 4-SIFRET KODE!")
            print("="*50)
        elif payload.get("result") == 1:
            print("✅ Allerede autorisert!")
            auth_done = True
            
    elif "authenticationcode" in topic:
        print(f"🔑 Auth respons: {payload}")
        if payload.get("result") == 1:
            print("\n✅ AUTENTISERING VELLYKKET!")
            auth_done = True
        else:
            print("❌ Autentisering feilet!")

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

print(f"🔄 Kobler til TV ({TV_IP})...")
print("📺 Hold øye med TV-skjermen for en kode!\n")

client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

# Vent på auth-melding eller timeout
for i in range(10):
    time.sleep(1)
    if auth_needed or auth_done:
        break

if auth_needed and not auth_done:
    print("\n" + "="*50)
    code = input("Skriv inn koden fra TV: ").strip()
    print("="*50)
    
    if code:
        payload = json.dumps({"authNum": code})
        topic = f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode"
        print(f"📤 Sender kode: {code}")
        client.publish(topic, payload)
        
        # Vent på bekreftelse
        for i in range(5):
            time.sleep(1)
            if auth_done:
                break
                
        if auth_done:
            print("\n🎉 Klar til bruk! Kjør bridge-scriptet på nytt.")
        else:
            print("\n❌ Fikk ikke bekreftelse. Prøv igjen.")
elif not auth_needed and not auth_done:
    print("\n⚠️ Fikk ingen auth-melding fra TV.")
    print("   Prøv å slå TV helt av og på igjen.")

client.loop_stop()
