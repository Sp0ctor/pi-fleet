# SSH authenticates, then hangs

**Symptoms:** ping works, port 22 is open, the key is accepted (`ssh -vvv` shows `Authenticated to ...`),
then nothing – or commands randomly take 30+ seconds.

**Most likely cause: the root filesystem is 100 % full.** Starting a login session needs small writes
(PAM, logind, MOTD, logs). With zero free space the session never opens.

```bash
ssh host 'df -hT /'
ssh host 'du -xsh /home /var /opt /srv /tmp /mnt 2>/dev/null'
ssh host 'journalctl --disk-usage'
ssh host 'find ~ -xdev -type f -size +500M -printf "%s %p\n" | sort -n | tail'
```
Avoid `du -xhd1 /` on a nearly-full disk; it can hang for minutes.

**Don't** run `apt upgrade` until there are a few GB free – a half-configured package system is worse.
Free space first (and ask before deleting anything you didn't create).

On an OMV box, also check for a data disk that didn't mount: see [omv-missing-mount.md](omv-missing-mount.md).
