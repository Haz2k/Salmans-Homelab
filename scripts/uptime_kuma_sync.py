#!/usr/bin/env python3
"""Add or refresh Uptime Kuma monitors from the list below (idempotent).
Run:  UK_USER=... UK_PASS=... python3 scripts/uptime_kuma_sync.py
Needs: pip install uptime-kuma-api2   (Uptime Kuma's API is internal and may change)
"""
import os, sys
from uptime_kuma_api import UptimeKumaApi, MonitorType

URL = os.environ.get("UK_URL", "http://192.168.0.7:3001")
DOMAIN = os.environ.get("UK_DOMAIN", "salmanslab.duckdns.org")
SLUG = "homepage"

PUBLIC = {  # name -> subdomain (checked through Traefik from outside)
    "Immich": "photos", "Nextcloud": "cloud/status.php", "Frigate": "frigate",
    "Vaultwarden": "vault", "Authelia": "auth", "Paperless": "paperless",
    "Home Assistant": "ha", "Grafana": "grafana", "Dockhand": "dockhand",
    "Receipts": "receipts", "Speedtest": "speedtest", "Homepage": "homepage",
}
DIRECT = {  # name -> direct LAN URL (works even if DNS or Traefik is down)
    "Pi-hole (direct)": "http://192.168.0.4:8081/admin",
    "Semaphore (direct)": "http://192.168.0.3:3000",
    "Frigate (direct)": "http://192.168.0.11:5000",
}
PING = {"Proxmox pve1": "192.168.0.100", "Proxmox pve2": "192.168.0.150"}

want = []
for name, sub in PUBLIC.items():
    host, _, path = sub.partition("/")
    want.append((name, dict(type=MonitorType.HTTP, url=f"https://{host}.{DOMAIN}" + (f"/{path}" if path else ""))))
for name, url in DIRECT.items():
    want.append((name, dict(type=MonitorType.HTTP, url=url)))
for name, host in PING.items():
    want.append((name, dict(type=MonitorType.PING, hostname=host)))

common = dict(interval=60, maxretries=3, retryInterval=20)

with UptimeKumaApi(URL) as api:
    api.login(os.environ["UK_USER"], os.environ["UK_PASS"])
    have = {m["name"]: m["id"] for m in api.get_monitors()}
    ids = []
    for name, cfg in want:
        if name in have:
            api.edit_monitor(have[name], **common)
            ids.append(have[name]); print("updated retries:", name)
        else:
            r = api.add_monitor(name=name, **cfg, **common)
            mid = r.get("monitorID") or r.get("monitorId") or {m["name"]: m["id"] for m in api.get_monitors()}[name]
            ids.append(mid); print("added:", name)
    ids += [i for n, i in have.items() if n not in dict(want) and i not in ids]
    try:
        page = api.get_status_page(SLUG)
        api.save_status_page(
            slug=SLUG, id=page["id"], title=page.get("title", "Homepage"),
            description=page.get("description"), theme=page.get("theme", "auto"),
            published=True, showTags=False, domainNameList=page.get("domainNameList", []),
            customCSS=page.get("customCSS", ""), footerText=page.get("footerText"),
            showPoweredBy=page.get("showPoweredBy", True), icon=page.get("icon", "/icon.svg"),
            publicGroupList=[{"name": "Services", "monitorList": [{"id": i} for i in ids]}],
        )
        print("status page updated:", len(ids), "monitors")
    except Exception as e:
        print("monitors are in, but the status page needs a manual edit:", e)
