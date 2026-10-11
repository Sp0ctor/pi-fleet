# Replica Pi: OpenMediaVault NAS

Second copy of the shared files, on a Pi 4 with a USB SSD.

- **OS:** OpenMediaVault on Debian 12. The data disk is mounted by OMV at `/srv/dev-disk-by-uuid-<uuid>/`.
- **Sharing:** Samba share for Windows/Mac clients.
- **Replication:** Syncthing (native service), folder shared two-way with the master Pi's `/mnt/storage/NAS`.
  No file versioning yet; the off-site copy is the master's nightly Google Drive backup.
- **Monitoring:** collectd (OMV graphs) plus the control Pi's watchdog.

Lesson learned: if the data disk ever fails to mount, apps write into the empty mount-point folder on the SD card,
the root filesystem fills, and SSH starts hanging right after login. See
[docs/runbooks/omv-missing-mount.md](../docs/runbooks/omv-missing-mount.md).
