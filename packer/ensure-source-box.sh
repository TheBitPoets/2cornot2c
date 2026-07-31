#!/usr/bin/env bash
set -euo pipefail

provider="${1:?Uso: $0 <vmware_desktop|virtualbox> <versione>}"
version="${2:?Uso: $0 <vmware_desktop|virtualbox> <versione>}"

case "$provider" in
  vmware_desktop|virtualbox) ;;
  *)
    echo "Provider non supportato: $provider" >&2
    exit 2
    ;;
esac

isolated_context="$(mktemp -d "${TMPDIR:-/tmp}/2cornot2c-vagrant-box.XXXXXX")"
cleanup() {
  rmdir "$isolated_context" 2>/dev/null || true
}
trap cleanup EXIT

cd "$isolated_context"
if vagrant box list | grep -Fq "bento/ubuntu-24.04 ($provider, $version"; then
  exit 0
fi

vagrant box add bento/ubuntu-24.04 \
  --box-version "$version" \
  --provider "$provider"
