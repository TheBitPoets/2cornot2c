#!/usr/bin/env bash
set -euo pipefail

fusion_download_url="https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion"
reinstall=false
homebrew_installer=""
fusion_mount=""

cleanup() {
  if [ -n "$homebrew_installer" ]; then
    rm -f "$homebrew_installer"
  fi
  if [ -n "$fusion_mount" ] && [ -d "$fusion_mount" ]; then
    hdiutil detach "$fusion_mount" >/dev/null 2>&1 || true
    rmdir "$fusion_mount" 2>/dev/null || true
  fi
}
trap cleanup EXIT

fail() {
  printf '\nERRORE: %s\n' "$1" >&2
  exit 1
}

ensure_homebrew_path() {
  brew_shellenv='eval "$(/opt/homebrew/bin/brew shellenv)"'
  case "$(basename "${SHELL:-}")" in
    bash) profile_file="$HOME/.bash_profile" ;;
    *) profile_file="$HOME/.zprofile" ;;
  esac
  touch "$profile_file"
  if ! grep -Fqx "$brew_shellenv" "$profile_file"; then
    printf '\n%s\n' "$brew_shellenv" >> "$profile_file"
  fi
  eval "$(/opt/homebrew/bin/brew shellenv)"
}

usage() {
  cat <<'EOF'
Uso: ./scripts/install-macos-host.sh [--reinstall]

Senza opzioni installa soltanto i componenti mancanti.
Con --reinstall reinstalla le applicazioni, ma conserva VM, box e dati Vagrant.
EOF
}

case "${1:-}" in
  "") ;;
  --reinstall) reinstall=true ;;
  --help|-h) usage; exit 0 ;;
  *) usage; fail "Opzione non riconosciuta: $1" ;;
esac

[ "$(uname -s)" = "Darwin" ] ||
  fail "Questo installer funziona soltanto su macOS."
[ "$(uname -m)" = "arm64" ] ||
  fail "Questa procedura è progettata per Mac Apple Silicon."

if command -v VBoxManage >/dev/null 2>&1 &&
   [ -n "$(VBoxManage list runningvms 2>/dev/null)" ]; then
  fail "Una VM VirtualBox legacy è in esecuzione. Spegnila con vagrant halt."
fi

vmrun="/Applications/VMware Fusion.app/Contents/Library/vmrun"
if [ -x "$vmrun" ] &&
   ! "$vmrun" list 2>/dev/null | grep -q '^Total running VMs: 0$'; then
  fail "Una VM VMware è in esecuzione. Spegnila con vm-halt."
fi

printf 'Installazione host 2cornot2c per macOS Apple Silicon\n'
printf 'Componenti: Homebrew, Git, Python, Vagrant, VMware Fusion,\n'
printf 'Vagrant VMware Utility, plugin VMware e box Packer ARM64.\n\n'
printf 'Le VM e i dati esistenti NON verranno eliminati.\n'

if $reinstall; then
  printf 'Modalità: reinstallazione dei componenti.\n'
else
  printf 'Modalità: installazione dei soli componenti mancanti.\n'
fi

printf '\nChiudi VMware Fusion prima di continuare.\n'
read -r -p "Digita CONTINUA per procedere: " confirmation
[ "$confirmation" = "CONTINUA" ] || fail "Installazione annullata."

if ! command -v brew >/dev/null 2>&1; then
  printf '\n[1/8] Installazione di Homebrew...\n'
  homebrew_installer="$(mktemp "${TMPDIR:-/tmp}/homebrew-install.XXXXXX")"
  curl --fail --location --proto '=https' --tlsv1.2 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh \
    --output "$homebrew_installer"
  /bin/bash "$homebrew_installer"
  rm -f "$homebrew_installer"
  homebrew_installer=""

  if [ -x /opt/homebrew/bin/brew ]; then
    ensure_homebrew_path
  fi
else
  printf '\n[1/8] Homebrew già installato.\n'
  if [ -x /opt/homebrew/bin/brew ]; then
    ensure_homebrew_path
  fi
fi

command -v brew >/dev/null 2>&1 ||
  fail "Homebrew non è disponibile. Chiudi e riapri il Terminale, poi riprova."

install_formula() {
  formula="$1"
  if brew list --formula "$formula" >/dev/null 2>&1; then
    if $reinstall; then
      brew reinstall "$formula"
    else
      printf '%s è già installato.\n' "$formula"
    fi
  else
    brew install "$formula"
  fi
}

