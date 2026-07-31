#!/usr/bin/env bash
set -euo pipefail

provider="${1:?Uso: $0 <vmware_desktop|virtualbox> <file.box>}"
box_file="${2:?Uso: $0 <vmware_desktop|virtualbox> <file.box>}"

case "$provider" in
  vmware_desktop|virtualbox) ;;
  *)
    echo "Provider non supportato: $provider" >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
box_file="$(cd "$(dirname "$box_file")" && pwd)/$(basename "$box_file")"
box_name="2cornot2c/acceptance-${provider}"
dotfile_path=".vagrant-${provider}"

cleanup() {
  VAGRANT_DOTFILE_PATH="$dotfile_path" vagrant destroy --force >/dev/null 2>&1 || true
  vagrant box remove "$box_name" --provider "$provider" --force >/dev/null 2>&1 || true
}
trap cleanup EXIT

test -f "$box_file"

vagrant box add "$box_name" "$box_file" --provider "$provider" --force

export CLASSROOM_BOX_NAME="$box_name"
export CLASSROOM_REPO_ROOT="$repo_root"
export CLASSROOM_MEMORY_MB="${CLASSROOM_MEMORY_MB:-2048}"
export VAGRANT_DOTFILE_PATH="$dotfile_path"

cd "$script_dir"
vagrant up --provider "$provider"
vagrant ssh -c '
  set -eu
  sudo /usr/local/bin/2cornot2c-health-check
  test "$(stat -c %a /home/vagrant/2cornot2c)" != ""
  test -x /home/vagrant/cambia-risoluzione.sh || test "'"$provider"'" = virtualbox
  systemctl is-active --quiet display-manager
  pgrep -u vagrant -x xfce4-session >/dev/null
  swapon --show --noheadings | grep -q zram
  free -m
  gcc --version | head -n 1
  vmtoolsd --version 2>/dev/null || VBoxControl --version
'

echo "Acceptance test superato per $provider."
