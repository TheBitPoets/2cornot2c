#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
wrapper="$project_dir/scripts/vmware-vagrant.sh"
begin_marker="# >>> 2cornot2c VMware aliases >>>"
end_marker="# <<< 2cornot2c VMware aliases <<<"

case "$(basename "${SHELL:-}")" in
  zsh) rc_file="$HOME/.zshrc" ;;
  bash) rc_file="$HOME/.bashrc" ;;
  *)
    printf 'Shell non supportata: %s\n' "${SHELL:-sconosciuta}" >&2
    printf 'Sono supportate zsh e bash.\n' >&2
    exit 1
    ;;
esac

quote_for_shell() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

temporary_file="$(mktemp "${TMPDIR:-/tmp}/2cornot2c-aliases.XXXXXX")"
trap 'rm -f "$temporary_file"' EXIT

if [ -f "$rc_file" ]; then
  awk -v begin="$begin_marker" -v end="$end_marker" '
    $0 == begin { skip = 1; next }
    $0 == end { skip = 0; next }
    !skip { print }
  ' "$rc_file" > "$temporary_file"
fi

{
  printf '\n%s\n' "$begin_marker"
  printf "alias vm-up=%s\n" "$(quote_for_shell "$wrapper up")"
  printf "alias vm-halt=%s\n" "$(quote_for_shell "$wrapper halt")"
  printf "alias vm-ssh=%s\n" "$(quote_for_shell "$wrapper ssh")"
  printf "alias vm-status=%s\n" "$(quote_for_shell "$wrapper status")"
  printf "alias vm-reload=%s\n" "$(quote_for_shell "$wrapper reload")"
  printf "alias vm-provision=%s\n" "$(quote_for_shell "$wrapper provision")"
  printf '%s\n' "$end_marker"
} >> "$temporary_file"

install -m 0644 "$temporary_file" "$rc_file"

printf 'Alias VMware installati in %s:\n' "$rc_file"
printf '  vm-up  vm-halt  vm-ssh  vm-status  vm-reload  vm-provision\n'
printf 'Per attivarli ora esegui: source %s\n' "$rc_file"
