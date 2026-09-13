import ipaddress
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
from auth import load_panel_db, save_panel_db, update_panel_db

# hostname[:port] or [v6addr][:port] — anything else is rejected before it can
# reach a config file or a generated shell script.
_ADDRESS_RE = re.compile(
    r'^(?:\[[0-9A-Fa-f:]+\]|[A-Za-z0-9](?:[A-Za-z0-9._-]{0,251}[A-Za-z0-9])?)'
    r'(?::(?P<port>\d{1,5}))?$')
_HOSTNAME_RE = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,251}[A-Za-z0-9])?$')
MAX_ADDRESSES = 8
# Client default since v1.1.5 (raised from 1280 to reduce QUIC fragmentation).
DEFAULT_MTU = 1350


def _split_host(address: str) -> str:
    a = str(address).strip()
    if a.startswith("["):
        end = a.find("]")
        return a[1:end] if end > 0 else ""
    return a.split(":")[0]


def validate_address(address: str) -> str:
    a = str(address).strip()
    m = _ADDRESS_RE.match(a)
    if not m:
        raise ValueError("invalid address: %r" % address)
    port = m.group("port")
    if port is not None and not (1 <= int(port) <= 65535):
        raise ValueError("port out of range in %r" % address)
    return a


def validate_hostname(hostname: str) -> str:
    h = str(hostname).strip()
    if not _HOSTNAME_RE.match(h):
        raise ValueError("invalid hostname: %r" % hostname)
    return h


def _clean_dns(values, limit=8):
    """DNS upstreams: plain IPs, ip:port, or DoH/DoT URLs. Keeps the list sane."""
    if isinstance(values, str):
        values = values.split(",")
    out = []
    for v in (values or []):
        v = str(v).strip()
        if v and len(v) <= 255 and not any(ch in v for ch in '"\\\n\r'):
            out.append(v)
    return out[:limit]


def normalize_addresses(values, hostname=""):
    """Accept a list or a comma-separated string; validate every entry."""
    if isinstance(values, str):
        values = values.split(",")
    out = []
    for v in (values or []):
        v = str(v).strip()
        if v:
            out.append(validate_address(v))
    if not out and hostname:
        out = [validate_hostname(hostname) + ":443"]
    if not out:
        raise ValueError("at least one address is required")
    if len(out) > MAX_ADDRESSES:
        raise ValueError("too many addresses (max %d)" % MAX_ADDRESSES)
    return out


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
                "certificate": data.get("certificate", ""),
                "client_random": data.get("client_random", ""),
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
    data = None
    if sys.version_info >= (3, 11):
        import tomllib
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            logger.warning("%s is not valid TOML (%s); using the lenient parser", path, e)
    if data is None:
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
    # DNS moved into [endpoint] in client v1.0.45; keep reading the legacy
    # top-level key so configs written by older panels still import.
    dns = ep.get("dns_upstreams")
    if dns is None:
        dns = data.get("dns_upstreams", [])
    return {
        "hostname": ep.get("hostname", ""),
        "addresses": ep.get("addresses", []),
        "username": ep.get("username", ""),
        "password": ep.get("password", ""),
        "upstream_protocol": ep.get("upstream_protocol", "http2"),
        "has_ipv6": ep.get("has_ipv6", True),
        "anti_dpi": ep.get("anti_dpi", False),
        "custom_sni": ep.get("custom_sni", ""),
        "certificate": ep.get("certificate", ""),
        "client_random": ep.get("client_random", ""),
        "vpn_mode": data.get("vpn_mode", "general"),
        "killswitch_enabled": data.get("killswitch_enabled", True),
        "dns_upstreams": dns,
        "exclusions": data.get("exclusions", []),
        "mtu_size": lt.get("mtu_size", data.get("mtu_size", DEFAULT_MTU)),
    }


def get_servers():
    db = load_panel_db()
    return db.get("servers", [])


def get_server(server_id):
    for s in get_servers():
        if s["id"] == server_id:
            return s
    return None


def _make_server_id(hostname, existing_ids):
    sid = re.sub(r'[^a-z0-9\-]', '', str(hostname or "").lower().replace(".", "-")).strip("-")
    if not sid:
        sid = "server"
    base = sid
    counter = 1
    while sid in existing_ids:
        sid = f"{base}-{counter}"
        counter += 1
    return sid


