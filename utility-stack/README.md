# Security & Maintenance Stack

Handles network-wide ad-blocking and local DNS hygiene running inside LXC container **CT105** (`192.168.0.136`).

## Services

* **Pi-hole v6:** Network-wide DNS sinkhole and ad-blocker.

## Notes

* Configured with custom local DNS records to map all `*.salmanslab.duckdns.org` subdomains directly to the internal Nginx Proxy Manager IP (`192.168.0.128`).
* Keeps internal traffic local, preventing hairpining or traffic leaving the local network.
* Acts as the primary upstream DNS server for the home network.
