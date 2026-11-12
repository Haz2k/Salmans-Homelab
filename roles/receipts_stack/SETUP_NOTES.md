# receipts_stack — setup notes

Everything here drops into `roles/receipts_stack/` as-is. Three things
still need manual edits to files this role doesn't own:

## 1. `group_vars/all/vault.yml` (and `vault.yml.example`)

Add:
```yaml
vault_receipts_db_password: "<generate with: openssl rand -base64 24>"
vault_anthropic_api_key: "sk-ant-..."
```
No `$` at the start of either value — see your own learnings doc, Compose
mangles a leading `$` as a variable reference.

## 2. `inventory/hosts.yml`

Add the new LXC to `lxc_hosts` (same group your other 5 app LXCs are in),
with `ansible_user: root` until you provision a non-root `ansible` user on it:
```yaml
receipts_stack:
  ansible_host: 192.168.0.9
  ansible_user: root
```

## 3. Your `proxmox_lxc_provision` role's LXC list var

Add an entry matching the shape of your existing 5 (pihole, core_stack,
etc.) — CTID 106, hostname `receipts-stack` (no underscore — Proxmox
hostnames can't have one), IP `192.168.0.9`, `nesting=1`, explicit `disk:`
size (don't trust the default — you've hit the 4G-fills-instantly problem
before).

## 4. Traefik dynamic routing

`templates/traefik-dynamic-receipts.yml.j2` is included in this role, but
it needs to be copied into wherever your `traefik` role's file-provider
dynamic config directory actually is — same pattern your other
non-core_stack services already use, since Docker labels don't cross LXC
boundaries.

## Running it

```bash
ansible-playbook site.yml --tags receipts_stack --vault-password-file .vault_pass
```

## First use

1. Visit `https://receipts.<yourdomain>` (through Authelia)
2. Go to **Categories**, add your real expense categories first — the
   extraction prompt only picks from categories that already exist, so
   anything added later won't retroactively apply to old receipts
3. Upload a receipt, open it in the review panel once it hits
   "needs review", check the fields, hit **Confirm**

## Known limitations worth knowing about

- Monthly totals only count **confirmed** receipts with a `line_items`
  sum — a receipt stuck in "needs review" won't show in the monthly
  total until you confirm it. This is intentional (keeps totals honest)
  but can look like "my total is wrong" if you forget to review a batch.
- `/mnt/pve/storage/receipts` needs to exist and be writable by the LXC
  before first run — this role creates it, but if the HDD mount isn't
  live on the Proxmox host yet, the bind-mount will silently create an
  empty directory *on the SSD* instead. Worth a `df -h` check after
  first deploy to confirm `/data/receipts` inside the container is
  actually landing on the HDD, not the LXC's own rootfs.
- No auth inside the app itself — it relies entirely on Authelia sitting
  in front of it via Traefik. Don't expose port 8000 directly.