def add_server(data):
    hostname = validate_hostname(data.get("hostname", ""))
    addresses = normalize_addresses(data.get("addresses"), hostname)
    proto = data.get("upstream_protocol", "http2")
    if proto not in ("http2", "http3"):
        proto = "http2"
    custom_sni = data.get("custom_sni", "")
    if custom_sni:
        custom_sni = validate_hostname(custom_sni)

    def _mutate(db):
        servers = db.setdefault("servers", [])
        server = {
            "id": _make_server_id(hostname, {s["id"] for s in servers}),
            "name": str(data.get("name") or hostname)[:64],
            "priority": len(servers) + 1,
            "enabled": True,
            "hostname": hostname,
            "addresses": addresses,
            "username": str(data.get("username", ""))[:128],
            "password": str(data.get("password", ""))[:256],
            "upstream_protocol": proto,
            "has_ipv6": bool(data.get("has_ipv6", True)),
            "anti_dpi": bool(data.get("anti_dpi", False)),
            "custom_sni": custom_sni,
            # Carried from the deeplink: a self-signed endpoint is unreachable
            # without its certificate, and client_random is required when the
            # endpoint issues links with a random prefix.
            "certificate": str(data.get("certificate", "")),
            "client_random": str(data.get("client_random", "")),
            # Per-server DNS (deeplink tag 0x0D); overrides the global setting.
            "dns_upstreams": _clean_dns(data.get("dns_upstreams")),
            "added_at": datetime.now().isoformat(timespec="seconds"),
        }
        servers.append(server)
        return server, db.get("settings", {})

    server, settings = update_panel_db(_mutate)
    _generate_toml(server, settings)
    return server


def update_server(server_id, data):
    clean = {}
    if "hostname" in data:
        clean["hostname"] = validate_hostname(data["hostname"])
    if "addresses" in data:
        clean["addresses"] = normalize_addresses(data["addresses"], clean.get("hostname", ""))
    if "custom_sni" in data:
        clean["custom_sni"] = validate_hostname(data["custom_sni"]) if data["custom_sni"] else ""
    if "upstream_protocol" in data:
        clean["upstream_protocol"] = data["upstream_protocol"] if data["upstream_protocol"] in ("http2", "http3") else "http2"
    for key in ("name", "username", "password", "client_random"):
        if key in data:
            clean[key] = str(data[key])[:256]
    if "certificate" in data:
        clean["certificate"] = str(data["certificate"])[:16384]
    if "dns_upstreams" in data:
        clean["dns_upstreams"] = _clean_dns(data["dns_upstreams"])
    for key in ("has_ipv6", "anti_dpi", "enabled"):
        if key in data:
            clean[key] = bool(data[key])

    def _mutate(db):
        for s in db.get("servers", []):
            if s["id"] == server_id:
                s.update(clean)
                return dict(s), db.get("settings", {}), db.get("active_server") == server_id
        return None, None, False

    server, settings, is_active = update_panel_db(_mutate)
    if not server:
        return None
    _generate_toml(server, settings)
    if is_active:
        ok, err = _restart_service()
        if ok:
            logger.info("Active server config updated, restarted service")
        else:
            logger.error("Active server config updated but restart failed: %s", err)
            server["restart_error"] = err
    return server


def delete_server(server_id):
    def _mutate(db):
        servers = db.get("servers", [])
        remaining = [s for s in servers if s["id"] != server_id]
        if len(remaining) == len(servers):
            return None
        db["servers"] = remaining
        was_active = db.get("active_server") == server_id
        if was_active:
            db["active_server"] = ""
        return was_active, sorted(remaining, key=lambda s: s.get("priority", 999))

    outcome = update_panel_db(_mutate)
    if outcome is None:
        return False
    was_active, remaining = outcome

    toml_path = TT_CONFIGS_DIR / f"{server_id}.toml"
    if toml_path.exists():
        toml_path.unlink()

    if was_active:
        # Don't leave active-config.toml dangling at a file we just deleted.
        replacement = next((s for s in remaining if s.get("enabled", True)), None)
        if replacement:
            logger.info("Deleted the active server; switching to %s", replacement["id"])
            activate_server(replacement["id"], manual=True)
        else:
            logger.warning("Deleted the active server and none remain; stopping %s", SERVICE_NAME)
            try:
                if TT_ACTIVE_LINK.is_symlink() or TT_ACTIVE_LINK.exists():
                    TT_ACTIVE_LINK.unlink()
            except OSError as e:
                logger.error("Could not remove %s: %s", TT_ACTIVE_LINK, e)
            try:
                subprocess.run(["systemctl", "stop", SERVICE_NAME], timeout=30, capture_output=True)
            except Exception as e:
                logger.error("Could not stop %s: %s", SERVICE_NAME, e)
    return True


