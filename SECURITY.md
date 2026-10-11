# Security notes

- **No secrets in this repo.** Passwords come from `.env` files (gitignored); `.env.example` shows the names only.
  rclone, WireGuard, Syncthing and Cloudflare credentials stay on the devices and are never copied here.
- **Addresses are examples.** All IPs are `192.168.1.x` placeholders and hostnames are generic.
- **Least privilege.** Health checks are read-only and never use `sudo` except `sudo -n vcgencmd` for temperature.
  The dashboard is view-only.
- **Exposure.** Nothing is port-forwarded except WireGuard (UDP). The website goes out through a Cloudflare Tunnel.
- **Pre-push check.** `./scan_before_push.sh` blocks pushes containing keys, tokens, personal emails or real
  home-network addresses. Add any extra private words to a local `.denylist` file (gitignored), one per line.

Found something? Open an issue without including the sensitive value itself.
