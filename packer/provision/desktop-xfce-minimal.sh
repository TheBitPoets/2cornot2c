#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get install -y --no-install-recommends \
  dbus-x11 \
  fonts-dejavu-core \
  lightdm \
  lightdm-gtk-greeter \
  policykit-1 \
  thunar \
  xfce4-panel \
  xfce4-session \
  xfce4-settings \
  xfce4-terminal \
  xfdesktop4 \
  xfwm4 \
  xinit \
  xserver-xorg-core \
  xserver-xorg-input-all \
  xserver-xorg-video-all \
  x11-xserver-utils \
  zram-tools

if command -v vmtoolsd >/dev/null 2>&1; then
  apt-get install -y --no-install-recommends open-vm-tools-desktop
fi

install -d -m 0755 /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/50-vagrant-autologin.conf <<'EOF'
[Seat:*]
autologin-user=vagrant
autologin-user-timeout=0
user-session=xfce
EOF

usermod -aG nopasswdlogin vagrant
systemctl enable lightdm
systemctl set-default graphical.target

cat > /etc/default/zramswap <<'EOF'
ALGO=zstd
PERCENT=25
PRIORITY=100
EOF
systemctl enable zramswap

install -d -o vagrant -g vagrant -m 0700 /home/vagrant/.config/xfce4/xfconf/xfce-perchannel-xml
cat > /home/vagrant/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Xft" type="empty">
    <property name="DPI" type="int" value="120"/>
  </property>
  <property name="Gtk" type="empty">
    <property name="FontName" type="string" value="Sans 11"/>
  </property>
</channel>
EOF
chown -R vagrant:vagrant /home/vagrant/.config
