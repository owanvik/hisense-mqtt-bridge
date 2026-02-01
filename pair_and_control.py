#!/usr/bin/env python3
"""
Hisense TV - Paring og kontroll
Steg 1: Par klienten med TV-en (vises PIN på TV-skjermen)
Steg 2: Kontroller TV-en
"""

import ssl
import socket
import time
import json
import os
import paho.mqtt.client as mqtt

TV_IP = "10.0.0.109"
PORT = 36669
CLIENT_ID = "HomeAssistant"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_CERT = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
CLIENT_KEY = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

connected = False
needs_auth = False
auth_complete = False
sources = []
apps = []

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        print("✅ MQTT tilkoblet!")
        connected = True
        client.subscribe("#")
    else:
        print(f"❌ Feil: {rc}")

def on_message(client, userdata, msg):
    global needs_auth, auth_complete, sources, apps
    
    topic = msg.topic
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
    except:
        return
    
    # Vis alle topics for debugging
    print(f"📩 {topic}")
    
    # Parse data
    data = None
    if payload and payload != '""':
        try:
            data = json.loads(payload)
            if data:
                print(f"   {json.dumps(data, ensure_ascii=False)[:200]}")
        except:
            if payload:
                print(f"   {payload[:200]}")
    
    # Sjekk authentication status
    if "authentication" in topic and "close" not in topic:
        if payload == "" or payload == '""':
            # Tom authentication = trenger paring
            needs_auth = True
            print("\n🔐 TV-EN TRENGER PARING!")
            print("   Se på TV-skjermen - det skal vises en 4-sifret kode")
            print("   Skriv: pin XXXX (erstatt XXXX med koden)")
        elif data:
            print(f"\n🔐 Auth data: {data}")
    
    elif "authenticationcode" in topic:
        if "close" in topic:
            auth_complete = True
            print("✅ Autentisering fullført!")
    
    elif "sourcelist" in topic and data:
        sources = data if isinstance(data, list) else []
        print(f"\n📋 KILDER ({len(sources)}):")
        for s in sources:
            print(f"   [{s.get('sourceid')}] {s.get('displayname', s.get('sourcename'))}")
    
    elif "applist" in topic and data:
        apps = data if isinstance(data, list) else []
        print(f"\n📱 APPER ({len(apps)}):")
        for app in apps[:15]:
            print(f"   - {app.get('name')}")
        if len(apps) > 15:
            print(f"   ... og {len(apps)-15} til")
    
    elif "volume" in topic and data:
        vol = data.get('volume_value', data.get('volume', '?'))
        print(f"\n🔊 Volum: {vol}")
    
    elif "state" in topic and "broadcast" in topic and data:
        print(f"\n📺 Status: {data.get('displayname', data.get('sourcename'))} (signal: {data.get('is_signal')})")

