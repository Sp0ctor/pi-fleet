# DNS Pi: Pi-hole + Unbound + PiVPN

Every device on the network uses this Pi for DNS (set as the router's DHCP DNS server).

```
device → Pi-hole (:53, blocks ads/trackers) → Unbound (127.0.0.1:5335, validating recursive resolver) → root servers
```

## Pi-hole
- Installed natively (`curl -sSL https://install.pi-hole.net | bash`), upstream set to `127.0.0.1#5335` only.
- Privacy settings worth checking (`/etc/pihole/pihole.toml`): `dns.EDNS0ECS = false` (stops leaking
  your subnet to upstreams), `dns.dnssec`, `database.maxDBdays`, `misc.privacylevel`.
- Don't add dynamic-DNS blocklists if you rely on DuckDNS for the VPN.
- See [docs/runbooks/pihole-privacy-review.md](../docs/runbooks/pihole-privacy-review.md).

## Unbound
- Native install, listens on `127.0.0.1:5335`. Standard Pi-hole guide config
  (`/etc/unbound/unbound.conf.d/pi-hole.conf`). Test DNSSEC:
  `dig fail01.dnssec.works @127.0.0.1 -p 5335` should return SERVFAIL; `dig dnssec.works ...` should return NOERROR.
- A containerized alternative lives in `master/docker/unbound/`.

## PiVPN (WireGuard)
- `curl -L https://install.pivpn.io | bash`, WireGuard, port UDP 51820 forwarded on the router.
- Endpoint is a DuckDNS name so a changing home IP doesn't break clients; the control Pi checks the record
  ([duckdns_health_check.py](../controller/scripts/duckdns_health_check.py)).
- One profile per device: `pivpn add -n phone`, `pivpn -qr phone` to show a QR code. Clients use the Pi-hole for DNS.
- Adding a separate management peer: [docs/runbooks/wireguard-control-peer.md](../docs/runbooks/wireguard-control-peer.md).
