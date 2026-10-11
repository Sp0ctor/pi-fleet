#!/usr/bin/env python3
"""Silent-on-healthy fleet watchdog for home Pi nodes.

Writes only when the fleet's health state changes. Designed for Hermes cron
with no_agent=True: empty stdout means no Telegram delivery.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

KEY = Path(os.environ.get("PI_FLEET_KEY", Path.home() / ".ssh/pi-fleet-keys/id_ed25519"))
STATE_PATH = Path.home() / ".hermes/state/pi_fleet_health_state.json"

# Edit these to match your network. Names matter: "Pi-hole" and "Master Pi / Ollama" get extra checks.
NODES = {
    "Master Pi / Ollama": "192.168.1.10",
    "Replica / NAS": "192.168.1.20",
    "Pi-hole": "192.168.1.30",
}
# This controller is part of the fleet and is probed locally, not over SSH.
LOCAL_NODES = {
    "Control Pi": "192.168.1.40",
}
REMOTE_PROBE = r'''
import json, subprocess

def call(args):
    try:
        p = subprocess.run(args, text=True, capture_output=True)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", "command-not-found"

def first_ok(commands):
    for command in commands:
        rc, out, _ = call(command)
        if rc == 0 and out:
            return out
    return "unavailable"

rc, disk, _ = call(["df", "-P", "/"])
disk_pct = None
if rc == 0:
    rows = disk.splitlines()
    if len(rows) > 1:
        disk_pct = int(rows[-1].split()[4].rstrip("%"))

rc, failed, _ = call(["systemctl", "--failed", "--no-legend", "--plain"])
failed_units = [line.split()[0] for line in failed.splitlines() if line.strip()]

temp = first_ok([["vcgencmd", "measure_temp"], ["sudo", "-n", "vcgencmd", "measure_temp"]])
throttled = first_ok([["vcgencmd", "get_throttled"], ["sudo", "-n", "vcgencmd", "get_throttled"]])
pihole_rc, pihole, _ = call(["pihole", "status"])
ollama_rc, ollama, _ = call(["systemctl", "is-active", "ollama"])

print(json.dumps({
    "disk_pct": disk_pct,
    "failed_units": failed_units,
    "temp": temp,
    "throttled": throttled,
    "pihole_status": pihole if pihole_rc == 0 else "not-installed",
    "ollama": ollama if ollama_rc == 0 else "inactive",
}))
'''


def run(args: list[str], *, timeout: int, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, input=input_text, capture_output=True, timeout=timeout)


def probe(name: str, host: str) -> list[str]:
    problems: list[str] = []
    ping = run(["ping", "-c1", "-W2", host], timeout=5)
    if ping.returncode != 0:
        return [f"{name} ({host}) is unreachable by ping"]
    ssh = run([
        "ssh", "-i", str(KEY), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=yes",
        f"pi@{host}", "python3 -",
    ], timeout=20, input_text=REMOTE_PROBE)
    if ssh.returncode != 0:
        return [f"{name} ({host}) responds to ping but SSH/probe failed: {ssh.stderr.strip()[:140]}"]
    try:
        data = json.loads(ssh.stdout)
    except json.JSONDecodeError:
        return [f"{name} ({host}) returned an unreadable health probe"]

    disk = data.get("disk_pct")
    if isinstance(disk, int) and disk >= 85:
        problems.append(f"{name}: root disk is {disk}% full")
    failed = data.get("failed_units") or []
    if failed:
        problems.append(f"{name}: failed unit(s): {', '.join(failed)}")
    temp = str(data.get("temp", ""))
    try:
        temp_c = float(temp.split("=")[1].split("'")[0])
        if temp_c >= 75:
            problems.append(f"{name}: CPU temperature is {temp_c:.1f}C")
    except (IndexError, ValueError):
        problems.append(f"{name}: unable to read CPU temperature")
    throttled = str(data.get("throttled", ""))
    if throttled not in {"throttled=0x0", "unavailable"}:
        problems.append(f"{name}: throttle/undervoltage state {throttled}")
    if name == "Pi-hole":
        status = str(data.get("pihole_status", ""))
        if "FTL is listening on port 53" not in status or "Pi-hole blocking is enabled" not in status:
            problems.append("Pi-hole: DNS FTL or blocking status is unhealthy")
    if name == "Master Pi / Ollama" and data.get("ollama") not in {"active", "unavailable"}:
        problems.append(f"Master Pi / Ollama: Ollama service is {data.get('ollama')}")
    return problems


def probe_local(name: str, host: str) -> list[str]:
    """Run the same health checks on the control Pi without SSH."""
    problems: list[str] = []
    local = run(["python3", "-c", REMOTE_PROBE], timeout=20)
    if local.returncode != 0:
        return [f"{name} ({host}) local health probe failed: {local.stderr.strip()[:140]}"]
    try:
        data = json.loads(local.stdout)
    except json.JSONDecodeError:
        return [f"{name} ({host}) returned an unreadable local health probe"]
    disk = data.get("disk_pct")
    if isinstance(disk, int) and disk >= 85:
        problems.append(f"{name}: root disk is {disk}% full")
    failed = data.get("failed_units") or []
    if failed:
        problems.append(f"{name}: failed unit(s): {', '.join(failed)}")
    temp = str(data.get("temp", ""))
    try:
        temp_c = float(temp.split("=")[1].split("'")[0])
        if temp_c >= 75:
            problems.append(f"{name}: CPU temperature is {temp_c:.1f}C")
    except (IndexError, ValueError):
        problems.append(f"{name}: unable to read CPU temperature")
    throttled = str(data.get("throttled", ""))
    if throttled not in {"throttled=0x0", "unavailable"}:
        problems.append(f"{name}: throttle/undervoltage state {throttled}")
    return problems


def load_previous() -> list[str]:
    try:
        payload = json.loads(STATE_PATH.read_text())
        prior = payload.get("problems", [])
        return prior if isinstance(prior, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def main() -> None:
    if not KEY.is_file():
        print("Fleet watchdog error: controller SSH key is missing.")
        return
    current: list[str] = []
    for name, host in NODES.items():
        try:
            current.extend(probe(name, host))
        except (OSError, subprocess.TimeoutExpired) as exc:
            current.append(f"{name} ({host}) probe error: {type(exc).__name__}")
    for name, host in LOCAL_NODES.items():
        try:
            current.extend(probe_local(name, host))
        except (OSError, subprocess.TimeoutExpired) as exc:
            current.append(f"{name} ({host}) local probe error: {type(exc).__name__}")
    current = sorted(set(current))
    previous = load_previous()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"problems": current}, indent=2) + "\n")
    if current == previous:
        return
    old, new = set(previous), set(current)
    messages: list[str] = []
    if new - old:
        messages.append("PI FLEET ALERT\n" + "\n".join(f"• {p}" for p in sorted(new - old)))
    if old - new:
        messages.append("PI FLEET RECOVERED\n" + "\n".join(f"• {p}" for p in sorted(old - new)))
    print("\n\n".join(messages))


if __name__ == "__main__":
    main()
