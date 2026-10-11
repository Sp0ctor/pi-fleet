# Pi-hole privacy review (read-only first)

**Look before changing:** FTL health and listening scope, pending OS updates, failed units, disk, memory.
Then read (don't edit) `dns.upstreams`, `dns.EDNS0ECS`, `dns.dnssec`, `dns.queryLogging`,
`database.maxDBdays`, `misc.privacylevel` from `/etc/pihole/pihole.toml`, and list enabled blocklists.

**Priority order**
1. Security updates; confirm FTL comes back after reboot.
2. Turn off EDNS Client Subnet. It tells upstream resolvers part of your network address.
3. Use local Unbound with DNSSEC instead of a plaintext third-party resolver. Test DNSSEC before leaving it on.
4. Keep detailed query logs only as long as you actually need them for troubleshooting.
5. Add blocklists only for device brands you actually own. More lists ≠ more protection.

Changes to upstreams, logging, DNSSEC or blocklists can break streaming, logins or updates for the household.
Change one thing at a time and tell people first.
