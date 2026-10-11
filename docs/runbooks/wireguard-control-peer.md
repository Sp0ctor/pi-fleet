# Adding a separate WireGuard peer for a management machine

Goal: let the control Pi reach a remote network through PiVPN **without** reusing a laptop's client profile.

1. **Find the real server.** On the suspected host: `pivpn -c` and `sudo wg show`. If it has `wg0` and peers,
   that's the server. List used tunnel IPs; don't take an address that's only "inactive".
2. **New identity.** Generate a fresh keypair on the control Pi (`umask 077; wg genkey | tee priv | wg pubkey > pub`).
   Never copy another client's private or preshared key.
3. **Narrow interface** (e.g. `remote-control.conf`): new address, server public key, DDNS endpoint,
   `PersistentKeepalive = 25`, and `AllowedIPs` limited to the tunnel subnet + the one remote LAN you manage.
   No full tunnel – it would route the control Pi's own traffic through the other site.
4. **Add the peer on the server live:**
   ```bash
   sudo cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.bak-$(date +%F-%H%M%S)
   printf '\n[Peer]\nPublicKey = <CONTROL_PUBKEY>\nAllowedIPs = <TUNNEL_IP>/32\n' | sudo tee -a /etc/wireguard/wg0.conf >/dev/null
   sudo wg set wg0 peer <CONTROL_PUBKEY> allowed-ips <TUNNEL_IP>/32
   ```
   Don't use `wg-quick save wg0` – it rewrites the PiVPN file and drops its `PostUp`/`PostDown` firewall rules.
5. **Prove it:** a recent handshake + bytes received in `wg show`, **and** an SSH command with strict host-key checking.
6. `sudo systemctl enable wg-quick@remote-control` so it survives reboots.
