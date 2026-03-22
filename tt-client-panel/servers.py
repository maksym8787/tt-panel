import os
import re
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from config import (
    TT_CONFIGS_DIR, TT_ACTIVE_LINK, TT_CLIENT_BIN, SETUP_ROUTES_SH,
    SERVICE_NAME, GATEWAY_IF, TUN_IF, LAN_GATEWAY, LAN_NETWORK, logger,
)
from auth import load_panel_db, save_panel_db


def import_existing_configs():
    db = load_panel_db()
    if db.get("servers"):
        return
    if not TT_CONFIGS_DIR.exists():
        return
    imported = 0
    active_target = None
    if TT_ACTIVE_LINK.is_symlink():
        active_target = TT_ACTIVE_LINK.resolve().name.replace(".toml", "")
    for toml_file in sorted(TT_CONFIGS_DIR.glob("*.toml")):
        try:
            data = _parse_existing_toml(toml_file)
            if not data.get("hostname"):
                continue
            sid = toml_file.stem
            server = {
                "id": sid,
                "name": data.get("hostname", sid),
                "priority": imported + 1,
                "enabled": True,
                "hostname": data.get("hostname", ""),
                "addresses": data.get("addresses", []),
                "username": data.get("username", ""),
                "password": data.get("password", ""),
                "upstream_protocol": data.get("upstream_protocol", "http2"),
                "has_ipv6": data.get("has_ipv6", True),
                "anti_dpi": data.get("anti_dpi", False),
                "custom_sni": data.get("custom_sni", ""),
                "added_at": datetime.now().isoformat(timespec="seconds"),
            }
            db.setdefault("servers", []).append(server)
            if active_target and sid == active_target:
                db["active_server"] = sid
            imported += 1
            logger.info("Imported existing config: %s (%s)", sid, data.get("hostname"))
        except Exception as e:
            logger.warning("Failed to import %s: %s", toml_file, e)
    if imported > 0:
        settings = db.get("settings", {})
        ep_data = _parse_existing_toml(TT_ACTIVE_LINK.resolve()) if TT_ACTIVE_LINK.is_symlink() else {}
        if ep_data.get("vpn_mode"):
            settings["vpn_mode"] = ep_data["vpn_mode"]
        if "killswitch_enabled" in ep_data:
            settings["killswitch_enabled"] = ep_data["killswitch_enabled"]
        if ep_data.get("dns_upstreams"):
            settings["dns_upstreams"] = ep_data["dns_upstreams"]
        if ep_data.get("exclusions"):
            settings["exclusions"] = ep_data["exclusions"]
        if ep_data.get("mtu_size"):
            settings["mtu_size"] = ep_data["mtu_size"]
        db["settings"] = settings
        save_panel_db(db)
        logger.info("Imported %d existing server(s), active: %s", imported, db.get("active_server", "none"))


def _parse_existing_toml(path):
    import sys
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            with open(path, "rb") as f:
                data = tomllib.load(f)
        else:
            raise ImportError
    except (ImportError, Exception):
        data = {}
        current = data
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "[endpoint]":
                data.setdefault("endpoint", {})
                current = data["endpoint"]
                continue
            if stripped.startswith("[listener"):
                current = {}
                continue
            if stripped.startswith("["):
                current = {}
                continue
            if "=" in stripped:
                k, v = stripped.split("=", 1)
                k = k.strip()
                v = v.strip()
                if v in ("true", "false"):
                    current[k] = v == "true"
                elif v.startswith('"') and v.endswith('"'):
                    current[k] = v[1:-1]
                elif v.startswith("[") and v.endswith("]"):
                    inner = v[1:-1].strip()
                    if not inner:
                        current[k] = []
                    else:
                        current[k] = [x.strip().strip('"') for x in inner.split(",")]
                else:
                    try:
                        current[k] = int(v)
                    except ValueError:
                        current[k] = v
    ep = data.get("endpoint", {})
    lt = data.get("listener", {}).get("tun", {})
    return {
        "hostname": ep.get("hostname", ""),
        "addresses": ep.get("addresses", []),
        "username": ep.get("username", ""),
        "password": ep.get("password", ""),
        "upstream_protocol": ep.get("upstream_protocol", "http2"),
        "has_ipv6": ep.get("has_ipv6", True),
        "anti_dpi": ep.get("anti_dpi", False),
        "custom_sni": ep.get("custom_sni", ""),
        "vpn_mode": data.get("vpn_mode", "general"),
        "killswitch_enabled": data.get("killswitch_enabled", True),
        "dns_upstreams": data.get("dns_upstreams", []),
        "exclusions": data.get("exclusions", []),
        "mtu_size": lt.get("mtu_size", data.get("mtu_size", 1280)),
    }


