# Immich Stack

Self-hosted photo and video backup solution running inside LXC container **CT101** (`192.168.0.129`).

## Services

* **Immich Server:** High-performance core asset management engine.
* **PostgreSQL:** Primary relational database holding asset metadata (stored on the fast NVMe drive).
* **Redis:** High-speed, in-memory key-value cache handling real-time background jobs and queues.

## Notes

* Used for fully automated photo and video phone backups.
* App data and media assets are persistently mapped to the dedicated 1TB storage drive.
* Complete self-hosted alternative to Google Photos and iCloud.
* Managed via Portainer.
