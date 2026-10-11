# OpenMediaVault: data disk didn't mount (looks like broken SSH)

**Symptoms:** key login succeeds, then hangs at `Entering interactive session`. Journal shows
`pam_systemd: Failed to create session: ... failed with 'dependency'`. Root disk may be full.

**Why:** OMV's `/etc/fstab` entry pointed at a disk UUID that no longer existed. systemd kept waiting for that
device, which broke login sessions – and apps had written into the empty mount-point folder on the SD card.

**Diagnose from the local console**
1. `df -h /` and `sudo du -xhd1 /srv /home /var | sort -h`
2. `sudo journalctl -b | grep -E 'session-[0-9]+\.scope|dependency failed|pam_systemd'`
3. `lsblk -f`, `ls -l /dev/disk/by-uuid/`, `findmnt /srv/dev-disk-by-uuid-<uuid>`
4. Mount the candidate disk read-only to confirm it's the right one: `sudo mount -o ro,noload /dev/sda1 /mnt`

**Fix**
- OMV owns its fstab block – fix it in OMV (Workbench or its RPC: update the filesystem record to the current UUID,
  then apply the `fstab` config). Don't hand-edit the generated block or leave a duplicate manual line.
- Never format or re-UUID the data disk.
- If the mount hides the `pi` user's home, re-check `~/.ssh` permissions (`755` home, `700` .ssh, `600` authorized_keys).

**Done when:** `findmnt` shows the right disk, root has free space, `ssh host 'hostname; df -h /'` returns, and
the journal has no more `pam_systemd` dependency errors.
