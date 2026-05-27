# Media Stack

Handles media automation, downloads, and streaming inside LXC container **CT104** (`192.168.0.134`).

## Services

* **Jellyfin:** Media streaming server with Intel QuickSync hardware transcoding enabled via `/dev/dri` passthrough.
* **Radarr:** Movie download management.
* **Sonarr:** TV show download management.
* **Prowlarr:** Indexer management for torrents.
* **qBittorrent:** Torrent download client.
* **Gluetun:** Secure VPN client connected to Mullvad VPN (Chicago server) acting as a strict kill switch for all qBittorrent traffic.
* **Seerr:** Media request dashboard for users.

## Notes

* Hardware acceleration (`/dev/dri`) passthrough configured from Proxmox host to LXC.
* All outbound torrent traffic is completely firewalled and routed through Gluetun.
* Central landing dashboard handled globally by Homepage in the Utility container.
* Managed via Portainer.