install_cask() {
  cask="$1"
  if brew list --cask "$cask" >/dev/null 2>&1; then
    if $reinstall; then
      brew reinstall --cask "$cask"
    else
      printf '%s è già installato.\n' "$cask"
    fi
  else
    brew install --cask "$cask"
  fi
}

printf '\n[2/8] Installazione di Git...\n'
install_formula git

printf '\n[3/8] Installazione di Python 3.12...\n'
install_formula python@3.12

printf '\n[4/8] Installazione di Vagrant...\n'
install_cask vagrant

install_fusion=false
if [ ! -d "/Applications/VMware Fusion.app" ] || $reinstall; then
  install_fusion=true
fi

printf '\n[5/8] Installazione di VMware Fusion...\n'
if $install_fusion; then
  printf 'Broadcom richiede un account per scaricare VMware Fusion.\n'
  printf 'Si apre ora il portale ufficiale. Accedi e scarica il DMG per\n'
  printf 'Apple Silicon, senza spostarlo dalla cartella Download.\n'
  open "$fusion_download_url"
  printf '\nTrascina qui il file DMG scaricato, poi premi Invio:\n'
  read -r fusion_dmg
  fusion_dmg="${fusion_dmg#\'}"
  fusion_dmg="${fusion_dmg%\'}"
  fusion_dmg="${fusion_dmg#\"}"
  fusion_dmg="${fusion_dmg%\"}"
  fusion_dmg="${fusion_dmg//\\ / }"
  [ -f "$fusion_dmg" ] || fail "File DMG non trovato: $fusion_dmg"

  fusion_mount="$(mktemp -d "${TMPDIR:-/tmp}/vmware-fusion.XXXXXX")"
  hdiutil attach "$fusion_dmg" -nobrowse -mountpoint "$fusion_mount"
  fusion_app="$(find "$fusion_mount" -maxdepth 2 -type d \
    -name 'VMware Fusion.app' -print -quit)"

  if [ -z "$fusion_app" ]; then
    hdiutil detach "$fusion_mount" >/dev/null
    fail "VMware Fusion.app non è presente nel DMG selezionato."
  fi

  sudo ditto "$fusion_app" "/Applications/VMware Fusion.app"
  hdiutil detach "$fusion_mount" >/dev/null
  rmdir "$fusion_mount"
  fusion_mount=""
else
  printf 'VMware Fusion è già installato.\n'
fi

printf '\n[6/8] Installazione di Vagrant VMware Utility...\n'
install_cask vagrant-vmware-utility

printf '\n[7/8] Installazione del plugin Vagrant VMware...\n'
if vagrant plugin list | grep -q '^vagrant-vmware-desktop '; then
  vagrant plugin update vagrant-vmware-desktop
else
  vagrant plugin install vagrant-vmware-desktop
fi

printf '\nVerifica finale...\n'
command -v git >/dev/null
command -v vagrant >/dev/null
[ -d "/Applications/VMware Fusion.app" ]
[ -x "/opt/vagrant-vmware-desktop/bin/vagrant-vmware-utility" ]
vagrant plugin list | grep -q '^vagrant-vmware-desktop '

printf '\nINSTALLAZIONE HOST COMPLETATA.\n'
printf 'Versione Git: %s\n' "$(git --version)"
printf 'Versione Vagrant: %s\n' "$(vagrant --version)"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -d "$project_dir/.git" ] &&
   [ -f "$project_dir/requirements-utui.txt" ] &&
   [ -f "$project_dir/Vagrantfile" ] &&
   [ -f "$project_dir/installer/tui.py" ]; then
  printf '\n[8/8] Preparazione e avvio installer box Packer...\n'
  venv_dir="$project_dir/.installer-venv"
  /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv --clear "$venv_dir"
  "$venv_dir/bin/python" -m pip install --disable-pip-version-check \
    -r "$project_dir/requirements-utui.txt"
  cd "$project_dir"
  exec "$venv_dir/bin/python" -m installer.tui
fi

printf '\nPassaggi manuali finali:\n'
printf '1. Apri VMware Fusion e accetta licenza e autorizzazioni.\n'
printf '2. Riavvia il Mac se macOS lo richiede.\n'
printf '3. Clona o apri il progetto 2cornot2c.\n'
printf '4. Esegui di nuovo ./scripts/install-macos-host.sh dal progetto.\n'
