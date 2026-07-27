#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/* /var/tmp/*
rm -f /home/vagrant/.bash_history
find /var/log -type f -exec truncate -s 0 {} \;

sync
