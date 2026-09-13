import ipaddress
import os
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
    # 404/403 accepted since endpoint 1.0.41 (was 407/405 only).
    "auth_failure_status_code": {"type": "int", "default": 407, "options": [407, 405, 404, 403]},
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
    # Endpoint 1.1.0+: adds per-user metric series and the /clients JSON
    # endpoint. Exposes usernames and client IPs, so keep the metrics listener
    # on loopback when enabling it.
    "per_client_metrics": {"type": "bool", "default": False},
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


def _is_table_array(v):
    return isinstance(v, list) and len(v) > 0 and all(isinstance(x, dict) for x in v)


def _toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    return '"%s"' % _esc(v)


def _dump_toml(data, prefix=""):
    """Serialize a parsed-TOML dict back to text, preserving every key and table."""
    lines = []
    tables = []
    for k, v in data.items():
        if isinstance(v, dict) or _is_table_array(v):
            tables.append((k, v))
        else:
            lines.append("%s = %s" % (k, _toml_value(v)))
    for k, v in tables:
        path = "%s.%s" % (prefix, k) if prefix else k
        if _is_table_array(v):
            for entry in v:
                lines.append("")
                lines.append("[[%s]]" % path)
                lines.extend(_dump_toml(entry, path))
        else:
            lines.append("")
            lines.append("[%s]" % path)
            lines.extend(_dump_toml(v, path))
    return lines


def _coerce(val, schema):
    if schema["type"] == "bool":
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("true", "1", "yes", "on")
    if schema["type"] == "int":
        try:
            v = int(val)
        except (ValueError, TypeError):
            return schema["default"]
        if "options" in schema and v not in schema["options"]:
            return schema["default"]
        mn, mx = schema.get("min"), schema.get("max")
        if mn is not None:
            v = max(mn, v)
        if mx is not None:
            v = min(mx, v)
        return v
    return str(val)


_HOSTPORT_RE = re.compile(r'^(\[[0-9A-Fa-f:]+\]|[A-Za-z0-9._-]+):(\d{1,5})$')


def validate_host_port(value: str) -> str:
    """Accept only host:port / [v6]:port. Rejects anything that could inject TOML."""
    v = str(value).strip()
    m = _HOSTPORT_RE.match(v)
    if not m:
        raise ValueError("expected host:port, got %r" % value)
    port = int(m.group(2))
    if not (1 <= port <= 65535):
        raise ValueError("port out of range: %d" % port)
    return v


def _atomic_write_text(path: Path, text: str, mode: int = 0o600):
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    os.replace(str(tmp), str(path))
    try:
        os.chmod(str(path), mode)
    except OSError:
        pass


def _backup(path: Path):
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        _atomic_write_text(bak, path.read_text())


def save_vpn_structured(settings):
    """Merge the edited values into the existing vpn.toml.

    The panel only models a subset of TrustTunnel's options, so the file is
    updated in place rather than regenerated — otherwise sections the UI does not
    know about ([icmp], [listen_protocols.http1], the extended QUIC tuning …)
    would be silently dropped.
    """
    _backup(VPN_TOML)
    data = _parse_toml_file(VPN_TOML) if VPN_TOML.exists() else {}

    core = settings.get("core") or {}
    for key, schema in VPN_SCHEMA.items():
        if key in core:
            data[key] = _coerce(core[key], schema)

    lp = data.setdefault("listen_protocols", {})
    for section, schema_map in (("http2", HTTP2_SCHEMA), ("quic", QUIC_SCHEMA)):
        incoming = settings.get(section) or {}
        target = lp.setdefault(section, {})
        for key, schema in schema_map.items():
            if key in incoming:
                target[key] = _coerce(incoming[key], schema)

    metrics_in = settings.get("metrics") or {}
    metrics = data.setdefault("metrics", {})
    for key, schema in METRICS_SCHEMA.items():
        if key not in metrics_in:
            continue
        if key == "address":
            metrics[key] = validate_host_port(metrics_in[key])
        else:
            metrics[key] = _coerce(metrics_in[key], schema)

    forward = settings.get("forward")
    if forward == "socks5":
        data["forward_protocol"] = {"socks5": {"address": validate_host_port(settings.get("socks5_address", ""))}}
    elif forward == "direct":
        data["forward_protocol"] = {"direct": {}}

    _atomic_write_text(VPN_TOML, "\n".join(_dump_toml(data)).lstrip("\n") + "\n")


def _esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def validate_cidr(value: str) -> str:
    v = str(value).strip()
    # strict=False so 10.0.0.5/24 is accepted and normalised rather than rejected
    return str(ipaddress.ip_network(v, strict=False))


_HEXPREFIX_RE = re.compile(r'^[0-9A-Fa-f]{1,64}$')


def save_rules_structured(rules):
    _backup(RULES_TOML)

    lines = []
    for idx, r in enumerate(rules):
        cidr = str(r.get("cidr", "")).strip()
        prefix = str(r.get("client_random_prefix", "")).strip()
        if not cidr and not prefix:
            continue
        if cidr:
            try:
                cidr = validate_cidr(cidr)
            except ValueError as e:
                raise ValueError("rule %d: invalid CIDR %r (%s)" % (idx + 1, r.get("cidr"), e))
        if prefix and not _HEXPREFIX_RE.match(prefix):
            raise ValueError("rule %d: client_random_prefix must be hex" % (idx + 1))
        action = r.get("action", "allow")
        if action not in ("allow", "deny"):
            action = "allow"
        lines.append("[[rule]]")
        if cidr:
            lines.append('cidr = "%s"' % _esc(cidr))
        if prefix:
            lines.append('client_random_prefix = "%s"' % _esc(prefix))
        lines.append('action = "%s"' % action)
        lines.append("")

    _atomic_write_text(RULES_TOML, "\n".join(lines))


def get_schema():
    return {
        "vpn": VPN_SCHEMA,
        "http2": HTTP2_SCHEMA,
        "quic": QUIC_SCHEMA,
        "metrics": METRICS_SCHEMA,
    }
