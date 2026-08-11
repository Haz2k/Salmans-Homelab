# Phases

**Current phase:** Ansible across the 3 currently-owned devices (this repo).

**Deferred, in rough order:**
1. Finish rack hardware (DeskPi RackMate T2, 12U)
2. Rebuild Proxmox cluster foundation on the rack-mounted hardware
3. (this repo) Stand up Ansible control node and roles
4. Rebuild existing services via Ansible, drop Portainer
5. Add new services via Ansible
6. ZFS replication (pvesr, 15-min) + HA groups, tested failover
7. Prometheus/Grafana monitoring stack
8. Semaphore with safety-logic playbooks + Grafana link panels
9. Rack kiosk screen
10. Real backup plan: PBS, second target, retention, alerting, tested restores

Explicitly NOT in scope right now: PBS/backup infra, 3rd Proxmox node,
the standalone mATX AI/math PC build, full 12U rack physical build.
