import json
import subprocess
import threading
import time
import urllib.parse
import urllib.request

from config import logger

_rdns_cache = {}
RDNS_TTL = 3600
RDNS_MAX_ENTRIES = 5000
_rdns_lock = threading.Lock()


def rdns_lookup(ip_port: str) -> str:
    ip = ip_port.split(":")[0]
    port = ip_port.split(":")[1] if ":" in ip_port else ""
    now = time.time()
    with _rdns_lock:
        cached = _rdns_cache.get(ip)
    if cached and now - cached[1] < RDNS_TTL:
        host = cached[0]
    else:
        try:
            r = subprocess.run(["getent", "hosts", ip], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split()
                host = parts[1] if len(parts) > 1 else ip
            else:
                host = ip
            with _rdns_lock:
                if len(_rdns_cache) >= RDNS_MAX_ENTRIES:
                    oldest_key = min(_rdns_cache, key=lambda k: _rdns_cache[k][1])
                    del _rdns_cache[oldest_key]
                _rdns_cache[ip] = (host, now)
        except (subprocess.TimeoutExpired, OSError, Exception):
            with _rdns_lock:
                _rdns_cache[ip] = (ip, now)
            host = ip
    return f"{host}:{port}" if port else host


_geo_cache = {}
GEO_TTL = 86400
_geo_lock = threading.Lock()
_geo_last_req = 0


def _cc_to_flag(cc: str) -> str:
    if not cc or len(cc) != 2:
        return ""
    return chr(0x1F1E6 + ord(cc[0].upper()) - ord('A')) + chr(0x1F1E6 + ord(cc[1].upper()) - ord('A'))


def geo_lookup(ip: str) -> dict:
    _private = ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or \
        ip.startswith("169.254.") or ip.startswith("fc") or ip.startswith("fd") or ip == "::1"
    if not _private and ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2:
            try:
                second = int(parts[1])
                _private = 16 <= second <= 31
            except ValueError:
                pass
    if not ip or _private:
        return {"country": "Local", "cc": "", "flag": "", "city": "", "isp": "Local"}
    now = time.time()
    with _geo_lock:
        cached = _geo_cache.get(ip)
        if cached and now - cached["_ts"] < GEO_TTL:
            return cached
    try:
        global _geo_last_req
        wait_time = 0
        with _geo_lock:
            elapsed = time.time() - _geo_last_req
            if elapsed < 1.5:
                wait_time = 1.5 - elapsed
            _geo_last_req = time.time() + wait_time
        if wait_time > 0:
            time.sleep(wait_time)
        safe_ip = urllib.parse.quote(ip, safe='')
        url = f"http://ip-api.com/json/{safe_ip}?fields=status,country,countryCode,city,isp,org"
        req = urllib.request.Request(url, headers={"User-Agent": "TrustTunnel-Admin/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") == "success":
            result = {
                "country": data.get("country", ""),
                "cc": data.get("countryCode", ""),
                "flag": _cc_to_flag(data.get("countryCode", "")),
                "city": data.get("city", ""),
                "isp": data.get("isp", data.get("org", "")),
                "_ts": now,
            }
        else:
            result = {"country": "", "cc": "", "flag": "", "city": "", "isp": "", "_ts": now}
        with _geo_lock:
            if len(_geo_cache) >= 500:
                oldest = min(_geo_cache, key=lambda k: _geo_cache[k]["_ts"])
                del _geo_cache[oldest]
            _geo_cache[ip] = result
        return result
    except Exception:
        result = {"country": "", "cc": "", "flag": "", "city": "", "isp": "", "_ts": now}
        with _geo_lock:
            _geo_cache[ip] = result
        return result


def enrich_with_geo(items: list, ip_key: str = "ip") -> list:
    for item in items:
        ip = item.get(ip_key)
        if ip:
            geo = geo_lookup(ip)
            item["geo"] = {k: v for k, v in geo.items() if k != "_ts"}
    return items
