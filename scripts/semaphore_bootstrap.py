#!/usr/bin/env python3
"""Set Semaphore up from code (no clicking): adds the jobs you need to an existing project.

Run ON CT100:   python3 ~/semaphore_bootstrap.py
It asks for the Semaphore password (hidden). Login name defaults to "salman"
(override: SEMAPHORE_ADMIN=...). Project name defaults to "Deploy Homelab"
(override: PROJECT_NAME=...). Nothing secret is printed.

What it does (safe to re-run, existing things are reused by name):
  * reuses the project's existing repository, inventory, environment and vault key
    (only creates them, from ~/.ssh/id_ed25519 and ~/Salmans-Homelab/.vault_pass,
    if the project has none)
  * adds three task templates:
      "OS patch (LXCs + Pi)"       os_update.yml  + weekly schedule (Sunday 04:00)
      "Run playbook (site.yml)"    site.yml, you type any extra args when you run it
                                   e.g.  --tags immich --limit photos_stack
      "Ad-hoc command"             adhoc.yml, asks for hosts + a shell command
"""
import getpass, json, os, sys, urllib.request, urllib.error, http.cookiejar

BASE = os.environ.get("SEMAPHORE_URL", "http://localhost:3000").rstrip("/")
ADMIN = os.environ.get("SEMAPHORE_ADMIN", "admin")
PROJECT = os.environ.get("PROJECT_NAME", "Deploy Homelab")
REPO_URL = os.environ.get("REPO_URL", "https://github.com/Haz2k/Salmans-Homelab.git")
BRANCH = os.environ.get("REPO_BRANCH", "Main")
HOME = os.path.expanduser("~")
SSH_KEY_FILE = os.environ.get("ANSIBLE_SSH_KEY", f"{HOME}/.ssh/id_ed25519")
VAULT_FILE = os.environ.get("VAULT_FILE", f"{HOME}/Salmans-Homelab/.vault_pass")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + "/api" + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:300]}")


def read(path):
    try:
        return open(path).read()
    except OSError as e:
        sys.exit(f"Cannot read {path}: {e}")


def first(items, name=None, **match):
    """Find one item: by name, else by field match, else just the first one."""
    items = items or []
    if name is not None:
        return next((i for i in items if i.get("name") == name), None)
    if match:
        return next((i for i in items if all(i.get(k) == v for k, v in match.items())), None)
    return items[0] if items else None


def main():
    pw = os.environ.get("SEMAPHORE_PASSWORD") or getpass.getpass(f"Semaphore password for '{ADMIN}': ")
    call("POST", "/auth/login", {"auth": ADMIN, "password": pw})
    print("Logged in.")

    proj = first(call("GET", "/projects"), PROJECT)
    if not proj:
        proj = call("POST", "/projects", {"name": PROJECT, "alert": False, "max_parallel_tasks": 0})
        print(f"  + project: {PROJECT}")
    else:
        print(f"  = project: {PROJECT}")
    pid = proj["id"]
    P = f"/project/{pid}"

    keys = call("GET", f"{P}/keys")

    def key(name, body):
        found = first(keys, name)
        if found:
            return found
        made = call("POST", f"{P}/keys", dict(body, name=name, project_id=pid))
        keys.append(made)
        print(f"  + key: {name}")
        return made

    repo = first(call("GET", f"{P}/repositories"))
    if repo:
        print(f"  = repository: {repo['name']}")
    else:
        k_none = key("no-key", {"type": "none"})
        repo = call("POST", f"{P}/repositories", {
            "name": "homelab", "project_id": pid, "git_url": REPO_URL, "git_type": "git",
            "git_branch": BRANCH, "ssh_key_id": k_none["id"]})
        print("  + repository: homelab")

    inv = first(call("GET", f"{P}/inventory"))
    if inv:
        print(f"  = inventory: {inv['name']}")
    else:
        k_ssh = key("ansible-ssh", {"type": "ssh", "ssh": {
            "login": "root", "passphrase": "", "private_key": read(SSH_KEY_FILE)}})
        inv = call("POST", f"{P}/inventory", {
            "name": "homelab", "project_id": pid, "type": "file", "inventory": "inventory/hosts.yml",
            "ssh_key_id": k_ssh["id"], "repository_id": repo["id"]})
        print("  + inventory: homelab")

    env = first(call("GET", f"{P}/environment"))
    if env:
        print(f"  = environment: {env['name']}")
    else:
        env = call("POST", f"{P}/environment", {"name": "default", "project_id": pid, "json": "{}", "env": "{}"})
        print("  + environment: default")

    vault = first(keys, type="login_password")
    if vault:
        print(f"  = vault key: {vault['name']}")
    else:
        vault = key("ansible-vault", {"type": "login_password", "login_password": {
            "login": "", "password": read(VAULT_FILE).strip()}})

    templates = call("GET", f"{P}/templates")

    def tmpl(name, playbook, **extra):
        found = first(templates, name)
        if found:
            print(f"  = template: {name}")
            return found
        body = {"project_id": pid, "name": name, "playbook": playbook, "app": "ansible", "type": "",
                "inventory_id": inv["id"], "repository_id": repo["id"], "environment_id": env["id"],
                "arguments": "[]", "allow_override_args_in_task": False,
                "vaults": [{"vault_key_id": vault["id"], "type": "password"}]}
        body.update(extra)
        made = call("POST", f"{P}/templates", body)
        print(f"  + template: {name}")
        return made

    patch = tmpl("OS patch (LXCs + Pi)", "os_update.yml")
    tmpl("Run playbook (site.yml)", "site.yml", allow_override_args_in_task=True)
    tmpl("Ad-hoc command", "adhoc.yml", survey_vars=[
        {"name": "target", "title": "Hosts or group (e.g. lxc_hosts, sandbox)", "type": "string", "required": True},
        {"name": "cmd", "title": "Shell command to run", "type": "string", "required": True}])

    if not first(call("GET", f"{P}/schedules"), "Weekly OS patch"):
        call("POST", f"{P}/schedules", {"project_id": pid, "template_id": patch["id"],
                                        "name": "Weekly OS patch", "cron_format": "0 4 * * 0", "active": True})
        print("  + schedule: Weekly OS patch (Sunday 04:00)")
    else:
        print("  = schedule: Weekly OS patch")
    print(f"\nDone. Open {BASE} -> {PROJECT} -> Task Templates.")


if __name__ == "__main__":
    main()
