#!/usr/bin/env python3
"""
Hisense TV MQTT Controller - Forbedret versjon
Med autentisering og bedre visning av data
"""

import ssl
import socket
import time
import json
import os
import threading
import paho.mqtt.client as mqtt

# === KONFIGURASJON ===
TV_IP = "10.0.0.109"
PORT = 36669
CLIENT_ID = "HomeAssistant"

# Sertifikater
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_CERT = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
CLIENT_KEY = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

# MQTT Credentials
MQTT_USERNAME = "hisenseservice"
MQTT_PASSWORD = "multimqttservice"

# State
connected = False
authenticated = False
waiting_for_auth = False
tv_state = {}
sources = []
apps = []
volume_info = {}

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        print("✅ MQTT tilkoblet!")
        connected = True
        client.subscribe("#")
    else:
        codes = {1: "Feil protokoll", 2: "Ugyldig klient-ID", 3: "Server utilgjengelig", 
                 4: "Feil brukernavn/passord", 5: "Ikke autorisert"}
        print(f"❌ Tilkobling feilet: {codes.get(rc, f'Ukjent feil {rc}')}")

def on_message(client, userdata, msg):
    global tv_state, sources, apps, volume_info, authenticated, waiting_for_auth
    
    topic = msg.topic
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
    except:
        return
    
    # Parse JSON
    data = None
    if payload:
        try:
            data = json.loads(payload)
        except:
            data = payload
    
    # Håndter forskjellige topics
    if "ui_service/state" in topic and "broadcast" in topic:
        tv_state = data if isinstance(data, dict) else {}
        print(f"\n📺 TV-STATUS OPPDATERT:")
        print(f"   Kilde: {tv_state.get('displayname', tv_state.get('sourcename', 'Ukjent'))}")
        print(f"   Signal: {'Ja' if tv_state.get('is_signal') else 'Nei'}")
        
    elif "sourcelist" in topic:
        sources = data if isinstance(data, list) else []
        print(f"\n📋 KILDER ({len(sources)} stk):")
        for s in sources:
            signal = "📶" if s.get('is_signal') == "1" else "  "
            print(f"   {signal} [{s.get('sourceid')}] {s.get('displayname', s.get('sourcename'))}")
            
    elif "applist" in topic:
        apps = data if isinstance(data, list) else []
        print(f"\n📱 APPER ({len(apps)} stk):")
        for i, app in enumerate(apps[:20]):  # Vis maks 20
            print(f"   {i+1}. {app.get('name', 'Ukjent')}")
        if len(apps) > 20:
            print(f"   ... og {len(apps) - 20} flere")
            
    elif "volume" in topic:
        volume_info = data if isinstance(data, dict) else {}
        vol = volume_info.get('volume_value', volume_info.get('volume', '?'))
        print(f"\n🔊 VOLUM: {vol}")
        
    elif "authentication" in topic and "close" not in topic:
        if data == "" or data is None:
            authenticated = True
            print("✅ Autentisert!")
        else:
            waiting_for_auth = True
            print(f"\n🔐 AUTENTISERING PÅKREVD!")
            print(f"   Se på TV-skjermen for en 4-sifret kode")
            
    elif "authenticationcode" in topic:
        if "close" in topic:
            waiting_for_auth = False
            print("   Autentiseringsdialog lukket")
        else:
            print(f"   Autentiseringskode mottatt")
            
    elif "tvsetting" in topic or "picture" in topic:
        print(f"\n⚙️ INNSTILLINGER:")
        if isinstance(data, dict):
            for k, v in list(data.items())[:10]:
                print(f"   {k}: {v}")
                
    elif "broadcast" in topic:
        # Andre broadcast-meldinger
        if data and data != "":
            print(f"\n📡 {topic.split('/')[-1]}:")
            if isinstance(data, dict):
                for k, v in data.items():
                    print(f"   {k}: {v}")
            elif isinstance(data, list):
                for item in data[:5]:
                    print(f"   - {item}")
            else:
                print(f"   {str(data)[:100]}")

def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    global connected
    connected = False
    print("🔌 Frakoblet")

def create_client():
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    return client

def connect_with_certs(client):
    global connected
    
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
            return True
        time.sleep(0.5)
    return False

