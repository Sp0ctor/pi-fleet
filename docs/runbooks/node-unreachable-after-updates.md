# A node disappears after updates

A Pi that needed a reboot after `apt full-upgrade` can drop off the network (or come back on a new DHCP address).

**Check, in order:**
```bash
ssh -i "$PI_FLEET_KEY" -o BatchMode=yes -o ConnectTimeout=5 pi@192.168.1.10 'hostname; uptime -p'
ping -c 3 -W 2 192.168.1.10
ip neigh show 192.168.1.10          # INCOMPLETE/FAILED = nothing answering at that address
getent hosts raspberrypi.local      # did it come back somewhere else?
~/bin/pi-fleet-status
```

**Report honestly:** if ping and SSH both fail, say it's offline or moved. Never present old container/service
lists as current – label them "last known".

**Prevent it:** give every Pi a DHCP reservation on the router.
