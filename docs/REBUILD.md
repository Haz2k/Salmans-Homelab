# Rebuild runbook

How to rebuild the homelab from nothing, and how to run it day to day.
Repo: github.com/Haz2k/Salmans-Homelab (branch Main). Last reviewed: 2026-11-19.

## What you need before you start

- The vault password (`.vault_pass`, gitignored, repo root on CT100). Keep a copy OUTSIDE the lab
  (flash drive or password manager). Without it `group_vars/all/vault.yml` cannot be decrypted.
- A GitHub token for pushing from CT100 (embedded in the git remote URL).
- The backups on pve2's disk (`marketing-storage`, NFS-exported to pve1 as storage `pve2-backups`).

## Layout

| Node / CT | CTID | IP | Notes |
|---|---|---|---|
| pve1 (OptiPlex 5080) | - | 192.168.0.100 | 256G NVMe + 698G HDD (`storage`) |
| pve2 (OptiPlex 3050) | - | 192.168.0.150 | 256G NVMe + 596G HDD (`marketing-storage`, backup target) |
| Pi (QDevice) | - | 192.168.0.199 | DHCP reservation, needs tcp 5403 open |
| ansible_control | 100 | 192.168.0.3 | Semaphore, Dockhand (main UI), DIUN |
| pihole | 101 | 192.168.0.4 | |
| core_stack | 102 | 192.168.0.5 | Traefik, Authelia, Vaultwarden, DuckDNS |
| monitoring_stack | 104 | 192.168.0.7 | Prometheus, Grafana, Uptime Kuma, Homepage |
| automation_stack | 105 | 192.168.0.8 (pve2) | Home Assistant, Ollama, Paperless |
| receipts_stack | 106 | 192.168.0.9 (pve2) | |
| photos_stack | 107 | 192.168.0.10 | Immich + Nextcloud |
| sandbox | 108 | 192.168.0.11 | Frigate, test apps (managed from Dockhand) |

CT sizes, bind mounts and the Frigate GPU passthrough are declared in `group_vars/all/main.yml`
(`lxc_services`) and applied by the `proxmox_lxc_provision` role. Disk sizes only apply at CT creation:
growing an existing disk is a manual `pct resize`.

## Rebuild order

1. Proxmox on both nodes, cluster "Salmans-Cluster", QDevice on the Pi (`pvecm status` should show 3 votes).
   Mount each node's HDD at `/mnt/pve/storage` (pve1) and `/mnt/pve/marketing-storage` (pve2) as directory
   storages with `is_mountpoint 1` and the same names.
2. Create the `ansible` user with passwordless sudo on pve1 and pve2 from the Proxmox web Shell
   (root SSH is disabled by the hardening role, by design).
3. Create CT100 by hand (Debian 12, unprivileged, nesting on, 12G disk). Install ansible-core 2.18+ (pipx),
   generate `~/.ssh/id_ed25519`, clone the repo, restore `.vault_pass`.
4. Run everything, in site.yml order:

        cd ~/Salmans-Homelab
        ansible-playbook site.yml --vault-password-file .vault_pass

   Order inside: security baseline, provision CTs, Docker, main Dockhand (CT100) + Hawser agents,
   Pi-hole, Traefik, core, monitoring, automation, Semaphore, receipts, Immich, backups, Frigate, Nextcloud.
   Run a single piece with `--tags <name>` (e.g. `--tags traefik`).
5. Semaphore project and schedules: `SEMAPHORE_ADMIN=salman python3 scripts/semaphore_bootstrap.py`
   (the login is `salman`, not `admin`).
6. Restore data (below), then the manual steps (below).

## Restoring data

- Whole CTs: Proxmox UI, storage `pve2-backups` (or `marketing-storage` on pve2) -> Backups -> Restore.
  Test restores must use a spare CT ID (199) and a different IP, with "Start after restore" off.
- Immich photos: bind-mounted, so NOT in vzdump. Nightly copy is in `pve2-backups/photos-copy`
  (rsync, never deletes). Copy back to `/mnt/pve/storage/immich/uploads` before starting Immich.
- Nextcloud files: bind-mounted, nightly copy in `pve2-backups/nextcloud-copy`. Put it at
  `/mnt/pve/storage/nextcloud/data`, `chown -R 100033:100033`. IMPORTANT: Nextcloud refuses to install
  if the admin user's folder already exists. Move the user folder aside (`salman` -> `salman.old`),
  run the nextcloud play, then swap it back and run:

        docker exec -u www-data nextcloud php occ files:scan --all

  The CT107 vzdump contains the Nextcloud and Immich databases (snapshot, crash-consistent).
- Frigate recordings (`/mnt/pve/storage/frigate`) are not backed up. CT108 is not in the backup job.

## Secrets and where they live

- `group_vars/all/vault.yml` (encrypted): service passwords, `vault_domain`, `vault_hawser_token`,
  Nextcloud DB/admin entries. Never put a value starting with `$` in it (Compose eats it); the
  Nextcloud template escapes `$` for you. Never paste decrypted vault output anywhere.
- Hawser agents all use the shared `vault_hawser_token`. Dockhand's list of environments is stored inside
  Dockhand on CT100 (not in this repo): after a rebuild, re-add each CT as a Standard (Hawser) environment,
  host `<CT ip>`, port 2376, same token. CT100 is in the nightly backup, so a restore brings them back.

## Manual first-run steps (not automated)

- Dockhand admin, Frigate admin (password is printed once in `docker logs frigate`: change it), Immich,
  Nextcloud 2FA, Home Assistant, Paperless, Vaultwarden, Pi-hole first logins.
- Router: only 80/443 forwarded, to Traefik (192.168.0.5). Nothing for 8006, 22 or 2376.
- Pi-hole local DNS entries must match real service IPs (a stale entry once broke household DNS).

## Day to day

- Containers: update from Dockhand (https://dockhand.<domain>). Image versions are pinned in the role
  templates (tag + digest); upgrading an app means changing its pin in the repo. DIUN reports new versions.
- OS patching: Semaphore, Sundays 04:00 (`os_update.yml`). Check that every CT is back afterwards.
- Ad-hoc commands: `ansible-playbook adhoc.yml --vault-password-file .vault_pass -e target=<host> -e "cmd='...'"`
- Push to GitHub from CT100 (token in the remote URL); keep the repo and the live system in sync.

## Backups

- vzdump nightly, snapshot + zstd, keep last 7: `backup-pve1` 02:00 (CTs 100, 101, 102, 104, 107) to
  `pve2-backups`; `backup-pve2` 02:30 (CTs 105, 106) to `marketing-storage`.
- rsync copies: photos 03:30, Nextcloud 04:00 (cron on pve1, no `--delete`).
- Known gaps: no offsite copy, no UPS, Frigate/CT108 not backed up, the backup disk is a 5400rpm laptop HDD,
  the Pi QDevice had a low-voltage warning at boot.