def main():
    global connected, needs_auth
    
    print("=" * 60)
    print("   HISENSE TV - PARING OG KONTROLL")
    print(f"   TV: {TV_IP}")
    print("=" * 60)
    
    # Sjekk tilgang
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    if sock.connect_ex((TV_IP, PORT)) != 0:
        print("❌ TV-en svarer ikke. Er den slått på?")
        return
    sock.close()
    
    # Koble til
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set("hisenseservice", "multimqttservice")
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.tls_set(
        ca_certs=None,
        certfile=CLIENT_CERT,
        keyfile=CLIENT_KEY,
        cert_reqs=ssl.CERT_NONE,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )
    client.tls_insecure_set(True)
    
    client.connect(TV_IP, PORT, keepalive=30)
    client.loop_start()
    
    for _ in range(20):
        if connected:
            break
        time.sleep(0.5)
    
    if not connected:
        print("❌ Kunne ikke koble til")
        return
    
    time.sleep(2)
    
    # Topics
    base = "/remoteapp/tv"
    topics = {
        "state": f"{base}/ui_service/{CLIENT_ID}/actions/gettvstate",
        "sources": f"{base}/ui_service/{CLIENT_ID}/actions/sourcelist",
        "apps": f"{base}/ui_service/{CLIENT_ID}/actions/applist",
        "volume": f"{base}/platform_service/{CLIENT_ID}/actions/getvolume",
        "key": f"{base}/remote_service/{CLIENT_ID}/actions/sendkey",
        "launch": f"{base}/ui_service/{CLIENT_ID}/actions/launchapp",
        "source": f"{base}/ui_service/{CLIENT_ID}/actions/changesource",
        "auth": f"{base}/ui_service/{CLIENT_ID}/actions/authenticationcode",
    }
    
    print("\n" + "-" * 60)
    print("KOMMANDOER:")
    print("  pin XXXX  - Send paringskode fra TV-skjermen")
    print("  status    - Hent TV-status")
    print("  kilder    - Hent kilder")
    print("  apper     - Hent apper")
    print("  volum     - Hent volum")
    print("  vol+/vol- - Volum opp/ned")
    print("  up/down/left/right/ok/back - Navigasjon")
    print("  hdmi1/hdmi2/hdmi3 - Bytt kilde")
    print("  youtube/netflix - Start app")
    print("  power     - Standby")
    print("  quit      - Avslutt")
    print("-" * 60)
    
    # Trigger authentication for å se om vi trenger å pare
    print("\n🔄 Sjekker autentisering...")
    client.publish(topics["state"], "")
    time.sleep(2)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd in ["quit", "q", "exit"]:
                break
            
            elif cmd.startswith("pin "):
                code = cmd.split(" ")[1].strip()
                payload = json.dumps({"authNum": code})
                client.publish(topics["auth"], payload)
                print(f"🔐 Sender PIN: {code}")
                
            elif cmd == "status":
                client.publish(topics["state"], "")
                
            elif cmd == "kilder":
                client.publish(topics["sources"], "")
                
            elif cmd == "apper":
                client.publish(topics["apps"], "")
                
            elif cmd == "volum":
                client.publish(topics["volume"], "")
                
            elif cmd == "vol+":
                client.publish(topics["key"], "KEY_VOLUMEUP")
                print("🔊+")
                
            elif cmd == "vol-":
                client.publish(topics["key"], "KEY_VOLUMEDOWN")
                print("🔉-")
                
            elif cmd == "mute":
                client.publish(topics["key"], "KEY_MUTE")
                
            elif cmd in ["up", "down", "left", "right", "ok", "menu", "home"]:
                key = f"KEY_{cmd.upper()}"
                client.publish(topics["key"], key)
                print(f"🎮 {key}")
                
            elif cmd == "back":
                client.publish(topics["key"], "KEY_RETURNS")
                print("🎮 KEY_RETURNS")
                
            elif cmd == "power":
                client.publish(topics["key"], "KEY_POWER")
                print("⏻ Standby")
                
            elif cmd.startswith("hdmi"):
                num = cmd.replace("hdmi", "")
                payload = json.dumps({"sourceid": f"HDMI{num}"})
                client.publish(topics["source"], payload)
                print(f"📺 Bytter til HDMI{num}")
                
            elif cmd == "tv":
                payload = json.dumps({"sourceid": "TV"})
                client.publish(topics["source"], payload)
                
            elif cmd == "youtube":
                payload = json.dumps({"name": "YouTube", "urlType": 37, "storeType": 0, "url": "youtube"})
                client.publish(topics["launch"], payload)
                print("▶️ YouTube")
                
            elif cmd == "netflix":
                payload = json.dumps({"name": "Netflix", "urlType": 37, "storeType": 0, "url": "netflix"})
                client.publish(topics["launch"], payload)
                print("▶️ Netflix")
                
            elif cmd == "disney":
                payload = json.dumps({"name": "Disney+", "urlType": 37, "storeType": 0, "url": "disneyplus"})
                client.publish(topics["launch"], payload)
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n👋 Avsluttet")

if __name__ == "__main__":
    main()
