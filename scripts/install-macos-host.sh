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
  fail "Una VM VirtualBox è in esecuzione. Spegnila con vagrant halt."
fi

vmrun="/Applications/VMware Fusion.app/Contents/Library/vmrun"
if [ -x "$vmrun" ] &&
   ! "$vmrun" list 2>/dev/null | grep -q '^Total running VMs: 0$'; then
  fail "Una VM VMware è in esecuzione. Spegnila con vm-halt."
fi

printf 'Installazione host 2cornot2c per macOS Apple Silicon\n'
printf 'Componenti: Homebrew, Git, Vagrant, VirtualBox, VMware Fusion,\n'
printf 'Vagrant VMware Utility e plugin VMware.\n\n'
printf 'Le VM e i dati esistenti NON verranno eliminati.\n'

if $reinstall; then
  printf 'Modalità: reinstallazione dei componenti.\n'
else
  printf 'Modalità: installazione dei soli componenti mancanti.\n'
fi

printf '\nChiudi VirtualBox e VMware Fusion prima di continuare.\n'
read -r -p "Digita CONTINUA per procedere: " confirmation
[ "$confirmation" = "CONTINUA" ] || fail "Installazione annullata."

if ! command -v brew >/dev/null 2>&1; then
  printf '\n[1/7] Installazione di Homebrew...\n'
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
  printf '\n[1/7] Homebrew già installato.\n'
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

printf '\n[2/7] Installazione di Git...\n'
install_formula git

printf '\n[3/7] Installazione di Vagrant...\n'
install_cask vagrant

printf '\n[4/7] Installazione di VirtualBox...\n'
install_cask virtualbox

install_fusion=false
if [ ! -d "/Applications/VMware Fusion.app" ] || $reinstall; then
  install_fusion=true
fi

printf '\n[5/7] Installazione di VMware Fusion...\n'
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

printf '\n[6/7] Installazione di Vagrant VMware Utility...\n'
install_cask vagrant-vmware-utility

printf '\n[7/7] Installazione del plugin Vagrant VMware...\n'
if vagrant plugin list | grep -q '^vagrant-vmware-desktop '; then
  vagrant plugin update vagrant-vmware-desktop
else
  vagrant plugin install vagrant-vmware-desktop
fi

printf '\nVerifica finale...\n'
command -v git >/dev/null
command -v vagrant >/dev/null
command -v VBoxManage >/dev/null
[ -d "/Applications/VirtualBox.app" ]
[ -d "/Applications/VMware Fusion.app" ]
[ -x "/opt/vagrant-vmware-desktop/bin/vagrant-vmware-utility" ]
vagrant plugin list | grep -q '^vagrant-vmware-desktop '

printf '\nINSTALLAZIONE HOST COMPLETATA.\n'
printf 'Versione Git: %s\n' "$(git --version)"
printf 'Versione Vagrant: %s\n' "$(vagrant --version)"
printf 'Versione VirtualBox: %s\n' "$(VBoxManage --version)"
printf '\nPassaggi manuali finali:\n'
printf '1. Apri VirtualBox e autorizza le estensioni richieste da macOS.\n'
printf '2. Apri VMware Fusion e accetta licenza e autorizzazioni.\n'
printf '3. Riavvia il Mac se macOS lo richiede.\n'
printf '4. Clona o apri il progetto 2cornot2c.\n'
printf '5. Avvia la VM dalla sua directory con ./scripts/setup-vm.sh\n'
