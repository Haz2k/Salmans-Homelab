# Salman’s HomeLab Configuration

This repository documents my multi-node self-hosted home server infrastructure running on **Proxmox VE (PVE)**.

---

## 🖥️ Node Hardware Layout

### 🟠 [pve1](./pve1) — Dell Optiplex 5080 (Primary Node)
* **Host IP:** `192.168.0.100`
* **Storage:** 256GB NVMe (OS & DBs) + 1TB HDD mapped to `/mnt/pve/storage`
* **Core Role:** Handles edge routing, media management, local cloud, and document automation.
* **Services Hosted:** NPM, Immich, Nextcloud, Home Assistant, Jellyfin/Arr Stack, Pi-hole v6, Paperless-NGX/n8n.

### 🔵 pve2 — (Secondary Node)
* *Documentation coming soon...*

---

## 📦 Stacks & LXC Layout (pve1)

All services for this node are organized cleanly inside the `pve1/` directory:

* **[Utility & Routing Layout](./pve1/utility-stack)** (CT100 — `192.168.0.128`): Nginx Proxy Manager, Homepage Dashboard, Filebrowser, DuckDNS Updater
* **[Immich Stack](./pve1/immich-stack)** (CT101 — `192.168.0.129`): Photos, PostgreSQL, Redis
* **[Nextcloud Stack](./pve1/nextcloud-stack)** (CT102 — `192.168.0.132`): Cloud storage, MariaDB
* **[Home Assistant Stack](./pve1/home-assistant-stack)** (CT103 — `192.168.0.133`): Smart home automation
* **[Media Stack](./pve1/media-stack)** (CT104 — `192.168.0.134`): Jellyfin, Arr apps, qBittorrent, Gluetun VPN
* **[Security & Maintenance Stack](./pve1/security-stack)** (CT105 — `192.168.0.136`): Pi-hole v6 (Local overrides for subdomains)
* **[Automation Stack](./pve1/automation-stack)** (CT106 — `192.168.0.137`): Paperless-NGX, Ollama (Mistral), n8n workflow

*Each stack folder contains its respective Docker Compose configurations and specific system documentation.*
