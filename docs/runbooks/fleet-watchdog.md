# Silent fleet watchdog + read-only dashboard

## Watchdog ([pi_fleet_health_check.py](../../controller/scripts/pi_fleet_health_check.py))
- Runs only on the control Pi (the one machine with the fleet key).
- Per node: ping, then key-only SSH (`BatchMode`, `IdentitiesOnly`, `StrictHostKeyChecking=yes`) running a small
  Python probe: root disk %, `systemctl --failed`, `vcgencmd measure_temp` / `get_throttled`,
  Pi-hole status on the DNS node, Ollama state on the master.
- Saves the current problem set to `~/.hermes/state/`. Prints only **new** problems and **recoveries**.
  Empty output = no message, so a healthy fleet is silent.
- Thresholds: disk ≥ 85 %, CPU ≥ 75 °C, any non-zero throttle flag, any failed unit.

**Bug worth knowing:** calling `pihole` on a node without Pi-hole raises `FileNotFoundError` inside the probe.
Without catching it, a healthy fleet looks broken. The probe wraps every command.

**Before scheduling:** run it twice by hand. Both healthy runs must exit 0 and print nothing. Then run every 30 min:
`hermes cron create "*/30 * * * *" --name "Pi fleet watchdog" --script pi_fleet_health_check.py --no-agent --deliver telegram`

## Dashboard ([Homepage](../../master/docker/homepage/))
- One card per physical Pi; Pi's with two NICs list both addresses but ping the reliable one.
- Read-only: no SSH keys, no API tokens, no update buttons in browser-visible YAML.
- Bound to the LAN IP only (`192.168.1.10:3000`), not `0.0.0.0`.
- Check every URL with `curl` before adding it as a `siteMonitor`.
- After editing compose: `docker compose config` then `docker compose up -d --force-recreate homepage`, and confirm
  with `docker inspect` that the port is really mapped. A container can show "healthy" while running an old config.
