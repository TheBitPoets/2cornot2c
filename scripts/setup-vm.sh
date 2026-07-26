#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

fail() {
  printf '\nERRORE: %s\n' "$1" >&2
  exit 1
}

command -v vagrant >/dev/null 2>&1 ||
  fail "Vagrant non è installato o non è disponibile nel PATH."
command -v VBoxManage >/dev/null 2>&1 ||
  fail "VirtualBox non è installato o non è disponibile nel PATH."

printf 'Controllo della configurazione...\n'
vagrant validate

printf '\nAvvio dell’ambiente didattico (il primo avvio può richiedere alcuni minuti)...\n'
vagrant up --provider=virtualbox

health_check='
set -eu
test "$(uname -m)" = "aarch64" -o "$(uname -m)" = "x86_64"
command -v gcc >/dev/null
command -v gdb >/dev/null
systemctl is-active --quiet vboxadd-service
findmnt -rn /lab >/dev/null
findmnt -rn /lab2 >/dev/null
'

printf '\nControllo automatico della macchina...\n'
if ! vagrant ssh -c "$health_check"; then
  printf 'Primo controllo non riuscito: provo un riavvio automatico...\n'
  vagrant reload
  vagrant ssh -c "$health_check" ||
    fail "La macchina è avviata, ma il controllo finale non è riuscito. Comunica questo messaggio al docente."
fi

printf '\nAMBIENTE PRONTO.\n'
printf 'La finestra grafica si apre automaticamente. Per il terminale usa: vagrant ssh\n'
