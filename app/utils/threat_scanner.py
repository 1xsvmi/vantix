"""Threat intelligence scanner with FireHOL blocklist support."""
import os, json, time, logging, requests, ipaddress
log = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.expanduser("~"), ".vantix", "blocklist.json")
FIREHOL_URL = "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset"
CACHE_TTL   = 86400  # 24 hours

os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

_blocklist: set = set()
_custom:    set = set()

def _load_cache():
    global _blocklist
    if os.path.exists(CACHE_FILE):
        try:
            data = json.loads(open(CACHE_FILE).read())
            if time.time() - data.get("ts", 0) < CACHE_TTL:
                _blocklist = set(data.get("ips", []))
                log.info(f"Loaded {len(_blocklist)} IPs from cache")
                return True
        except Exception as e:
            log.error(f"Cache load: {e}")
    return False

def fetch_blocklist(force=False):
    global _blocklist
    if not force and _load_cache():
        return len(_blocklist)
    try:
        r = requests.get(FIREHOL_URL, timeout=15)
        r.raise_for_status()
        ips = []
        for line in r.text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ips.append(line)
        _blocklist = set(ips)
        with open(CACHE_FILE, "w") as f:
            json.dump({"ts": time.time(), "ips": list(_blocklist)}, f)
        log.info(f"Fetched {len(_blocklist)} entries from FireHOL")
        return len(_blocklist)
    except requests.exceptions.ConnectionError:
        log.warning("Offline – using cached blocklist")
        _load_cache()
        return len(_blocklist)
    except Exception as e:
        log.error(f"Fetch blocklist: {e}")
        _load_cache()
        return len(_blocklist)

def _ip_in_set(ip_str: str, ip_set: set) -> bool:
    if not ip_str or ip_str in ("N/A", "0.0.0.0"):
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
        if str(addr) in ip_set:
            return True
        for entry in ip_set:
            try:
                if "/" in entry and addr in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                pass
    except ValueError:
        pass
    return False

def check_ip(ip_str: str) -> dict:
    ip_clean = ip_str.split(":")[0] if ":" in ip_str else ip_str
    in_bl  = _ip_in_set(ip_clean, _blocklist)
    in_cu  = _ip_in_set(ip_clean, _custom)
    threat = "DANGEROUS" if (in_bl or in_cu) else "SAFE"
    return {"ip": ip_clean, "threat": threat, "blocklisted": in_bl, "custom": in_cu}

def add_custom_ip(ip: str):
    _custom.add(ip.strip())

def remove_custom_ip(ip: str):
    _custom.discard(ip.strip())

def get_custom_ips() -> list:
    return list(_custom)

def blocklist_size() -> int:
    return len(_blocklist)

def check_connections(conns: list) -> list:
    results = []
    for c in conns:
        rip = c.get("raddr","").split(":")[0]
        info = check_ip(rip)
        results.append({**c, "threat": info["threat"], "blocklisted": info["blocklisted"]})
    return results
