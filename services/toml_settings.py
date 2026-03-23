import re
from pathlib import Path
from config import VPN_TOML, HOSTS_TOML, RULES_TOML, logger


VPN_SCHEMA = {
    "listen_address": {"type": "str", "default": "0.0.0.0:443"},
    "ipv6_available": {"type": "bool", "default": True},
    "allow_private_network_connections": {"type": "bool", "default": False},
    "tls_handshake_timeout_secs": {"type": "int", "default": 10, "min": 1, "max": 120},
    "client_listener_timeout_secs": {"type": "int", "default": 600, "min": 10, "max": 86400},
    "connection_establishment_timeout_secs": {"type": "int", "default": 30, "min": 1, "max": 300},
    "tcp_connections_timeout_secs": {"type": "int", "default": 604800, "min": 60, "max": 2592000},
    "udp_connections_timeout_secs": {"type": "int", "default": 300, "min": 10, "max": 86400},
    "speedtest_enable": {"type": "bool", "default": False},
    "speedtest_path": {"type": "str", "default": "/speedtest"},
    "ping_enable": {"type": "bool", "default": False},
    "ping_path": {"type": "str", "default": "/ping"},
    "auth_failure_status_code": {"type": "int", "default": 407, "options": [407, 405]},
}

HTTP2_SCHEMA = {
    "initial_connection_window_size": {"type": "int", "default": 8388608, "min": 65535, "max": 2147483647},
    "initial_stream_window_size": {"type": "int", "default": 131072, "min": 65535, "max": 2147483647},
    "max_concurrent_streams": {"type": "int", "default": 1000, "min": 1, "max": 100000},
    "max_frame_size": {"type": "int", "default": 16384, "min": 16384, "max": 16777215},
    "header_table_size": {"type": "int", "default": 65536, "min": 0, "max": 1048576},
}

QUIC_SCHEMA = {
    "recv_udp_payload_size": {"type": "int", "default": 1350, "min": 1200, "max": 65535},
    "send_udp_payload_size": {"type": "int", "default": 1350, "min": 1200, "max": 65535},
    "initial_max_data": {"type": "int", "default": 104857600, "min": 1048576, "max": 1073741824},
    "initial_max_streams_bidi": {"type": "int", "default": 4096, "min": 1, "max": 100000},
    "initial_max_streams_uni": {"type": "int", "default": 4096, "min": 1, "max": 100000},
    "disable_active_migration": {"type": "bool", "default": True},
    "enable_early_data": {"type": "bool", "default": True},
}

METRICS_SCHEMA = {
    "address": {"type": "str", "default": "127.0.0.1:1987"},
    "request_timeout_secs": {"type": "int", "default": 3, "min": 1, "max": 60},
}


def _parse_toml_file(path: Path):
    if not path.exists():
        return {}
    import sys
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            with open(path, "rb") as f:
                return tomllib.load(f)
        else:
            raise ImportError
    except ImportError:
        return _manual_parse(path.read_text())


def _manual_parse(text):
    result = {}
    current_section = result
    current_key = None
    array_key = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = re.match(r'^\[\[(\S+)\]\]$', stripped)
        if m:
            array_key = m.group(1)
            result.setdefault(array_key, [])
            entry = {}
            result[array_key].append(entry)
            current_section = entry
            continue

        m = re.match(r'^\[(\S+)\]$', stripped)
        if m:
            array_key = None
            keys = m.group(1).split(".")
            current_section = result
            for k in keys:
                current_section = current_section.setdefault(k, {})
            continue

        m = re.match(r'^(\w+)\s*=\s*(.+)$', stripped)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            current_section[key] = _parse_value(val)

    return result


def _parse_value(val):
    if val in ("true", "false"):
        return val == "true"
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val == "[]":
        return []
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        items = []
        for item in inner.split(","):
            items.append(_parse_value(item.strip()))
        return items
    if val == "{}":
        return {}
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def parse_vpn_structured():
    data = _parse_toml_file(VPN_TOML)
    result = {"core": {}, "http2": {}, "quic": {}, "metrics": {}, "forward": "direct", "socks5_address": ""}

    for key, schema in VPN_SCHEMA.items():
        result["core"][key] = data.get(key, schema["default"])

    lp = data.get("listen_protocols", {})
    h2 = lp.get("http2", {})
    for key, schema in HTTP2_SCHEMA.items():
        result["http2"][key] = h2.get(key, schema["default"])

    quic = lp.get("quic", {})
    for key, schema in QUIC_SCHEMA.items():
        result["quic"][key] = quic.get(key, schema["default"])

    met = data.get("metrics", {})
    for key, schema in METRICS_SCHEMA.items():
        result["metrics"][key] = met.get(key, schema["default"])

    fp = data.get("forward_protocol", {})
    if "socks5" in fp:
        result["forward"] = "socks5"
        result["socks5_address"] = fp["socks5"].get("address", "")

    return result