def reorder_servers(order):
    def _mutate(db):
        servers = db.get("servers", [])
        id_map = {s["id"]: s for s in servers}
        for i, sid in enumerate(order):
            if sid in id_map:
                id_map[sid]["priority"] = i + 1
        db["servers"] = sorted(servers, key=lambda s: s.get("priority", 999))
        return list(db["servers"]), db.get("active_server", "")

    # Reordering used to take _panel_lock and then call load_panel_db(), which
    # takes it again — a guaranteed deadlock that froze the whole panel.
    servers, current_active = update_panel_db(_mutate)

    new_primary = servers[0] if servers else None
    if not new_primary or new_primary["id"] == current_active or not new_primary.get("enabled", True):
        return {"ok": True, "activated": None}

    logger.info("Priority changed: activating new primary %s", new_primary["id"])
    result = activate_server(new_primary["id"])
    if result.get("ok"):
        return {"ok": True, "activated": new_primary["id"]}
    logger.warning("Primary %s failed (%s), trying fallback", new_primary["id"], result.get("error"))
    for s in servers[1:]:
        if s.get("enabled", True):
            fb = activate_server(s["id"])
            if fb.get("ok"):
                return {"ok": True, "activated": s["id"], "fallback": True}
    return {"ok": False, "error": result.get("error", "activation failed")}


def _restart_service():
    """Returns (ok, error_text)."""
    try:
        r = subprocess.run(["systemctl", "restart", SERVICE_NAME],
                           timeout=60, capture_output=True, text=True)
        if r.returncode == 0:
            return True, ""
        return False, (r.stderr or r.stdout or "").strip()[:300] or ("exit code %d" % r.returncode)
    except subprocess.TimeoutExpired:
        return False, "systemctl restart timed out"
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def activate_server(server_id, manual=False, _db=None):
    db = _db or load_panel_db()
    server = None
    for s in db.get("servers", []):
        if s["id"] == server_id:
            server = s
            break
    if not server:
        return {"ok": False, "error": "Server not found"}
    if not server.get("enabled", True):
        return {"ok": False, "error": "Server is disabled"}

    settings = db.get("settings", {})
    _generate_toml(server, settings)
    toml_path = TT_CONFIGS_DIR / f"{server_id}.toml"

    try:
        if TT_ACTIVE_LINK.is_symlink() or TT_ACTIVE_LINK.exists():
            TT_ACTIVE_LINK.unlink()
        TT_ACTIVE_LINK.symlink_to(toml_path)
    except Exception as e:
        return {"ok": False, "error": f"Symlink error: {e}"}

    _update_routes_script(server)

    ok, err = _restart_service()
    if not ok:
        return {"ok": False, "error": "Service restart failed: " + err}

    def _mutate(d):
        d["active_server"] = server_id
        if manual:
            d["on_backup"] = False

    update_panel_db(_mutate)
    try:
        from health import reset_external_ip_cache
        reset_external_ip_cache()
    except Exception:
        pass

    wait = settings.get("activate_timeout", 10) if manual else settings.get("failover_timeout", 5)
    for _ in range(int(wait)):
        time.sleep(1)
        if _check_tun_up():
            return {"ok": True, "message": "Connected"}

    return {"ok": not manual, "message": "Service restarted, waiting for %s" % TUN_IF,
            "error": None if not manual else "Interface %s did not come up in %ss" % (TUN_IF, wait)}


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


def _read_varint(data, offset):
    """QUIC/TLS variable-length integer (RFC 9000 §16).

    The two high bits of the first byte give the encoded length: 1, 2, 4 or 8
    bytes. Deeplink tags *and* lengths use this, so reading them as single bytes
    truncates any field longer than 63 bytes (notably the DER certificate).
    """
    if offset >= len(data):
        raise ValueError("truncated varint")
    first = data[offset]
    size = 1 << (first >> 6)
    if offset + size > len(data):
        raise ValueError("truncated varint")
    value = first & 0x3F
    for i in range(1, size):
        value = (value << 8) | data[offset + i]
    return value, offset + size


