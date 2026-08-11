# Salman's Homelab — Ansible Control Repo

This repo is the single source of truth for the homelab. If a node dies,
cloning this repo + running `site.yml` (with the vault password from the
flash drive) rebuilds it.

Full write-up / hardware plan lives at:
https://github.com/Haz2k/Salmans-Homelab

## Current phase

Ansible setup across the 3 currently-owned devices only:
- pve1 — Dell OptiPlex Micro 3050 (Proxmox node)
- pve2 — Dell OptiPlex Micro 3050 (Proxmox node)
- pi-qdevice — Raspberry Pi 3B (Corosync QDevice)

Everything else (rack build, PBS, 3rd node, AI PC) is deferred — see
`docs/phases.md`.

## How this repo is organized

```
inventory/            # which machines exist (pve1, pve2, pi)
group_vars/           # variables + Ansible Vault-encrypted secrets
roles/                # one folder per job (security, docker, each stack...)
playbooks/            # entry points that call roles
site.yml              # the master playbook — runs everything, tag-gated
requirements.yml      # Galaxy roles/collections this repo depends on
```

## First-time setup (on the control node / your machine)

```bash
# install Galaxy roles + collections this repo needs
ansible-galaxy install -r requirements.yml
ansible-galaxy collection install -r requirements.yml

# create your vault password file (NOT committed — lives on the flash drive)
# then encrypt secrets:
ansible-vault create group_vars/all/vault.yml
```

## Running it

```bash
# bootstrap everything from empty (new/replacement node)
ansible-playbook site.yml --tags init --vault-password-file .vault_pass

# patch everything (OS + containers)
ansible-playbook site.yml --tags upgrade --vault-password-file .vault_pass

# rebuild just one stack, e.g. media
ansible-playbook site.yml --tags media_stack --vault-password-file .vault_pass
```

## Secrets model

- All secrets live encrypted in `group_vars/all/vault.yml` via Ansible
  Vault — safe to commit to GitHub.
- The **vault password itself** is the one thing that never goes to
  GitHub. It lives on a flash drive (`ansible-homelab/.vault_pass`)
  alongside a mirror of this repo and a `node-configs/` folder with
  native app exports (Pi-hole Teleporter, Uptime Kuma JSON, Grafana
  dashboard JSON, Home Assistant backups) for fast manual recovery.

## Role sourcing rule

When a well-known, actively maintained Galaxy role exists for a job,
use it (see `requirements.yml`) instead of writing one from scratch.
For app-specific compose/config files, source from the app's official
docs/website first, falling back to its official GitHub repo.

## Status of the compose files

Every role's `docker-compose.yml.j2` (and supporting config templates,
e.g. Authelia's `configuration.yml` / `users_database.yml`, Prometheus's
scrape config) is filled in with real, current settings pulled from each
app's own official docs — not placeholders. Source links are at the top
of every task file. Still TODO before first run:
- Real IPs in `inventory/hosts.yml`
- Real values in `group_vars/all/vault.yml` (see `vault.yml.example` for
  every key that's expected)
- Confirm the LXC OS template name in `proxmox_lxc_provision` matches
  what's actually on your Proxmox storage
- Scrutiny's `/dev/sda` device path — confirm real disk paths per node