def parse_hosts_structured():
    data = _parse_toml_file(HOSTS_TOML)
    result = {
        "main_hosts": data.get("main_hosts", []),
        "ping_hosts": data.get("ping_hosts", []),
        "speedtest_hosts": data.get("speedtest_hosts", []),
        "reverse_proxy_hosts": data.get("reverse_proxy_hosts", []),
    }
    for key in result:
        if isinstance(result[key], list):
            result[key] = [{"hostname": h.get("hostname", ""), "cert_chain_path": h.get("cert_chain_path", ""), "private_key_path": h.get("private_key_path", "")} for h in result[key]]
    return result


def parse_rules_structured():
    data = _parse_toml_file(RULES_TOML)
    rules = data.get("rule", [])
    return [{"cidr": r.get("cidr", ""), "client_random_prefix": r.get("client_random_prefix", ""), "action": r.get("action", "allow")} for r in rules]


def save_vpn_structured(settings):
    VPN_TOML_BAK = VPN_TOML.with_suffix(".toml.bak")
    if VPN_TOML.exists():
        VPN_TOML_BAK.write_text(VPN_TOML.read_text())

    core = settings.get("core", {})
    http2 = settings.get("http2", {})
    quic = settings.get("quic", {})
    metrics = settings.get("metrics", {})
    forward = settings.get("forward", "direct")
    socks5_addr = settings.get("socks5_address", "")

    lines = []

    for key, schema in VPN_SCHEMA.items():
        val = core.get(key, schema["default"])
        if key in ("credentials_file", "rules_file"):
            continue
        lines.append(_fmt_kv(key, val, schema))

    lines.append("")

    existing = _parse_toml_file(VPN_TOML) if VPN_TOML.exists() else {}
    creds = existing.get("credentials_file")
    rules_f = existing.get("rules_file")
    if creds:
        lines.append('credentials_file = "%s"' % creds)
    if rules_f:
        lines.append('rules_file = "%s"' % rules_f)

    lines.append("")
    lines.append("[listen_protocols.http2]")
    for key, schema in HTTP2_SCHEMA.items():
        val = http2.get(key, schema["default"])
        lines.append(_fmt_kv(key, val, schema))

    lines.append("")
    lines.append("[listen_protocols.quic]")
    for key, schema in QUIC_SCHEMA.items():
        val = quic.get(key, schema["default"])
        lines.append(_fmt_kv(key, val, schema))

    lines.append("")
    if forward == "socks5" and socks5_addr:
        lines.append("[forward_protocol.socks5]")
        lines.append('address = "%s"' % socks5_addr)
    else:
        lines.append("[forward_protocol]")
        lines.append("direct = {}")

    lines.append("")
    lines.append("[metrics]")
    for key, schema in METRICS_SCHEMA.items():
        val = metrics.get(key, schema["default"])
        lines.append(_fmt_kv(key, val, schema))

    lines.append("")
    VPN_TOML.write_text("\n".join(lines))


def _esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def save_rules_structured(rules):
    RULES_BAK = RULES_TOML.with_suffix(".toml.bak")
    if RULES_TOML.exists():
        RULES_BAK.write_text(RULES_TOML.read_text())

    lines = []
    for r in rules:
        lines.append("[[rule]]")
        if r.get("cidr"):
            lines.append('cidr = "%s"' % _esc(r["cidr"]))
        if r.get("client_random_prefix"):
            lines.append('client_random_prefix = "%s"' % _esc(r["client_random_prefix"]))
        action = r.get("action", "allow")
        if action not in ("allow", "deny"):
            action = "allow"
        lines.append('action = "%s"' % action)
        lines.append("")

    RULES_TOML.write_text("\n".join(lines))


def _fmt_kv(key, val, schema):
    if schema["type"] == "bool":
        return "%s = %s" % (key, "true" if val else "false")
    elif schema["type"] == "int":
        mn = schema.get("min")
        mx = schema.get("max")
        try:
            v = int(val)
        except (ValueError, TypeError):
            v = schema["default"]
        if mn is not None:
            v = max(mn, v)
        if mx is not None:
            v = min(mx, v)
        return "%s = %d" % (key, v)
    else:
        return '%s = "%s"' % (key, _esc(str(val)))


def get_schema():
    return {
        "vpn": VPN_SCHEMA,
        "http2": HTTP2_SCHEMA,
        "quic": QUIC_SCHEMA,
        "metrics": METRICS_SCHEMA,
    }