def _der_to_pem(der: bytes) -> str:
    import base64
    b64 = base64.b64encode(der).decode("ascii")
    body = "\n".join(b64[i:i + 64] for i in range(0, len(b64), 64))
    return "-----BEGIN CERTIFICATE-----\n%s\n-----END CERTIFICATE-----\n" % body


def _decode_string_array(value):
    out = []
    offset = 0
    while offset < len(value):
        length, offset = _read_varint(value, offset)
        if offset + length > len(value):
            raise ValueError("truncated string array")
        out.append(value[offset:offset + length].decode("utf-8", "replace"))
        offset += length
    return out


def _parse_deeplink_binary(payload):
    import base64
    pad = "=" * (-len(payload) % 4)
    try:
        data = base64.urlsafe_b64decode(payload + pad)
    except Exception:
        return None

    result = {"hostname": "", "addresses": [], "username": "", "password": "",
              "has_ipv6": True, "skip_verification": False, "upstream_protocol": "http2",
              "anti_dpi": False, "custom_sni": "", "name": "", "dns_upstreams": [],
              "certificate": "", "client_random": ""}

    offset = 0
    try:
        while offset < len(data):
            tag, offset = _read_varint(data, offset)
            length, offset = _read_varint(data, offset)
            if offset + length > len(data):
                raise ValueError("truncated value for tag 0x%02x" % tag)
            value = data[offset:offset + length]
            offset += length
            txt = value.decode("utf-8", "replace")

            if tag == 0x01:
                result["hostname"] = txt
            elif tag == 0x02:
                result["addresses"].append(txt)
            elif tag == 0x03:
                result["custom_sni"] = txt
            elif tag == 0x04:
                result["has_ipv6"] = bool(value and value[0])
            elif tag == 0x05:
                result["username"] = txt
            elif tag == 0x06:
                result["password"] = txt
            elif tag == 0x07:
                # Parsed for completeness; the panel always writes
                # skip_verification = false and never honours this flag.
                result["skip_verification"] = bool(value and value[0])
            elif tag == 0x09:
                if value:
                    result["upstream_protocol"] = "http3" if value[0] == 0x02 else "http2"
            elif tag == 0x0A:
                result["anti_dpi"] = bool(value and value[0])
            elif tag == 0x08:
                # DER certificate for a self-signed endpoint. Dropping it made
                # such servers fail TLS verification after import.
                result["certificate"] = _der_to_pem(value)
            elif tag == 0x0B:
                # Maps to [endpoint].client_random; required to connect when the
                # endpoint was set up with --generate-client-random-prefix.
                result["client_random"] = txt
            elif tag == 0x0C:
                result["name"] = txt
            elif tag == 0x0D:
                result["dns_upstreams"] = _decode_string_array(value)
            # 0x00 version: informational only
    except (ValueError, IndexError) as e:
        logger.warning("Deeplink parse failed: %s", e)
        return None

    if not result["hostname"]:
        return None
    if not result["addresses"]:
        result["addresses"] = [result["hostname"] + ":443"]
    if not result["name"]:
        result["name"] = result["hostname"]
    return result


def parse_deeplink(link):
    link = link.strip()
    if not link.startswith("tt://"):
        return None

    payload = link[5:]
    if payload.startswith("?"):
        payload = payload[1:]

    # trusttunnel_client has no --parse-deeplink flag (only -v/-s/-c/-l/-h), so
    # there is no binary to fall back to: our TLV decoder is the parser.
    return _parse_deeplink_binary(payload)


