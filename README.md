# Salman’s HomeLab

This repository documents my self-hosted home server infrastructure running on **Proxmox VE (PVE)** using LXC containers, Docker Compose, and Portainer.

## System Overview

* **Host Machine:** Dell Optiplex 5080
* **Hypervisor:** Proxmox VE 8.x (Host IP: `192.168.0.100`)
* **Container Management:** LXC Containers + Docker Compose + Portainer (`192.168.0.128:9000`)
* **Base Domain:** `salmanslab.duckdns.org` (SSL via Nginx Proxy Manager)
* **Storage:** * 256GB NVMe (OS, LXC root disks, high-performance databases)
  * 1TB HDD mounted at `/mnt/pve/storage` (Persistent app data and media)
* **Design Goals:**
  * High availability and resource isolation via LXC
  * Easy containerized updates using Portainer / Watchtower
  * Complete separation of routing, media, storage, and automation stacks

## Stacks & LXC Layout

* **[Utility & Routing]** (CT100 — `192.168.0.128`): Nginx Proxy Manager, Homepage Dashboard, Filebrowser, DuckDNS Updater
* **[Immich Stack](https://github.com/Markaz-Ash-Shadibi/Salmans-Homelab/tree/main/immich-stack)** (CT101 — `192.168.0.129`): Photos, PostgreSQL, Redis
* **[Nextcloud Stack](https://github.com/Markaz-Ash-Shadibi/Salmans-Homelab/tree/main/nextcloud-stack)** (CT102 — `192.168.0.132`): Cloud storage, MariaDB
* **[Home Assistant Stack]** (CT103 — `192.168.0.133`): Smart home automation
* **[Media Stack](https://github.com/Markaz-Ash-Shadibi/Salmans-Homelab/tree/main/media-stack)** (CT104 — `192.168.0.134`): Jellyfin, Arr apps, qBittorrent, Gluetun VPN
* **[Security & Maintenance Stack](https://github.com/Markaz-Ash-Shadibi/Salmans-Homelab/tree/main/security-stack)** (CT105 — `192.168.0.136`): Pi-hole v6 (Local overrides for subdomains)
* **[Automation Stack]** (CT106 — `192.168.0.137`): Paperless-NGX, Ollama (Mistral), n8n workflow

*Each stack folder contains its respective Docker Compose configurations and specific system documentation.*
