#!/usr/bin/env bash
# One-time preparation of the Auto Expert server (deploy prompt, stage B.3–B.5). Run as root AFTER
# inspect.sh showed nothing of other projects that this could break:
#   scp -r deploy/server root@SERVER:/root/autoexpert-server && ssh root@SERVER bash /root/autoexpert-server/bootstrap.sh
# What it does (idempotent):
#   - user "deploy" (no password, SSH key only, docker group), key copied from root
#   - SSH: key login only; root without password (prohibit-password); config checked before reload
#   - firewall ufw: only 22, 80, 443 incoming; fail2ban for sshd; automatic security updates
#   - Docker Engine + Compose plugin from Docker's repository, log rotation
#   - swap 2 GB; folders /srv/autoexpert/*; systemd timers (backup, health, recalls)
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "run as root"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_USER=deploy
export DEBIAN_FRONTEND=noninteractive

echo "== packages"
apt-get update -q
apt-get install -y -q ca-certificates curl gnupg ufw fail2ban unattended-upgrades apt-listchanges cron

echo "== user ${DEPLOY_USER}"
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "Auto Expert deploy" "$DEPLOY_USER"
fi
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
if [ -s /root/.ssh/authorized_keys ]; then
  install -m 600 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/authorized_keys"
fi
# sudo only for the service units (no general root)
cat > /etc/sudoers.d/autoexpert <<EOF
$DEPLOY_USER ALL=(root) NOPASSWD: /usr/bin/systemctl start autoexpert-*, /usr/bin/systemctl restart autoexpert-*, /usr/bin/systemctl status autoexpert-*, /usr/sbin/reboot
EOF
chmod 440 /etc/sudoers.d/autoexpert
visudo -cf /etc/sudoers.d/autoexpert

echo "== ssh: key only"
cat > /etc/ssh/sshd_config.d/10-autoexpert.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
MaxAuthTries 4
EOF
sshd -t && systemctl reload ssh 2>/dev/null || systemctl reload sshd

echo "== firewall"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "== fail2ban"
cat > /etc/fail2ban/jail.d/autoexpert.local <<'EOF'
[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

echo "== automatic security updates"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
systemctl enable --now unattended-upgrades

echo "== docker"
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
cat > /etc/docker/daemon.json <<'EOF'
{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "5"}, "live-restore": true}
EOF
systemctl enable docker containerd
systemctl restart docker
usermod -aG docker "$DEPLOY_USER"

echo "== swap 2 GB"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
echo 'vm.swappiness=10' > /etc/sysctl.d/90-autoexpert.conf
sysctl --system >/dev/null

echo "== folders"
install -d -m 755 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /srv/autoexpert /srv/autoexpert/releases /srv/autoexpert/vpic /srv/autoexpert/logs
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /srv/autoexpert/shared /srv/autoexpert/backups
install -d -m 755 -o 10001 -g 10001 /srv/autoexpert/media   # the backend container's user
install -m 755 "$HERE/backup.sh" "$HERE/health.sh" /usr/local/bin/
cp "$HERE"/systemd/*.service "$HERE"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now autoexpert-backup.timer autoexpert-health.timer autoexpert-recalls.timer
cat > /etc/logrotate.d/autoexpert <<'EOF'
/srv/autoexpert/logs/*.log {
  weekly
  rotate 8
  compress
  missingok
  notifempty
}
EOF

echo "== done. Check: ssh ${DEPLOY_USER}@<server> in a NEW terminal before closing this one."