def _esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _generate_toml(server, settings):
    TT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    toml_path = TT_CONFIGS_DIR / f"{server['id']}.toml"
    vpn_mode = settings.get("vpn_mode", "general")
    if vpn_mode not in ("general", "selective"):
        vpn_mode = "general"
    killswitch = settings.get("killswitch_enabled", True)
    # A deeplink can carry per-server DNS (tag 0x0D); it wins over the global
    # setting, which stays the fallback.
    dns = server.get("dns_upstreams") or settings.get("dns_upstreams", [])
    exclusions = settings.get("exclusions", [])
    mtu = max(1200, min(int(settings.get("mtu_size", DEFAULT_MTU)), 9000))

    addrs = server.get("addresses", [])
    addr_str = ", ".join(f'"{_esc(a)}"' for a in addrs)
    excl_str = ", ".join(f'"{_esc(e)}"' for e in exclusions)
    # Emit the key only when non-empty: an explicit empty array means "no DNS
    # upstreams" to the client, which is not the same as leaving it unset.
    dns_line = ""
    if dns:
        dns_line = "dns_upstreams = [%s]\n" % ", ".join(f'"{_esc(d)}"' for d in dns)
    proto = server.get('upstream_protocol', 'http2')
    if proto not in ('http2', 'http3'):
        proto = 'http2'

    content = f'''loglevel = "info"
vpn_mode = "{vpn_mode}"
killswitch_enabled = {"true" if killswitch else "false"}
killswitch_allow_ports = []
post_quantum_group_enabled = true
exclusions = [{excl_str}]

[endpoint]
hostname = "{_esc(server['hostname'])}"
addresses = [{addr_str}]
custom_sni = "{_esc(server.get('custom_sni', ''))}"
has_ipv6 = {"true" if server.get('has_ipv6', True) else "false"}
username = "{_esc(server['username'])}"
password = "{_esc(server['password'])}"
client_random = "{_esc(server.get('client_random', ''))}"
skip_verification = false
certificate = "{_esc(server.get('certificate', ''))}"
upstream_protocol = "{proto}"
anti_dpi = {"true" if server.get('anti_dpi', False) else "false"}
# Since client v1.0.45 DNS lives here; a top-level dns_upstreams is legacy and
# is ignored outright once this key exists, so it must not be duplicated above.
{dns_line}
[listener]

[listener.tun]
bound_if = ""
# Pin the interface name: without it the kernel picks one (tun1 if tun0 is
# taken) and the health check, routes script and TUN_IF config all break.
device_name = "{_esc(TUN_IF)}"
included_routes = ["0.0.0.0/0", "2000::/3"]
excluded_routes = ["0.0.0.0/8", "10.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16", "224.0.0.0/3"]
mtu_size = {mtu}
change_system_dns = false
'''
    tmp = toml_path.with_suffix(".tmp")
    tmp.write_text(content)
    os.chmod(str(tmp), 0o600)
    os.replace(str(tmp), str(toml_path))
    logger.info("Generated config: %s", toml_path)


def _server_endpoint_ip(server):
    """Resolve the server's endpoint to a literal IP address.

    The result is interpolated into a root-executed shell script, so it must be a
    validated IP and never raw user input.
    """
    first = (server.get("addresses") or [""])[0]
    host = _split_host(first)
    if not host:
        return None
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    try:
        return str(ipaddress.ip_address(socket.gethostbyname(host)))
    except (socket.gaierror, ValueError, OSError) as e:
        logger.error("Cannot resolve %r to an IP address: %s", host, e)
        return None


def _update_routes_script(server):
    ip = _server_endpoint_ip(server)
    if not ip:
        logger.error("Skipping routes script update for %s: no usable endpoint IP", server.get("id"))
        return False

    content = f'''#!/bin/bash
sleep 5
ip route add {ip} via {LAN_GATEWAY} dev {GATEWAY_IF} 2>/dev/null
ip route del default via {LAN_GATEWAY} 2>/dev/null
ip route add default dev {TUN_IF} 2>/dev/null
ip route add {LAN_NETWORK} via {LAN_GATEWAY} dev {GATEWAY_IF} 2>/dev/null
exit 0
'''
    SETUP_ROUTES_SH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETUP_ROUTES_SH.with_suffix(".tmp")
    tmp.write_text(content)
    os.chmod(str(tmp), 0o755)
    os.replace(str(tmp), str(SETUP_ROUTES_SH))
    logger.info("Updated routes script for %s (%s)", server.get("hostname"), ip)
    return True


def _check_tun_up():
    try:
        result = subprocess.run(
            ["ip", "link", "show", TUN_IF],
            capture_output=True, text=True, timeout=5
        )
        return "UP" in result.stdout
    except Exception:
        return False
