#!/usr/bin/env python3
"""
Hisense TV MQTT til Home Assistant

Kobler til Hisense TV og publiserer som MQTT-enhet til Home Assistant
via MQTT Discovery.
"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import sys
import argparse
import threading

# === KONFIGURASJON ===

# Hisense TV
TV_IP = "10.0.0.109"
TV_PORT = 36669
TV_MAC = "a0:62:fb:1b:f2:e1"
HISENSE_USER = "hisenseservice"
HISENSE_PASS = "multimqttservice"

# Home Assistant MQTT Broker
HA_MQTT_HOST = os.environ.get("HA_MQTT_HOST", "10.0.0.50")
HA_MQTT_PORT = int(os.environ.get("HA_MQTT_PORT", "1883"))
HA_MQTT_USER = os.environ.get("HA_MQTT_USER", "")
HA_MQTT_PASS = os.environ.get("HA_MQTT_PASS", "")

# Enhetsnavn
DEVICE_NAME = "Hisense TV Soverom"
DEVICE_ID = "hisense_tv_soverom"
UNIQUE_ID = TV_MAC.replace(":", "").lower()

# Sertifikater
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

# MQTT Topics for HA
HA_BASE = f"homeassistant"
STATE_TOPIC = f"hisense/{DEVICE_ID}/state"
COMMAND_TOPIC = f"hisense/{DEVICE_ID}/command"
AVAILABILITY_TOPIC = f"hisense/{DEVICE_ID}/available"

class HisenseMQTTBridge:
    def __init__(self):
        self.tv_client = None
        self.ha_client = None
        self.tv_connected = False
        self.ha_connected = False
        self.running = True
        
        self.state = {
            "state": "off",
            "volume_level": 0,
            "is_volume_muted": False,
            "source": "Unknown",
            "source_list": [],
            "app_id": "",
            "app_name": ""
        }
        
    def setup_ha_mqtt(self):
        """Setter opp MQTT-klient for Home Assistant"""
        self.ha_client = mqtt.Client(
            client_id=f"hisense_bridge_{UNIQUE_ID}",
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        
        if HA_MQTT_USER and HA_MQTT_PASS:
            self.ha_client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)
            
        self.ha_client.will_set(AVAILABILITY_TOPIC, "offline", retain=True)
        self.ha_client.on_connect = self.on_ha_connect
        self.ha_client.on_message = self.on_ha_message
        
    def setup_tv_mqtt(self):
        """Setter opp MQTT-klient for Hisense TV"""
        self.tv_client = mqtt.Client(
            client_id="HomeAssistant",
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.tv_client.username_pw_set(HISENSE_USER, HISENSE_PASS)
        self.tv_client.tls_set(
            certfile=CERT_FILE,
            keyfile=KEY_FILE,
            cert_reqs=ssl.CERT_NONE
        )
        self.tv_client.tls_insecure_set(True)
        self.tv_client.on_connect = self.on_tv_connect
        self.tv_client.on_message = self.on_tv_message
        self.tv_client.on_disconnect = self.on_tv_disconnect
        
    def on_ha_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Koblet til Home Assistant MQTT")
            self.ha_connected = True
            
            # Publiser MQTT Discovery
            self.publish_discovery()
            
            # Subscribe til kommandoer
            client.subscribe(f"{COMMAND_TOPIC}/#")
            
            # Marker som online
            client.publish(AVAILABILITY_TOPIC, "online", retain=True)
        else:
            print(f"❌ HA MQTT feil: {rc}")
            
    def on_ha_message(self, client, userdata, msg):
        """Håndterer kommandoer fra Home Assistant"""
        topic = msg.topic
        payload = msg.payload.decode()
        
        print(f"📥 HA kommando: {topic} = {payload}")
        
        if "power" in topic:
            if payload.lower() in ["on", "off", "toggle"]:
                self.send_key("KEY_POWER")
        elif "volume_up" in topic:
            self.send_key("KEY_VOLUMEUP")
        elif "volume_down" in topic:
            self.send_key("KEY_VOLUMEDOWN")
        elif "mute" in topic:
            self.send_key("KEY_MUTE")
        elif "source" in topic:
            # Bytt kilde
            self.change_source(payload)
        elif "key" in topic:
            # Send vilkårlig tast
            self.send_key(payload)
            
    def on_tv_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Koblet til Hisense TV")
            self.tv_connected = True
            self.state["state"] = "on"
            client.subscribe("#")
            self.request_tv_data()
            self.publish_state()
        else:
            print(f"❌ TV MQTT feil: {rc}")
            
    def on_tv_disconnect(self, client, userdata, rc, properties=None):
        print("🔌 Frakoblet fra TV")
        self.tv_connected = False
        self.state["state"] = "off"
        if self.ha_connected:
            self.publish_state()
            
    def on_tv_message(self, client, userdata, msg):
        """Håndterer meldinger fra TV-en"""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except:
            return
            
        changed = False
        
        if "volume" in topic.lower():
            if isinstance(payload, dict):
                if "volume_value" in payload:
                    self.state["volume_level"] = payload["volume_value"] / 100
                    self.state["is_volume_muted"] = payload.get("volume_mute", 0) == 1
                    changed = True
                    
        elif "sourcelist" in topic.lower():
            if isinstance(payload, list):
                self.state["source_list"] = [
                    s.get("displayname", s.get("sourcename", "?")) 
                    for s in payload
                ]
                changed = True
                
        elif "applist" in topic.lower():
            if isinstance(payload, list):
                # Lagre app-liste for senere bruk
                self.apps = payload
                changed = True
                
        elif "state" in topic.lower() and isinstance(payload, dict):
            if "displayname" in payload or "sourcename" in payload:
                self.state["source"] = payload.get("displayname", payload.get("sourcename", "Unknown"))
                self.state["state"] = "on"
                changed = True
                
        if changed:
            self.publish_state()
            
    def request_tv_data(self):
        """Henter data fra TV-en"""
        base = "/remoteapp/tv"
        client_id = "HomeAssistant"
        
        self.tv_client.publish(f"{base}/ui_service/{client_id}/actions/sourcelist", "")
        time.sleep(0.2)
        self.tv_client.publish(f"{base}/platform_service/{client_id}/actions/getvolume", "")
        time.sleep(0.2)
        self.tv_client.publish(f"{base}/ui_service/{client_id}/actions/applist", "")
        
    def send_key(self, key):
        """Sender tastetrykkkommando til TV-en"""
        if not self.tv_connected:
            print(f"⚠️ TV ikke tilkoblet, kan ikke sende {key}")
            return
            
        topic = f"/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey"
        payload = json.dumps({"keytype": "keypress", "keyvalue": key})
        self.tv_client.publish(topic, payload)
        print(f"📺 Sendt: {key}")
        
    def change_source(self, source_name):
        """Bytter kilde på TV-en"""
        topic = f"/remoteapp/tv/ui_service/HomeAssistant/actions/changesource"
        payload = json.dumps({"sourcename": source_name})
        self.tv_client.publish(topic, payload)
        print(f"📺 Bytter til: {source_name}")
        
    def publish_discovery(self):
        """Publiserer MQTT Discovery for Home Assistant"""
        
        # Device info (deles av alle entiteter)
        device_info = {
            "identifiers": [UNIQUE_ID],
            "name": DEVICE_NAME,
            "manufacturer": "Hisense",
            "model": "VIDAA TV",
            "sw_version": "MQTT Bridge 1.0"
        }
        
        # Media Player
        media_player_config = {
            "name": None,  # Bruker device name
            "unique_id": f"{UNIQUE_ID}_media_player",
            "object_id": DEVICE_ID,
            "device": device_info,
            "state_topic": STATE_TOPIC,
            "command_topic": f"{COMMAND_TOPIC}/power",
            "availability_topic": AVAILABILITY_TOPIC,
            "payload_on": "on",
            "payload_off": "off",
            "volume_level_topic": STATE_TOPIC,
            "volume_level_template": "{{ value_json.volume_level }}",
            "source_topic": STATE_TOPIC,
            "source_template": "{{ value_json.source }}",
            "icon": "mdi:television"
        }
        
        self.ha_client.publish(
            f"{HA_BASE}/media_player/{DEVICE_ID}/config",
            json.dumps(media_player_config),
            retain=True
        )
        
        # Volum-sensor
        volume_config = {
            "name": "Volum",
            "unique_id": f"{UNIQUE_ID}_volume",
            "object_id": f"{DEVICE_ID}_volum",
            "device": device_info,
            "state_topic": STATE_TOPIC,
            "value_template": "{{ (value_json.volume_level * 100) | int }}",
            "unit_of_measurement": "%",
            "icon": "mdi:volume-high",
            "availability_topic": AVAILABILITY_TOPIC
        }
        
        self.ha_client.publish(
            f"{HA_BASE}/sensor/{DEVICE_ID}_volume/config",
            json.dumps(volume_config),
            retain=True
        )
        
        # Kilde-sensor
        source_config = {
            "name": "Kilde",
            "unique_id": f"{UNIQUE_ID}_source",
            "object_id": f"{DEVICE_ID}_kilde",
            "device": device_info,
            "state_topic": STATE_TOPIC,
            "value_template": "{{ value_json.source }}",
            "icon": "mdi:video-input-hdmi",
            "availability_topic": AVAILABILITY_TOPIC
        }
        
        self.ha_client.publish(
            f"{HA_BASE}/sensor/{DEVICE_ID}_source/config",
            json.dumps(source_config),
            retain=True
        )
        
        # Power-knapp
        buttons = [
            ("power", "KEY_POWER", "mdi:power", "Power"),
            ("mute", "KEY_MUTE", "mdi:volume-mute", "Mute"),
            ("volume_up", "KEY_VOLUMEUP", "mdi:volume-plus", "Volum opp"),
            ("volume_down", "KEY_VOLUMEDOWN", "mdi:volume-minus", "Volum ned"),
            ("home", "KEY_HOME", "mdi:home", "Home"),
            ("back", "KEY_BACK", "mdi:arrow-left", "Tilbake"),
        ]
        
        for btn_id, key, icon, name in buttons:
            btn_config = {
                "name": name,
                "unique_id": f"{UNIQUE_ID}_{btn_id}",
                "object_id": f"{DEVICE_ID}_{btn_id}",
                "device": device_info,
                "command_topic": f"{COMMAND_TOPIC}/key",
                "payload_press": key,
                "icon": icon,
                "availability_topic": AVAILABILITY_TOPIC
            }
            
            self.ha_client.publish(
                f"{HA_BASE}/button/{DEVICE_ID}_{btn_id}/config",
                json.dumps(btn_config),
                retain=True
            )
            
        print("📢 MQTT Discovery publisert")
        
    def publish_state(self):
        """Publiserer gjeldende tilstand til HA"""
        if self.ha_connected:
            self.ha_client.publish(STATE_TOPIC, json.dumps(self.state), retain=True)
            
    def connect_tv(self):
        """Kobler til TV-en med reconnect-logikk"""
        while self.running:
            if not self.tv_connected:
                try:
                    print(f"🔄 Kobler til TV ({TV_IP})...")
                    self.tv_client.connect(TV_IP, TV_PORT, 60)
                    self.tv_client.loop_start()
                except Exception as e:
                    print(f"❌ TV-tilkobling feilet: {e}")
                    self.state["state"] = "off"
                    self.publish_state()
            time.sleep(30)  # Prøv på nytt hvert 30. sekund
            
    def run(self):
        """Hovedløkke"""
        print(f"🚀 Starter Hisense MQTT Bridge for {DEVICE_NAME}")
        
        # Setup klienter
        self.setup_ha_mqtt()
        self.setup_tv_mqtt()
        
        # Koble til HA MQTT
        try:
            print(f"🔄 Kobler til HA MQTT ({HA_MQTT_HOST})...")
            self.ha_client.connect(HA_MQTT_HOST, HA_MQTT_PORT, 60)
            self.ha_client.loop_start()
        except Exception as e:
            print(f"❌ Kunne ikke koble til HA MQTT: {e}")
            return
            
        # Start TV-tilkobling i egen tråd
        tv_thread = threading.Thread(target=self.connect_tv, daemon=True)
        tv_thread.start()
        
        # Periodisk oppdatering
        try:
            while self.running:
                if self.tv_connected:
                    self.request_tv_data()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n👋 Avslutter...")
            self.running = False
            
        # Cleanup
        self.ha_client.publish(AVAILABILITY_TOPIC, "offline", retain=True)
        self.ha_client.loop_stop()
        self.tv_client.loop_stop()

def main():
    parser = argparse.ArgumentParser(description="Hisense TV MQTT Bridge")
    parser.add_argument("--mqtt-host", default="10.0.0.50", help="HA MQTT broker host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="HA MQTT broker port")
    parser.add_argument("--mqtt-user", default="", help="MQTT brukernavn")
    parser.add_argument("--mqtt-pass", default="", help="MQTT passord")
    
    args = parser.parse_args()
    
    # Oppdater globale variabler
    global HA_MQTT_HOST, HA_MQTT_PORT, HA_MQTT_USER, HA_MQTT_PASS
    HA_MQTT_HOST = args.mqtt_host
    HA_MQTT_PORT = args.mqtt_port
    HA_MQTT_USER = args.mqtt_user
    HA_MQTT_PASS = args.mqtt_pass
    
    bridge = HisenseMQTTBridge()
    bridge.run()

if __name__ == "__main__":
    main()
