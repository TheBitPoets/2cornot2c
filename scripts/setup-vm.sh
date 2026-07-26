#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

fail() {
  printf '\nERRORE: %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Uso: ./scripts/setup-vm.sh [--virtualbox|--vmware]

Su macOS senza opzioni viene mostrata la scelta del provider.
Su Windows usa setup-vm.cmd: VirtualBox viene scelto automaticamente.
EOF
}

command -v vagrant >/dev/null 2>&1 ||
  fail "Vagrant non è installato o non è disponibile nel PATH."

provider=""
case "${1:-}" in
  --virtualbox) provider="virtualbox" ;;
  --vmware) provider="vmware_desktop" ;;
  --help|-h) usage; exit 0 ;;
  "") ;;
  *) usage; fail "Opzione non riconosciuta: $1" ;;
esac

if [ -z "$provider" ]; then
  if [ "$(uname -s)" = "Darwin" ] && [ -t 0 ]; then
    printf 'Scegli il motore della macchina virtuale:\n'
    printf '  1) VirtualBox (soluzione stabile con finestra scalata)\n'
    printf '  2) VMware Fusion (spike sperimentale)\n'
    printf 'Scelta [1]: '
    read -r provider_choice
    case "$provider_choice" in
      ""|1) provider="virtualbox" ;;
      2) provider="vmware_desktop" ;;
      *) fail "Scelta non valida." ;;
    esac
  else
    provider="virtualbox"
  fi
fi

state_dir=".vagrant"
provider_health_check='systemctl is-active --quiet vboxadd-service'

if [ "$provider" = "virtualbox" ]; then
  command -v VBoxManage >/dev/null 2>&1 ||
    fail "VirtualBox non è installato o non è disponibile nel PATH."
else
  [ "$(uname -s)" = "Darwin" ] ||
    fail "La spike VMware è abilitata soltanto su macOS."
  [ -d "/Applications/VMware Fusion.app" ] ||
    fail "VMware Fusion non è installato in /Applications."
  vagrant plugin list | grep -q '^vagrant-vmware-desktop ' ||
    fail "Manca il plugin Vagrant VMware: vagrant plugin install vagrant-vmware-desktop"
  [ -x "/opt/vagrant-vmware-desktop/bin/vagrant-vmware-utility" ] ||
    fail "Manca Vagrant VMware Utility."
  state_dir=".vagrant-vmware"
  provider_health_check='pgrep -x vmtoolsd >/dev/null'
fi

run_vagrant() {
  VAGRANT_DOTFILE_PATH="$state_dir" vagrant "$@"
}

printf 'Controllo della configurazione...\n'
run_vagrant validate

printf '\nAvvio dell’ambiente didattico con %s (il primo avvio può richiedere alcuni minuti)...\n' "$provider"
run_vagrant up --provider="$provider"

health_check="
set -eu
test \"\$(uname -m)\" = \"aarch64\" -o \"\$(uname -m)\" = \"x86_64\"
command -v gcc >/dev/null
command -v gdb >/dev/null
$provider_health_check
systemctl is-active --quiet lightdm
findmnt -rn /lab >/dev/null
findmnt -rn /lab2 >/dev/null
"

printf '\nControllo automatico della macchina...\n'
if ! run_vagrant ssh -c "$health_check"; then
  printf 'Primo controllo non riuscito: provo un riavvio automatico...\n'
  run_vagrant reload
  run_vagrant ssh -c "$health_check" ||
    fail "La macchina è avviata, ma il controllo finale non è riuscito. Comunica questo messaggio al docente."
fi

printf '\nAMBIENTE PRONTO.\n'
printf 'La finestra grafica si apre automaticamente.\n'
if [ "$provider" = "vmware_desktop" ]; then
  printf 'Per il terminale usa: VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant ssh\n'
else
  printf 'Per il terminale usa: vagrant ssh\n'
fi
