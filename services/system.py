import os
import subprocess
import time

from config import logger


def get_service_status():
    info = {"active": False, "uptime": "", "uptime_seconds": 0, "memory": "", "pid": ""}
    try:
        r = subprocess.run(["systemctl", "show", "trusttunnel", "--no-pager",
            "-p", "ActiveState,MainPID,MemoryCurrent,ActiveEnterTimestampMonotonic"],
            capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if line.startswith("ActiveState="):
                info["active"] = line.split("=", 1)[1] == "active"
            elif line.startswith("MainPID="):
                info["pid"] = line.split("=", 1)[1]
            elif line.startswith("MemoryCurrent="):
                v = line.split("=", 1)[1]
                if v.isdigit():
                    info["memory"] = f"{int(v)/1024/1024:.1f} MB"
            elif line.startswith("ActiveEnterTimestampMonotonic="):
                v = line.split("=", 1)[1].strip()
                if v.isdigit() and int(v) > 0:
                    mono_now = int(time.monotonic() * 1_000_000)
                    try:
                        with open("/proc/uptime") as f:
                            boot_seconds = float(f.read().split()[0])
                        mono_now = int(boot_seconds * 1_000_000)
                    except Exception:
                        pass
                    elapsed = max(0, mono_now - int(v))
                    info["uptime_seconds"] = elapsed // 1_000_000
    except Exception as e:
        logger.error("Service check error: %s", e)
    return info


def get_server_ip():
    try:
        r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split()[0]
    except Exception:
        return "unknown"


_prev_cpu = None
_prev_cpu_ts = 0


def _read_cpu_stat():
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith("cpu "):
                return list(map(int, line.split()[1:]))
    return None


def get_vps_resources():
    global _prev_cpu, _prev_cpu_ts
    info = {}
    try:
        cur = _read_cpu_stat()
        now = time.monotonic()
        if cur and _prev_cpu and (now - _prev_cpu_ts) > 1:
            d_idle = cur[3] - _prev_cpu[3]
            d_total = sum(cur) - sum(_prev_cpu)
            info["cpu_pct"] = round(100 * (1 - d_idle / d_total), 1) if d_total > 0 else 0
        else:
            info["cpu_pct"] = 0
        if cur:
            _prev_cpu = cur
            _prev_cpu_ts = now
    except Exception:
        info["cpu_pct"] = 0
    try:
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                parts = line.split()
                if parts[0] in ("MemTotal:", "MemAvailable:", "MemFree:", "Buffers:", "Cached:"):
                    mem[parts[0].rstrip(":")] = int(parts[1])
            total = mem.get("MemTotal", 1)
            avail = mem.get("MemAvailable", mem.get("MemFree", 0) + mem.get("Buffers", 0) + mem.get("Cached", 0))
            info["ram_total_mb"] = round(total / 1024)
            info["ram_used_mb"] = round((total - avail) / 1024)
            info["ram_pct"] = round(100 * (total - avail) / total, 1) if total > 0 else 0
    except Exception:
        info["ram_total_mb"] = 0
        info["ram_used_mb"] = 0
        info["ram_pct"] = 0
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        used = total - st.f_frsize * st.f_bfree
        info["disk_total_gb"] = round(total / 1073741824, 1)
        info["disk_used_gb"] = round(used / 1073741824, 1)
        info["disk_pct"] = round(100 * used / total, 1) if total > 0 else 0
    except Exception:
        info["disk_total_gb"] = 0
        info["disk_used_gb"] = 0
        info["disk_pct"] = 0
    try:
        with open("/proc/uptime") as f:
            info["uptime_seconds"] = int(float(f.read().split()[0]))
    except Exception:
        info["uptime_seconds"] = 0
    return info
