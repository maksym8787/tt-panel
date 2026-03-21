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
            r = subprocess.run(["getent", "hosts", ip], capture_output=True, text=True, timeout=1)
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


def rdns_lookup_cached(ip_port: str) -> str:
    ip = ip_port.split(":")[0]
    port = ip_port.split(":")[1] if ":" in ip_port else ""
    with _rdns_lock:
        cached = _rdns_cache.get(ip)
    if cached:
        host = cached[0]
        return f"{host}:{port}" if port else host
    _schedule_rdns_bg(ip)
    return ip_port


_rdns_bg_queue = set()
_rdns_bg_lock = threading.Lock()
_rdns_bg_running = False


def _schedule_rdns_bg(ip: str):
    global _rdns_bg_running
    with _rdns_bg_lock:
        _rdns_bg_queue.add(ip)
        if _rdns_bg_running:
            return
        _rdns_bg_running = True
    t = threading.Thread(target=_rdns_bg_worker, daemon=True)
    t.start()


def _rdns_bg_worker():
    global _rdns_bg_running
    while True:
        with _rdns_bg_lock:
            if not _rdns_bg_queue:
                _rdns_bg_running = False
                return
            ip = _rdns_bg_queue.pop()
        rdns_lookup(ip + ":0")


_geo_cache = {}
GEO_TTL = 86400
_geo_lock = threading.Lock()


def _cc_to_flag(cc: str) -> str:
    if not cc or len(cc) != 2:
        return ""
    return chr(0x1F1E6 + ord(cc[0].upper()) - ord('A')) + chr(0x1F1E6 + ord(cc[1].upper()) - ord('A'))


def _is_private(ip: str) -> bool:
    if not ip:
        return True
    if ip.startswith(("10.", "192.168.", "127.", "169.254.", "fc", "fd")) or ip == "::1":
        return True
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2:
            try:
                return 16 <= int(parts[1]) <= 31
            except ValueError:
                pass
    return False


def geo_lookup(ip: str) -> dict:
    if _is_private(ip):
        return {"country": "Local", "cc": "", "flag": "", "city": "", "isp": "Local"}
    now = time.time()
    with _geo_lock:
        cached = _geo_cache.get(ip)
        if cached and now - cached["_ts"] < GEO_TTL:
            return cached
    try:
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


def geo_lookup_batch(ips: list) -> dict:
    now = time.time()
    results = {}
    to_fetch = []
    for ip in ips:
        if _is_private(ip):
            results[ip] = {"country": "Local", "cc": "", "flag": "", "city": "", "isp": "Local"}
            continue
        with _geo_lock:
            cached = _geo_cache.get(ip)
            if cached and now - cached["_ts"] < GEO_TTL:
                results[ip] = cached
                continue
        to_fetch.append(ip)
    if not to_fetch:
        return results
    for batch_start in range(0, len(to_fetch), 100):
        batch = to_fetch[batch_start:batch_start + 100]
        try:
            payload = json.dumps([
                {"query": ip, "fields": "status,country,countryCode,city,isp,org,query"}
                for ip in batch
            ]).encode()
            req = urllib.request.Request(
                "http://ip-api.com/batch",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "TrustTunnel-Admin/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            for item in data:
                ip = item.get("query", "")
                if item.get("status") == "success":
                    result = {
                        "country": item.get("country", ""),
                        "cc": item.get("countryCode", ""),
                        "flag": _cc_to_flag(item.get("countryCode", "")),
                        "city": item.get("city", ""),
                        "isp": item.get("isp", item.get("org", "")),
                        "_ts": now,
                    }
                else:
                    result = {"country": "", "cc": "", "flag": "", "city": "", "isp": "", "_ts": now}
                with _geo_lock:
                    if len(_geo_cache) >= 500:
                        oldest = min(_geo_cache, key=lambda k: _geo_cache[k]["_ts"])
                        del _geo_cache[oldest]
                    _geo_cache[ip] = result
                results[ip] = result
        except Exception as e:
            logger.warning("Batch geo failed: %s", e)
            for ip in batch:
                result = {"country": "", "cc": "", "flag": "", "city": "", "isp": "", "_ts": now}
                with _geo_lock:
                    _geo_cache[ip] = result
                results[ip] = result
    return results


def enrich_with_geo(items: list, ip_key: str = "ip") -> list:
    ips = [item.get(ip_key) for item in items if item.get(ip_key)]
    geo_map = geo_lookup_batch(ips)
    for item in items:
        ip = item.get(ip_key)
        if ip and ip in geo_map:
            item["geo"] = {k: v for k, v in geo_map[ip].items() if k != "_ts"}
    return items
