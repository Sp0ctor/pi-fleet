# Three-copy fileshare backup: master → replica → Google Drive

## Layout
1. **Master Pi** `/mnt/storage/NAS` (SSD) – the working copy.
2. **Replica Pi** (OMV NAS) – Syncthing, two-way.
3. **Google Drive** – nightly `rclone copy` from the master ([script](../../master/scripts/backup-nas-to-gdrive)).

## Setting it up safely
1. **Inventory first.** Count files and bytes on the master; check Drive space with `rclone about gdrive:`.
2. **Verify the replica on its own.** A connected Syncthing peer doesn't prove the data matches. Compare a sorted
   list of relative path + size on both sides (`find . -type f -printf '%P %s\n' | sort`). A differing `.stfolder/` is normal.
3. **Use `copy`, never `sync`.** `rclone copy` adds and updates but never deletes on Drive, so a mistake on the
   master can't wipe the backup.
4. **Verify after the first run:** `rclone check /mnt/storage/NAS gdrive:nas-fileshare-backup --size-only` → 0 differences.
5. **Schedule it with a lock** (`flock -n`) so two runs can't overlap. See [crontab.example](../../master/crontab.example).

## Gotchas
- Big trees hit Drive API rate limits while updating folder timestamps even after files upload.
  `--no-update-dir-modtime --tpslimit 8 --tpslimit-burst 8` fixes it.
- An "empty token" error means the rclone remote needs re-authorizing. Never paste rclone config into chat or git.
- A backup that has never been restored is a hope. Test restoring a folder now and then.
- Deleting from the master "because it's backed up" quietly turns three copies into two. Decide on purpose.
