#!/usr/bin/env python3
"""
Hisense TV MQTT Bridge for Home Assistant
==========================================
Usage:
  First run:  python3 hisense_bridge.py --setup
  Normal:     python3 hisense_bridge.py

Author: https://github.com/owanvik
License: MIT
"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import sys
import yaml
import argparse
import logging
import socket
from typing import Dict, Any, Optional

__version__ = "1.1.0"

# ============================================================================
# EMBEDDED CERTIFICATES - Standard RemoteNOW certs (same for all Hisense TVs)
# ============================================================================

CERT_CHAIN = """-----BEGIN CERTIFICATE-----
MIIDvTCCAqWgAwIBAgIBAjANBgkqhkiG9w0BAQsFADBnMQswCQYDVQQGEwJDTjER
MA8GA1UECAwIc2hhbmRvbmcxEDAOBgNVBAcMB3FpbmdkYW8xCzAJBgNVBAoMAmho
MRMwEQYDVQQLDAptdWx0aW1lZGlhMREwDwYDVQQDDAhSZW1vdGVDQTAeFw0xODA0
MTkwMjAxMTdaFw00MzA0MTMwMjAxMTdaMGAxCzAJBgNVBAYTAkNOMREwDwYDVQQI
DAhzaGFuZG9uZzELMAkGA1UECgwCaGgxFDASBgNVBAsMC211bHRpc2NyZWVuMRsw
GQYDVQQDDBJyZW1vdGVjbGllbnRtb2JpbGUwggEiMA0GCSqGSIb3DQEBAQUAA4IB
DwAwggEKAoIBAQDu/o3p42CAraBA19IrYteEt8N8dyAvUmEyTVZMwHobwzNUABra
zUXhmFvduh02q/1y2TblB8dHSf53WKV+5O+sRpD7dc1lbhgoYLmHp3yVxrVDDKTo
z22fH54LrLm3t2k3j3ShXMbJIBEQqFJxW0P0I4Kj7wktKWBQ1rJjK3gFgHxaRugC
0oGZuv16M9Dn7tKpg+VX9SQ5Uj6nFjHv5scFUOBC7rPPlcFNQhkZT4Mdg/fcCFlJ
0hF5R6BDniRkRLEmsyNWhFSUf6UKDcNIDuPlcjYEmZNB5p4OGVWt0c/A5q057ZVO
RsSq9dwUgkSjj4Zz8nGK1lf3P5KVFMdocvzDAgMBAAGjezB5MAkGA1UdEwQCMAAw
LAYJYIZIAYb4QgENBB8WHU9wZW5TU0wgR2VuZXJhdGVkIENlcnRpZmljYXRlMB0G
A1UdDgQWBBSoDVzwztBO4zBMk73za2OMYSa+3DAfBgNVHSMEGDAWgBQjQIKRqSQG
hzF4k4+glDyqSfz8OzANBgkqhkiG9w0BAQsFAAOCAQEAgrk7ZK0/eGlY8uqAql25
R+cm17C+3MAvAj7yuU889CewPDPTtZmM05/1i0bV1oo2Pp9fLf0dxLovTwBpvAN8
lcxYNPxbZ824+sSncwx2AujmTJk7eIUoHczhluiU6rapK8apkU/iN4GNcBZkbccn
1FghvHaAKmUefzOwbY2LOAd7Z1KhKmf6MyL7RqN8LAgx3i2uiW1GM4C8KeFxZ090
9+e4R6eufW/V+58/HJtF9jECeNikLvJpxveCC6Q/N49s72hHZC0L0NeJ7GNKzoOi
8lXL5QgNGCg/bawsx9q5YvWLsDOVJIEhWv3MxmnC/reIeDf7iMEK3BP5E4u8uTzJ
Hg==
-----END CERTIFICATE-----
"""

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDu/o3p42CAraBA
19IrYteEt8N8dyAvUmEyTVZMwHobwzNUABrazUXhmFvduh02q/1y2TblB8dHSf53
WKV+5O+sRpD7dc1lbhgoYLmHp3yVxrVDDKToz22fH54LrLm3t2k3j3ShXMbJIBEQ
qFJxW0P0I4Kj7wktKWBQ1rJjK3gFgHxaRugC0oGZuv16M9Dn7tKpg+VX9SQ5Uj6n
FjHv5scFUOBC7rPPlcFNQhkZT4Mdg/fcCFlJ0hF5R6BDniRkRLEmsyNWhFSUf6UK
DcNIDuPlcjYEmZNB5p4OGVWt0c/A5q057ZVORsSq9dwUgkSjj4Zz8nGK1lf3P5KV
FMdocvzDAgMBAAECggEBAIwImx5wHBtJoJxd2MeTIrSg9+n14uXXXxwaNHbEUMfz
mB+f8BxEKq4El89TPcrK+7ZPj9qitCEROgiz6ERx3/0RW+H7JF5KI92EzzCs8lLQ
G2UuA3JmF9UksXYlvqvmy7/CTpQ9yDwQje80sRm6YBast99WMApGNCkpo1x4G9sc
S994P5wQwE+aC4encNDfrbPmDco2vjTIhVmcFJ9hxfPvkZbecxlMnKnh1eQtLYzB
DxWTTtpKzCg+EDhp67aE9MlB/HJ06hCHyrt/QaUGfrAa0lGOOJq2tHK+D7ZCi1BW
Y7FXHwrkgO+PiEtjCex6d4I7gZKoZuO8oIhRbaWvMAECgYEA+d6kCnOk7z+AJFzm
MuITuASBxTZovguGuQ2hKX479pKLw+ehs0J/srR35SPHeLaAzsuG8Xi5tKNpbnY9
c/aHfEdj+CYP8k5aWvhuGO3dZYyGTHlDcex4Tmx1ytOeC74RWJxHRPWg21l29Nfd
MmlW2+UW8+TEDPY/if6AGMW4Pd8CgYEA9Nub1OP5wX8sllRuGBnMm14Mx+p6bEnp
AEB81Nj8DwYKMaWlrq+l6R0RB/jsnaSRe0KfdL1MKN5VSOfevd2gwgET0vJCRhPk
rlBG8BVyG9ma1Fd+K00CQ2iOMVSIqW6OKDDiXVif2/U51mrc0oz3JXXFR14ck3TR
El5auO9WVZ0CgYBNxy/o0PaWQn3w07oUPKtGrKB4cudHwO6+y69O6yxfJF69LGz5
D8oQJnzrpqeAu858kH4AzEOCJxu6drPKVQL3fIFxzOdJ1Xnqt0oOGHzCD2v+ggCs
hZ8tSjWgXR7lKNTdcEf+/zaDEOYmcMs51fBjonvyj1M3da9xlPbqvyEKoQKBgQDm
comHI8i7w+VC1tOG+0EGOM3umU/++tC/2/GgoVcZDKYrc6srbUTI0QJmbnDDLU9+
ooVQaZh0HkxGAXQxXZUfAcSWlEqria2AIS2iZ4ytiW+eyXmFZ0TqDE1HQDgevl4s
lVV2ZSKO8Y0tsAWEZAd2yhCRypE6docOsp7PzvGCQQKBgQCinwRjA6qjSEUcXwR1
F7ep46RNe8JGpJ2ZMffneFct8P4fyKYMSY5zZBc9kYSxpgJPZc5Y+V5Tq+vWc4SX
/QNCZLcC5wMVs2jp8LYruoR0QoQdizpvlKQC2s4UD7Lp12lntJsCDULN9G9lzKUI
LgVhEy5cFTsByGHGWF6LAKrpHA==
-----END PRIVATE KEY-----
"""

# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.join(get_script_dir(), "config.yaml")


def write_embedded_certs() -> tuple:
    """Write embedded certificates to files."""
    cert_dir = os.path.join(get_script_dir(), ".certs")
    os.makedirs(cert_dir, exist_ok=True)
    
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    
    with open(cert_path, "w") as f:
        f.write(CERT_CHAIN.strip())
    with open(key_path, "w") as f:
        f.write(PRIVATE_KEY.strip())
    
    return cert_path, key_path


def test_tv_connection(ip: str, port: int = 36669) -> bool:
    """Test TCP connection to TV."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False


def run_setup():
    """Interactive setup wizard."""
    print("")
    print("=" * 60)
    print("  🔧 Hisense TV MQTT Bridge - Setup Wizard")
    print("=" * 60)
    print("")
    print("SSL certificates are built-in - no manual extraction needed!")
    print("")
    
    config = {"tv": {}, "mqtt": {}, "device": {}, "volume": {}}
    
    # TV Settings
    print("📺 TV SETTINGS")
    print("-" * 40)
    
    while True:
        tv_ip = input("Enter your Hisense TV IP address: ").strip()
        if not tv_ip:
            print("❌ IP address is required")
            continue
        
        print(f"🔄 Testing connection to {tv_ip}:36669...")
        if test_tv_connection(tv_ip):
            print("✅ TV found!")
            break
        else:
            print("⚠️  Could not connect. Make sure TV is on and IP is correct.")
            retry = input("Continue anyway? (y/n): ").strip().lower()
            if retry == 'y':
                break
    
    config["tv"]["ip"] = tv_ip
    config["tv"]["port"] = 36669
    config["tv"]["client_id"] = input("Client ID [HomeAssistant]: ").strip() or "HomeAssistant"
    print("")
    
    # MQTT Settings
    print("🔌 HOME ASSISTANT MQTT SETTINGS")
    print("-" * 40)
    
    config["mqtt"]["host"] = input("MQTT broker IP (your HA IP): ").strip()
    config["mqtt"]["port"] = int(input("MQTT port [1883]: ").strip() or "1883")
    
    mqtt_user = input("MQTT username (empty if none): ").strip()
    if mqtt_user:
        config["mqtt"]["username"] = mqtt_user
        config["mqtt"]["password"] = input("MQTT password: ").strip()
    print("")
    
    # Device Settings
    print("🏷️  DEVICE SETTINGS")
    print("-" * 40)
    
    device_id = input("Device ID (e.g., hisense_bedroom) [hisense_tv]: ").strip() or "hisense_tv"
    config["device"]["id"] = device_id
    config["device"]["name"] = input("Device name [Hisense TV]: ").strip() or "Hisense TV"
    config["device"]["topic_prefix"] = f"hisense/{device_id.replace('hisense_', '')}"
    print("")
    
    # Volume Settings
    print("🔊 VOLUME SETTINGS")
    print("-" * 40)
    
    config["volume"]["max"] = int(input("Maximum volume [30]: ").strip() or "30")
    config["volume"]["step"] = int(input("Volume step [1]: ").strip() or "1")
    print("")
    
    # Save config
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print("=" * 60)
    print(f"✅ Configuration saved!")
    print("")
    print("To start the bridge, run:")
    print(f"  python3 hisense_bridge.py")
    print("=" * 60)


class HisenseBridge:
    """Bridge between Hisense TV and Home Assistant via MQTT."""
    
    NAV_BUTTONS = [
        ("up", "Up", "mdi:arrow-up", "KEY_UP"),
        ("down", "Down", "mdi:arrow-down", "KEY_DOWN"),
        ("left", "Left", "mdi:arrow-left", "KEY_LEFT"),
        ("right", "Right", "mdi:arrow-right", "KEY_RIGHT"),
        ("ok", "OK", "mdi:check-circle", "KEY_OK"),
        ("back", "Back", "mdi:arrow-left-circle", "KEY_BACK"),
        ("home", "Home", "mdi:home", "KEY_HOME"),
        ("menu", "Menu", "mdi:menu", "KEY_MENU"),
    ]
    
    MEDIA_BUTTONS = [
        ("play", "Play", "mdi:play", "KEY_PLAY"),
        ("pause", "Pause", "mdi:pause", "KEY_PAUSE"),
        ("stop", "Stop", "mdi:stop", "KEY_STOP"),
        ("rewind", "Rewind", "mdi:rewind", "KEY_REWIND"),
        ("fastforward", "Fast Forward", "mdi:fast-forward", "KEY_FASTFORWARD"),
    ]
    
    SOURCES = ["TV", "HDMI1", "HDMI2", "HDMI3", "AV"]
    
    SOURCE_MAP = {
        "TV": {"sourceid": "TV", "sourcename": "TV"},
        "HDMI1": {"sourceid": "HDMI1", "sourcename": "HDMI1"},
        "HDMI2": {"sourceid": "HDMI2", "sourcename": "HDMI2"},
        "HDMI3": {"sourceid": "HDMI3", "sourcename": "HDMI3"},
        "AV": {"sourceid": "AVS", "sourcename": "AV"},
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        self.tv_ip = config["tv"]["ip"]
        self.tv_port = config["tv"].get("port", 36669)
        self.tv_client_id = config["tv"].get("client_id", "HomeAssistant")
        
        self.ha_host = config["mqtt"]["host"]
        self.ha_port = config["mqtt"].get("port", 1883)
        self.ha_user = config["mqtt"].get("username", "")
        self.ha_pass = config["mqtt"].get("password", "")
        
        self.device_id = config["device"].get("id", "hisense_tv")
        self.device_name = config["device"].get("name", "Hisense TV")
        self.topic_prefix = config["device"].get("topic_prefix", "hisense/tv")
        
        self.volume_max = config.get("volume", {}).get("max", 30)
        self.volume_step = config.get("volume", {}).get("step", 1)
        
        self.cert_file, self.key_file = write_embedded_certs()
        
        self.current_volume = 0
        self.is_muted = False
        self.current_source: Optional[str] = None
        self.tv_client: Optional[mqtt.Client] = None
        self.ha_client: Optional[mqtt.Client] = None
    
    def tv_topic(self, service: str, action: str) -> str:
        return f"/remoteapp/tv/{service}/{self.tv_client_id}/actions/{action}"
    
    def device_info(self) -> Dict[str, Any]:
        return {
            "identifiers": [self.device_id],
            "name": self.device_name,
            "manufacturer": "Hisense",
            "model": "Smart TV",
            "sw_version": __version__
        }
    
    def on_tv_connect(self, client, userdata, flags, rc, props=None):
        logger.info("✅ Connected to TV")
        client.subscribe("#")
        client.publish(self.tv_topic("platform_service", "getvolume"), "")
    
    def on_tv_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if "volumechange" in msg.topic and payload.get("volume_type") == 0:
                self.current_volume = payload.get("volume_value", 0)
                logger.info(f"🔊 Volume: {self.current_volume}")
                self.publish_ha_state()
            
            elif "volumechange" in msg.topic and payload.get("volume_type") == 2:
                self.is_muted = payload.get("volume_value") == 1
                logger.info(f"🔇 Muted: {self.is_muted}")
            
            elif "state" in msg.topic and payload.get("statetype") == "sourceswitch":
                self.current_source = payload.get("sourcename")
                logger.info(f"📺 Source: {self.current_source}")
                self.publish_ha_state()
                
        except (json.JSONDecodeError, KeyError):
            pass
    
    def on_ha_connect(self, client, userdata, flags, rc, props=None):
        logger.info("✅ Connected to Home Assistant MQTT")
        self.register_entities()
        
        client.subscribe(f"{self.topic_prefix}/button/#")
        client.subscribe(f"{self.topic_prefix}/source/set")
        client.subscribe(f"{self.topic_prefix}/volume/set")
        
        client.publish(f"{self.topic_prefix}/available", "online", retain=True)
        self.publish_ha_state()
        
        logger.info("📡 Entities registered in Home Assistant")
    
    def on_ha_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        
        if "button/volume_up" in topic:
            new_vol = min(self.current_volume + self.volume_step, self.volume_max)
            logger.info(f"🔊 Volume: {self.current_volume} -> {new_vol}")
            self.tv_client.publish(self.tv_topic("platform_service", "changevolume"), str(new_vol))
            
        elif "button/volume_down" in topic:
            new_vol = max(self.current_volume - self.volume_step, 0)
            logger.info(f"🔉 Volume: {self.current_volume} -> {new_vol}")
            self.tv_client.publish(self.tv_topic("platform_service", "changevolume"), str(new_vol))
            
        elif "button/mute" in topic:
            logger.info("🔇 Mute")
            self.tv_client.publish(self.tv_topic("remote_service", "sendkey"), "KEY_MUTE")
        
        elif "button/power" in topic:
            logger.info("⚡ Power")
            self.tv_client.publish(self.tv_topic("remote_service", "sendkey"), "KEY_POWER")
        
        elif any(f"button/{btn[0]}" in topic for btn in self.NAV_BUTTONS):
            for btn_id, _, _, key in self.NAV_BUTTONS:
                if f"button/{btn_id}" in topic:
                    self.tv_client.publish(self.tv_topic("remote_service", "sendkey"), key)
                    break
        
        elif any(f"button/{btn[0]}" in topic for btn in self.MEDIA_BUTTONS):
            for btn_id, _, _, key in self.MEDIA_BUTTONS:
                if f"button/{btn_id}" in topic:
                    self.tv_client.publish(self.tv_topic("remote_service", "sendkey"), key)
                    break
        
        elif "volume/set" in topic:
            try:
                new_vol = max(0, min(self.volume_max, int(float(payload))))
                logger.info(f"🎚️ Volume: {new_vol}")
                self.tv_client.publish(self.tv_topic("platform_service", "changevolume"), str(new_vol))
            except ValueError:
                pass
        
        elif "source/set" in topic:
            if payload in self.SOURCE_MAP:
                logger.info(f"📺 Source: {payload}")
                self.tv_client.publish(
                    self.tv_topic("ui_service", "changesource"),
                    json.dumps(self.SOURCE_MAP[payload])
                )
    
    def register_entities(self):
        device = self.device_info()
        
        self.ha_client.publish(f"homeassistant/select/{self.device_id}_source/config", json.dumps({
            "name": "Source", "unique_id": f"{self.device_id}_source",
            "command_topic": f"{self.topic_prefix}/source/set",
            "state_topic": f"{self.topic_prefix}/source",
            "options": self.SOURCES, "icon": "mdi:video-input-hdmi",
            "availability_topic": f"{self.topic_prefix}/available", "device": device
        }), retain=True)
        
        self.ha_client.publish(f"homeassistant/number/{self.device_id}_volume/config", json.dumps({
            "name": "Volume", "unique_id": f"{self.device_id}_volume",
            "command_topic": f"{self.topic_prefix}/volume/set",
            "state_topic": f"{self.topic_prefix}/volume",
            "min": 0, "max": self.volume_max, "step": 1, "icon": "mdi:volume-high",
            "availability_topic": f"{self.topic_prefix}/available", "device": device
        }), retain=True)
        
        for btn_id, name, icon in [("volume_up", "Volume Up", "mdi:volume-plus"),
                                    ("volume_down", "Volume Down", "mdi:volume-minus"),
                                    ("mute", "Mute", "mdi:volume-mute"),
                                    ("power", "Power", "mdi:power")]:
            self.ha_client.publish(f"homeassistant/button/{self.device_id}_{btn_id}/config", json.dumps({
                "name": name, "unique_id": f"{self.device_id}_{btn_id}",
                "command_topic": f"{self.topic_prefix}/button/{btn_id}",
                "icon": icon, "availability_topic": f"{self.topic_prefix}/available", "device": device
            }), retain=True)
        
        for btn_id, name, icon, _ in self.NAV_BUTTONS + self.MEDIA_BUTTONS:
            self.ha_client.publish(f"homeassistant/button/{self.device_id}_{btn_id}/config", json.dumps({
                "name": name, "unique_id": f"{self.device_id}_{btn_id}",
                "command_topic": f"{self.topic_prefix}/button/{btn_id}",
                "icon": icon, "availability_topic": f"{self.topic_prefix}/available", "device": device
            }), retain=True)
    
    def publish_ha_state(self):
        if self.ha_client:
            self.ha_client.publish(f"{self.topic_prefix}/volume", str(self.current_volume), retain=True)
            if self.current_source:
                self.ha_client.publish(f"{self.topic_prefix}/source", self.current_source, retain=True)
    
    def start(self):
        logger.info(f"🚀 Hisense TV Bridge v{__version__}")
        
        self.tv_client = mqtt.Client(
            client_id=self.tv_client_id, protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.tv_client.username_pw_set("hisenseservice", "multimqttservice")
        self.tv_client.tls_set(certfile=self.cert_file, keyfile=self.key_file, cert_reqs=ssl.CERT_NONE)
        self.tv_client.tls_insecure_set(True)
        self.tv_client.on_connect = self.on_tv_connect
        self.tv_client.on_message = self.on_tv_message
        
        self.ha_client = mqtt.Client(
            client_id=f"HisenseBridge_{self.device_id}", protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        if self.ha_user:
            self.ha_client.username_pw_set(self.ha_user, self.ha_pass)
        self.ha_client.on_connect = self.on_ha_connect
        self.ha_client.on_message = self.on_ha_message
        
        logger.info(f"🔄 Connecting to TV at {self.tv_ip}...")
        try:
            self.tv_client.connect(self.tv_ip, self.tv_port, 60)
            self.tv_client.loop_start()
        except Exception as e:
            logger.error(f"❌ TV connection failed: {e}")
            sys.exit(1)
        
        time.sleep(2)
        
        logger.info(f"🔄 Connecting to MQTT at {self.ha_host}...")
        try:
            self.ha_client.connect(self.ha_host, self.ha_port, 60)
            self.ha_client.loop_start()
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
            sys.exit(1)
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("✅ Bridge running! Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        logger.info("\n👋 Stopping...")
        if self.ha_client:
            self.ha_client.publish(f"{self.topic_prefix}/available", "offline", retain=True)
            time.sleep(0.5)
            self.ha_client.loop_stop()
        if self.tv_client:
            self.tv_client.loop_stop()
        logger.info("✅ Stopped")


def main():
    parser = argparse.ArgumentParser(description="Hisense TV MQTT Bridge")
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--debug', action='store_true', help='Debug logging')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.setup:
        run_setup()
        return
    
    config_path = get_config_path()
    if not os.path.exists(config_path):
        print("❌ No configuration found!")
        print(f"\nRun: python3 {os.path.basename(__file__)} --setup")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        bridge = HisenseBridge(config)
        bridge.start()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
