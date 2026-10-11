#!/usr/bin/env python3
"""Quiet DuckDNS health watchdog (set DUCKDNS_DOMAIN, e.g. myhome.duckdns.org).

Exits silently when the current public IPv4, the DuckDNS A record, and the
most recent updater state agree. Prints a concise alert only on a discrepancy
or an inability to verify; suitable for Hermes cron ``no_agent`` delivery.
"""
from __future__ import annotations

import ipaddress
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DOMAIN = os.environ.get("DUCKDNS_DOMAIN", "myhome.duckdns.org")
STATE_PATH = Path.home() / ".hermes" / "state" / "duckdns_state.json"  # written by your updater: {"last_ip": "...", "last_status": "OK", "updated_at": "..."}
IP_SERVICES = (
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://ifconfig.me/ip",
)


def valid_ipv4(value: str) -> str | None:
    try:
        ip = ipaddress.ip_address(value.strip())
        return str(ip) if ip.version == 4 and ip.is_global else None
    except ValueError:
        return None


def public_ip() -> str:
    errors: list[str] = []
    for url in IP_SERVICES:
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                ip = valid_ipv4(response.read().decode("utf-8", "replace"))
            if ip:
                return ip
            errors.append("invalid response")
        except Exception as exc:
            errors.append(type(exc).__name__)
    raise RuntimeError("public-IP lookup failed (" + ", ".join(errors) + ")")


def duckdns_answers() -> dict[str, set[str]]:
    resolvers = {
        "Cloudflare": "https://cloudflare-dns.com/dns-query",
        "Google": "https://dns.google/resolve",
    }
    results: dict[str, set[str]] = {}
    errors: list[str] = []
    for name, endpoint in resolvers.items():
        try:
            url = endpoint + "?" + urllib.parse.urlencode({"name": DOMAIN, "type": "A"})
            request = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8", "replace"))
            answers = {valid_ipv4(str(item.get("data", ""))) for item in payload.get("Answer", []) if item.get("type") == 1}
            answers.discard(None)
            results[name] = answers
        except Exception as exc:
            errors.append(f"{name}:{type(exc).__name__}")
    if not results:
        raise RuntimeError("public DNS lookup failed (" + ", ".join(errors) + ")")
    return results


def saved_ip() -> str | None:
    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8")).get("last_ip", "")
        return valid_ipv4(str(value))
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError):
        return None


def main() -> int:
    try:
        current = public_ip()
        resolver_answers = duckdns_answers()
        state_ip = saved_ip()
    except Exception as exc:
        print(f"DuckDNS health check could not verify {DOMAIN}: {exc}")
        return 1

    problems: list[str] = []
    mismatched_resolvers = [name for name, answers in resolver_answers.items() if current not in answers]
    if mismatched_resolvers:
        problems.append("public DNS record does not match the current public IPv4 at " + ", ".join(mismatched_resolvers))
    if state_ip is None:
        problems.append("no valid recent updater state is available")
    elif state_ip != current:
        problems.append("updater state does not match the current public IPv4")

    if problems:
        # In no_agent cron mode, non-empty stdout is delivered as the alert.
        # A mismatch is a successful detection, not a watchdog execution failure.
        print(f"DuckDNS alert for {DOMAIN}: " + "; ".join(problems) + ".")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
