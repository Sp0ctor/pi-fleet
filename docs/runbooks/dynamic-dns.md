# Dynamic DNS (DuckDNS) check

The VPN endpoint is a DuckDNS name. An updater on the control Pi refreshes it and writes a small state file
(`last_ip`, `last_status`, `updated_at`). [duckdns_health_check.py](../../controller/scripts/duckdns_health_check.py)
verifies the update really worked.

**Healthy means all four agree:**
1. the updater's saved IP,
2. the current public IP (ipify, falling back to icanhazip / ifconfig.me),
3. the A record from Cloudflare DNS-over-HTTPS,
4. the A record from Google DNS-over-HTTPS.

Why two outside resolvers: the local Pi-hole cache can be stale, and DuckDNS answering `OK` only proves it accepted
the request, not that the world sees the new IP.

Never print or log the DuckDNS token; only the updater script reads it.