def main():
    global waiting_for_auth
    
    print("=" * 60)
    print("   HISENSE TV MQTT CONTROLLER")
    print(f"   TV: {TV_IP} | Klient: {CLIENT_ID}")
    print("=" * 60)
    
    # Sjekk tilgjengelighet
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    if sock.connect_ex((TV_IP, PORT)) != 0:
        print("❌ TV-en svarer ikke. Er den slått på?")
        return
    sock.close()
    print("✅ TV er tilgjengelig")
    
    # Koble til
    client = create_client()
    if not connect_with_certs(client):
        print("❌ Kunne ikke koble til")
        return
    
    time.sleep(2)  # La meldinger komme inn
    
    # Topics
    base = f"/remoteapp/tv"
    topics = {
        "state": f"{base}/ui_service/{CLIENT_ID}/actions/gettvstate",
        "sources": f"{base}/ui_service/{CLIENT_ID}/actions/sourcelist",
        "apps": f"{base}/ui_service/{CLIENT_ID}/actions/applist",
        "volume": f"{base}/platform_service/{CLIENT_ID}/actions/getvolume",
        "set_volume": f"{base}/platform_service/{CLIENT_ID}/actions/changevolume",
        "key": f"{base}/remote_service/{CLIENT_ID}/actions/sendkey",
        "launch": f"{base}/ui_service/{CLIENT_ID}/actions/launchapp",
        "source": f"{base}/ui_service/{CLIENT_ID}/actions/changesource",
        "auth": f"{base}/ui_service/{CLIENT_ID}/actions/authenticationcode",
        "picture": f"{base}/platform_service/{CLIENT_ID}/actions/picturesetting",
    }
    
    print("\n" + "=" * 60)
    print("📺 KOMMANDOER:")
    print("=" * 60)
    print("  status    - Vis TV-status")
    print("  kilder    - Vis tilgjengelige kilder")
    print("  apper     - Vis installerte apper")
    print("  volum     - Vis volum")
    print("  vol+/vol- - Juster volum")
    print("  mute      - Mute/unmute")
    print("  hdmi1-4   - Bytt til HDMI")
    print("  tv        - Bytt til TV")
    print("  youtube   - Start YouTube")
    print("  netflix   - Start Netflix")
    print("  disney    - Start Disney+")
    print("  auth XXXX - Send autentiseringskode")
    print("  key XXXX  - Send tastetrykk (up/down/ok/back/menu/power)")
    print("  bilde     - Vis bildeinnstillinger")
    print("  quit      - Avslutt")
    print("-" * 60)
    
    # Hent initial status
    client.publish(topics["state"], "")
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd in ["quit", "exit", "q", "0"]:
                break
                
            elif cmd == "status":
                client.publish(topics["state"], "")
                
            elif cmd == "kilder" or cmd == "sources":
                client.publish(topics["sources"], "")
                
            elif cmd == "apper" or cmd == "apps":
                client.publish(topics["apps"], "")
                
            elif cmd == "volum" or cmd == "volume":
                client.publish(topics["volume"], "")
                
            elif cmd == "vol+" or cmd == "opp":
                client.publish(topics["key"], "KEY_VOLUMEUP")
                print("🔊 Volume opp")
                
            elif cmd == "vol-" or cmd == "ned":
                client.publish(topics["key"], "KEY_VOLUMEDOWN")
                print("🔉 Volume ned")
                
            elif cmd == "mute":
                client.publish(topics["key"], "KEY_MUTE")
                print("🔇 Mute")
                
            elif cmd.startswith("hdmi"):
                try:
                    num = int(cmd.replace("hdmi", ""))
                    source_id = f"HDMI{num}"
                    payload = json.dumps({"sourceid": source_id})
                    client.publish(topics["source"], payload)
                    print(f"📺 Bytter til HDMI {num}")
                except:
                    print("Bruk: hdmi1, hdmi2, hdmi3 eller hdmi4")
                    
            elif cmd == "tv":
                payload = json.dumps({"sourceid": "TV"})
                client.publish(topics["source"], payload)
                print("📺 Bytter til TV")
                
            elif cmd == "youtube":
                payload = json.dumps({"name": "YouTube", "urlType": 37, "storeType": 0, "url": "youtube"})
                client.publish(topics["launch"], payload)
                print("▶️ Starter YouTube...")
                
            elif cmd == "netflix":
                payload = json.dumps({"name": "Netflix", "urlType": 37, "storeType": 0, "url": "netflix"})
                client.publish(topics["launch"], payload)
                print("▶️ Starter Netflix...")
                
            elif cmd == "disney":
                payload = json.dumps({"name": "Disney+", "urlType": 37, "storeType": 0, "url": "disneyplus"})
                client.publish(topics["launch"], payload)
                print("▶️ Starter Disney+...")
                
            elif cmd.startswith("auth "):
                code = cmd.split(" ")[1]
                payload = json.dumps({"authNum": code})
                client.publish(topics["auth"], payload)
                print(f"🔐 Sender autentiseringskode: {code}")
                
            elif cmd.startswith("key "):
                key = cmd.split(" ")[1].upper()
                if not key.startswith("KEY_"):
                    key = "KEY_" + key
                client.publish(topics["key"], key)
                print(f"🎮 Sender: {key}")
                
            elif cmd == "bilde" or cmd == "picture":
                client.publish(topics["picture"], "")
                
            elif cmd in ["up", "down", "left", "right", "ok", "back", "menu", "home", "power"]:
                key = f"KEY_{cmd.upper()}"
                if cmd == "back":
                    key = "KEY_RETURNS"
                client.publish(topics["key"], key)
                print(f"🎮 {key}")
                
            elif cmd == "play":
                client.publish(topics["key"], "KEY_PLAY")
            elif cmd == "pause":
                client.publish(topics["key"], "KEY_PAUSE")
            elif cmd == "stop":
                client.publish(topics["key"], "KEY_STOP")
                
            elif cmd == "help" or cmd == "?":
                print("Skriv en kommando: status, kilder, apper, volum, hdmi1-4, youtube, netflix, etc.")
                
            elif cmd:
                print(f"Ukjent kommando: {cmd}. Skriv 'help' for hjelp.")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Avsluttet")

if __name__ == "__main__":
    main()
