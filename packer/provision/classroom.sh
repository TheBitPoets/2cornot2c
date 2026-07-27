#!/usr/bin/env bash
set -euo pipefail

echo "vagrant:vagrant" | chpasswd

install -d -m 0755 /opt/2cornot2c

if command -v vmtoolsd >/dev/null 2>&1 && [ -f /tmp/change-resolution.sh ]; then
  sed 's/\r$//' /tmp/change-resolution.sh > /home/vagrant/cambia-risoluzione.sh
  chown vagrant:vagrant /home/vagrant/cambia-risoluzione.sh
  chmod 0755 /home/vagrant/cambia-risoluzione.sh
fi
rm -f /tmp/change-resolution.sh

cat > /usr/local/bin/2cornot2c-health-check <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

command -v gcc >/dev/null
command -v gdb >/dev/null
command -v make >/dev/null
command -v git >/dev/null
command -v vim >/dev/null
test -f /etc/lightdm/lightdm.conf.d/50-vagrant-autologin.conf
systemctl is-enabled --quiet lightdm

if command -v VBoxControl >/dev/null 2>&1; then
  systemctl is-enabled --quiet vboxadd-service
elif command -v vmtoolsd >/dev/null 2>&1; then
  test -x /usr/bin/vmtoolsd
else
  echo "Guest Tools del provider non trovati." >&2
  exit 1
fi
EOF
chmod 0755 /usr/local/bin/2cornot2c-health-check

/usr/local/bin/2cornot2c-health-check
