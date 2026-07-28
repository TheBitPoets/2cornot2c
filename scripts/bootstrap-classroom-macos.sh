#!/usr/bin/env bash
set -euo pipefail

repository_url="${CLASSROOM_REPOSITORY_URL:-https://github.com/TheBitPoets/2cornot2c.git}"
install_dir="${CLASSROOM_INSTALL_DIR:-$HOME/2cornot2c}"
brew_prefix="/opt/homebrew"

fail() {
  printf '\nERRORE: %s\n' "$1" >&2
  exit 1
}

[ "$(uname -s)" = "Darwin" ] || fail "Questo bootstrap richiede macOS."
[ "$(uname -m)" = "arm64" ] || fail "Sono supportati soltanto Mac Apple Silicon."

printf 'Bootstrap ambiente didattico 2cornot2c\n'
printf 'Directory: %s\n\n' "$install_dir"

if ! command -v brew >/dev/null 2>&1; then
  printf '[1/5] Installazione Homebrew...\n'
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl --fail --silent --show-error --location \
      https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if [ -x "$brew_prefix/bin/brew" ]; then
  eval "$("$brew_prefix/bin/brew" shellenv)"
fi
command -v brew >/dev/null 2>&1 || fail "Homebrew non è disponibile."

printf '[2/5] Preparazione Git e Python 3.12...\n'
brew list --formula git >/dev/null 2>&1 || brew install git
brew list --formula python@3.12 >/dev/null 2>&1 || brew install python@3.12

printf '[3/5] Preparazione repository...\n'
if [ -d "$install_dir/.git" ]; then
  git -C "$install_dir" pull --ff-only
elif [ -e "$install_dir" ]; then
  fail "La directory esiste ma non è un repository Git: $install_dir"
else
  git clone "$repository_url" "$install_dir"
fi

printf '[4/5] Preparazione interfaccia guidata...\n'
python_bin="$brew_prefix/bin/python3.12"
[ -x "$python_bin" ] || fail "Python 3.12 non è disponibile in $python_bin."
"$python_bin" -m venv "$install_dir/.installer-venv"
"$install_dir/.installer-venv/bin/python" -m pip install \
  --disable-pip-version-check \
  -r "$install_dir/requirements-utui.txt"

printf '[5/5] Avvio procedura guidata...\n'
cd "$install_dir"
exec "$install_dir/.installer-venv/bin/python" -m installer.tui
