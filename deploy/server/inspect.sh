#!/usr/bin/env bash
# Read-only inventory of the server before anything is installed (deploy prompt, stage B.2).
# Changes nothing. Usage: ssh root@SERVER 'bash -s' < deploy/server/inspect.sh
set -u
section() { printf '\n===== %s =====\n' "$1"; }

section "system"
hostnamectl 2>/dev/null || hostname
cat /etc/os-release 2>/dev/null | grep -E '^(PRETTY_NAME|VERSION_ID)='
uname -r
uptime
section "memory and swap"
free -h
swapon --show 2>/dev/null
section "disk"
df -h -x tmpfs -x devtmpfs
section "listening ports"
ss -tulpn 2>/dev/null
section "running services (systemd)"
systemctl list-units --type=service --state=running --no-pager --no-legend 2>/dev/null
section "enabled timers"
systemctl list-timers --no-pager 2>/dev/null | head -20
section "docker"
if command -v docker >/dev/null 2>&1; then
  docker --version; docker compose version 2>/dev/null
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null
  docker volume ls 2>/dev/null
else
  echo "docker: not installed"
fi
section "web servers / databases installed"
for p in nginx apache2 caddy postgresql mysql mariadb redis-server; do
  if dpkg -l "$p" 2>/dev/null | grep -q '^ii'; then echo "installed: $p"; fi
done
section "users with a login shell"
awk -F: '$7 ~ /(bash|sh|zsh)$/ {print $1" uid="$3" home="$6}' /etc/passwd
section "ssh settings"
sshd -T 2>/dev/null | grep -Ei '^(permitrootlogin|passwordauthentication|pubkeyauthentication|port) '
section "firewall"
ufw status verbose 2>/dev/null || echo "ufw: not installed"
command -v fail2ban-client >/dev/null && fail2ban-client status 2>/dev/null || echo "fail2ban: not installed"
section "cron"
crontab -l 2>/dev/null || echo "root crontab: empty"
ls /etc/cron.d 2>/dev/null
section "big directories in /srv /opt /home /var/www"
du -sh /srv/* /opt/* /home/* /var/www/* 2>/dev/null | sort -h | tail -15
section "end"
