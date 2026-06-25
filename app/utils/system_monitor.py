"""System monitoring utilities."""
import psutil, time, logging
log = logging.getLogger(__name__)

def get_cpu_percent():
    try:
        return psutil.cpu_percent(interval=None)
    except Exception as e:
        log.error(f"CPU: {e}"); return 0.0

def get_ram():
    try:
        m = psutil.virtual_memory()
        return {"percent": m.percent, "used_gb": m.used/1e9, "total_gb": m.total/1e9}
    except Exception as e:
        log.error(f"RAM: {e}"); return {"percent":0,"used_gb":0,"total_gb":0}

def get_net_speed():
    try:
        c1 = psutil.net_io_counters()
        time.sleep(0.5)
        c2 = psutil.net_io_counters()
        up = (c2.bytes_sent - c1.bytes_sent) / 0.5 / 1024
        dn = (c2.bytes_recv - c1.bytes_recv) / 0.5 / 1024
        return {"upload_kbs": round(up, 1), "download_kbs": round(dn, 1)}
    except Exception as e:
        log.error(f"NET: {e}"); return {"upload_kbs":0,"download_kbs":0}

def get_processes():
    procs = []
    dangerous_kws = ["malware","virus","trojan","ransom","miner","backdoor","rootkit","keylog","spyware","adware"]
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_info","username","status"]):
        try:
            info = p.info
            cpu  = info["cpu_percent"] or 0.0
            mem  = (info["memory_info"].rss / 1e6) if info["memory_info"] else 0.0
            name = (info["name"] or "").lower()
            user = info["username"] or "N/A"
            if any(k in name for k in dangerous_kws):
                risk = "DANGEROUS"
            elif cpu > 50 or mem > 200:
                risk = "SUSPICIOUS"
            else:
                risk = "SAFE"
            procs.append({"pid":info["pid"],"name":info["name"],"cpu":round(cpu,1),
                          "mem":round(mem,1),"user":user,"risk":risk})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs

def get_connections():
    conns = []
    suspicious_ports = {4444,1337,31337,6666,6667,1234,5555,7777,8888,9999}
    try:
        for c in psutil.net_connections(kind="inet"):
            try:
                laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
                raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
                status = c.status or "N/A"
                pid    = c.pid or 0
                pname  = "N/A"
                if pid:
                    try: pname = psutil.Process(pid).name()
                    except Exception: pass
                risk = "SAFE"
                if c.laddr and c.laddr.port in suspicious_ports: risk = "DANGEROUS"
                elif c.raddr and c.raddr.port in suspicious_ports: risk = "DANGEROUS"
                elif status == "CLOSE_WAIT": risk = "SUSPICIOUS"
                conns.append({"laddr":laddr,"raddr":raddr,"status":status,
                              "pid":pid,"pname":pname,"risk":risk})
            except Exception:
                pass
    except Exception as e:
        log.error(f"CONN: {e}")
    return conns

def get_disks():
    partitions = []
    try:
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                partitions.append({
                    "device": p.device, "mount": p.mountpoint,
                    "total_gb": round(usage.total/1e9,2),
                    "used_gb":  round(usage.used/1e9,2),
                    "free_gb":  round(usage.free/1e9,2),
                    "percent":  usage.percent,
                    "fstype":   p.fstype,
                })
            except PermissionError:
                pass
    except Exception as e:
        log.error(f"DISK: {e}")
    return partitions