def get_servers():
    db = load_panel_db()
    return db.get("servers", [])


def get_server(server_id):
    for s in get_servers():
        if s["id"] == server_id:
            return s
    return None


def add_server(data):
    db = load_panel_db()
    servers = db.get("servers", [])
    sid = re.sub(r'[^a-z0-9\-]', '', data.get("hostname", "unknown").lower().replace(".", "-"))
    base = sid
    counter = 1
    existing_ids = {s["id"] for s in servers}
    while sid in existing_ids:
        sid = f"{base}-{counter}"
        counter += 1
    server = {
        "id": sid,
        "name": data.get("name", data.get("hostname", sid)),
        "priority": len(servers) + 1,
        "enabled": True,
        "hostname": data.get("hostname", ""),
        "addresses": data.get("addresses", [data.get("hostname", "") + ":443"]),
        "username": data.get("username", ""),
        "password": data.get("password", ""),
        "upstream_protocol": data.get("upstream_protocol", "http2"),
        "has_ipv6": data.get("has_ipv6", True),
        "anti_dpi": data.get("anti_dpi", False),
        "custom_sni": data.get("custom_sni", ""),
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }
    servers.append(server)
    db["servers"] = servers
    save_panel_db(db)
    _generate_toml(server, db.get("settings", {}))
    return server


def update_server(server_id, data):
    db = load_panel_db()
    servers = db.get("servers", [])
    for s in servers:
        if s["id"] == server_id:
            for key in ["name", "hostname", "addresses", "username", "password",
                        "upstream_protocol", "has_ipv6", "anti_dpi", "custom_sni", "enabled"]:
                if key in data:
                    s[key] = data[key]
            db["servers"] = servers
            save_panel_db(db)
            _generate_toml(s, db.get("settings", {}))
            return s
    return None


def delete_server(server_id):
    db = load_panel_db()
    servers = db.get("servers", [])
    new_servers = [s for s in servers if s["id"] != server_id]
    if len(new_servers) == len(servers):
        return False
    db["servers"] = new_servers
    if db.get("active_server") == server_id:
        db["active_server"] = ""
    save_panel_db(db)
    toml_path = TT_CONFIGS_DIR / f"{server_id}.toml"
    if toml_path.exists():
        toml_path.unlink()
    return True


def reorder_servers(order):
    db = load_panel_db()
    servers = db.get("servers", [])
    id_map = {s["id"]: s for s in servers}
    for i, sid in enumerate(order):
        if sid in id_map:
            id_map[sid]["priority"] = i + 1
    db["servers"] = sorted(servers, key=lambda s: s.get("priority", 999))
    save_panel_db(db)


def activate_server(server_id):
    db = load_panel_db()
    server = None
    for s in db.get("servers", []):
        if s["id"] == server_id:
            server = s
            break
    if not server:
        return {"ok": False, "error": "Server not found"}
    if not server.get("enabled", True):
        return {"ok": False, "error": "Server is disabled"}

    _generate_toml(server, db.get("settings", {}))
    toml_path = TT_CONFIGS_DIR / f"{server_id}.toml"

    try:
        if TT_ACTIVE_LINK.is_symlink() or TT_ACTIVE_LINK.exists():
            TT_ACTIVE_LINK.unlink()
        TT_ACTIVE_LINK.symlink_to(toml_path)
    except Exception as e:
        return {"ok": False, "error": f"Symlink error: {e}"}

    _update_routes_script(server)

    try:
        subprocess.run(["systemctl", "restart", SERVICE_NAME], timeout=10)
    except Exception as e:
        return {"ok": False, "error": f"Service restart error: {e}"}

    db["active_server"] = server_id
    save_panel_db(db)

    for _ in range(15):
        time.sleep(1)
        if _check_tun_up():
            return {"ok": True, "message": "Connected"}

    return {"ok": True, "message": "Service restarted, waiting for tun0"}


def get_active_server_id():
    db = load_panel_db()
    return db.get("active_server", "")


def get_next_failover_server(current_id):
    db = load_panel_db()
    servers = sorted(db.get("servers", []), key=lambda s: s.get("priority", 999))
    for s in servers:
        if s["id"] != current_id and s.get("enabled", True):
            return s["id"]
    return None


def parse_deeplink(link):
    link = link.strip()
    if link.startswith("tt://"):
        try:
            result = subprocess.run(
                [str(TT_CLIENT_BIN), "--parse-deeplink", link],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                return data
        except Exception:
            pass

    if link.startswith("tt://") or link.startswith("trusttunnel://"):
        import base64
        try:
            parts = link.split("://", 1)[1].split("/")
            host_port = parts[0] if parts else ""
            hostname = host_port.split(":")[0]
            return {
                "hostname": hostname,
                "addresses": [host_port if ":" in host_port else host_port + ":443"],
                "name": hostname,
            }
        except Exception:
            pass

    return None


def _generate_toml(server, settings):
    TT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    toml_path = TT_CONFIGS_DIR / f"{server['id']}.toml"
    vpn_mode = settings.get("vpn_mode", "general")
    killswitch = settings.get("killswitch_enabled", True)
    dns = settings.get("dns_upstreams", [])
    exclusions = settings.get("exclusions", [])
    mtu = settings.get("mtu_size", 1280)

    addrs = server.get("addresses", [])
    addr_str = ", ".join(f'"{a}"' for a in addrs)
    dns_str = ", ".join(f'"{d}"' for d in dns)
    excl_str = ", ".join(f'"{e}"' for e in exclusions)

    content = f'''loglevel = "info"
vpn_mode = "{vpn_mode}"
killswitch_enabled = {"true" if killswitch else "false"}
killswitch_allow_ports = []
post_quantum_group_enabled = true
exclusions = [{excl_str}]
dns_upstreams = [{dns_str}]

[endpoint]
hostname = "{server['hostname']}"
addresses = [{addr_str}]
custom_sni = "{server.get('custom_sni', '')}"
has_ipv6 = {"true" if server.get('has_ipv6', True) else "false"}
username = "{server['username']}"
password = "{server['password']}"
client_random = ""
skip_verification = false
certificate = ""
upstream_protocol = "{server.get('upstream_protocol', 'http2')}"
anti_dpi = {"true" if server.get('anti_dpi', False) else "false"}

[listener]

[listener.tun]
bound_if = ""
included_routes = ["0.0.0.0/0", "2000::/3"]
excluded_routes = ["0.0.0.0/8", "10.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16", "224.0.0.0/3"]
mtu_size = {mtu}
change_system_dns = false
'''
    toml_path.write_text(content)
    logger.info("Generated config: %s", toml_path)


def _update_routes_script(server):
    try:
        hostname = server.get("addresses", [""])[0].split(":")[0]
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = server.get("addresses", [""])[0].split(":")[0]

    content = f'''#!/bin/bash
sleep 5
ip route add {ip} via {LAN_GATEWAY} dev {GATEWAY_IF} 2>/dev/null
ip route del default via {LAN_GATEWAY} 2>/dev/null
ip route add default dev {TUN_IF} 2>/dev/null
ip route add {LAN_NETWORK} via {LAN_GATEWAY} dev {GATEWAY_IF} 2>/dev/null
exit 0
'''
    SETUP_ROUTES_SH.write_text(content)
    os.chmod(str(SETUP_ROUTES_SH), 0o755)
    logger.info("Updated routes script for %s (%s)", server["hostname"], ip)


def _check_tun_up():
    try:
        result = subprocess.run(
            ["ip", "link", "show", TUN_IF],
            capture_output=True, text=True, timeout=5
        )
        return "UP" in result.stdout
    except Exception:
        return False
