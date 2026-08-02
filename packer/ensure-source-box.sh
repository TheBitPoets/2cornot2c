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

: "${VAGRANT_HOME:?VAGRANT_HOME job-specifico non configurato}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lock_file="$script_dir/source-boxes.lock.json"

python_command=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' \
       >/dev/null 2>&1; then
    python_command="$candidate"
    break
  fi
done
if [ -z "$python_command" ]; then
  echo "Python 3 non disponibile." >&2
  exit 3
fi

locked_output="$(
  "$python_command" - "$lock_file" "$provider" <<'PY'
import json
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
provider = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
if set(payload) != {"schema_version", "boxes"}:
    raise SystemExit("Schema lock box sorgenti non valido.")
if payload["schema_version"] != "2cornot2c.packer-source-boxes.v1":
    raise SystemExit("Versione lock box sorgenti non supportata.")
boxes = payload["boxes"]
if set(boxes) != {"virtualbox", "vmware_desktop"}:
    raise SystemExit("Provider lock box sorgenti non validi.")
entry = boxes[provider]
if set(entry) != {"architecture", "version", "sha256", "size_bytes"}:
    raise SystemExit("Campi lock box sorgente non validi.")
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", entry["version"]):
    raise SystemExit("Versione box sorgente non valida.")
if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
    raise SystemExit("SHA-256 box sorgente non valido.")
if type(entry["size_bytes"]) is not int or entry["size_bytes"] <= 0:
    raise SystemExit("Dimensione box sorgente non valida.")
print(entry["version"])
print(entry["sha256"])
PY
)"

if [ "$(printf '%s\n' "$locked_output" | wc -l | tr -d ' ')" -ne 2 ]; then
  echo "Lock box sorgente incompleto." >&2
  exit 3
fi
locked_version="$(printf '%s\n' "$locked_output" | sed -n '1p')"
checksum="$(printf '%s\n' "$locked_output" | sed -n '2p')"
if [ "$version" != "$locked_version" ]; then
  echo "Versione sorgente non attestata: $version (attesa $locked_version)." >&2
  exit 3
fi

mkdir -p "$VAGRANT_HOME"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) chmod 0700 "$VAGRANT_HOME" ;;
esac

isolated_context="$(mktemp -d "${TMPDIR:-/tmp}/2cornot2c-vagrant-box.XXXXXX")"
cleanup() {
  rmdir "$isolated_context" 2>/dev/null || true
}
trap cleanup EXIT

cd "$isolated_context"
box_list="$(vagrant box list --machine-readable)"
if printf '%s\n' "$box_list" | grep -q ',box-name,'; then
  echo "VAGRANT_HOME contiene già una box; rifiuto una sorgente residua." >&2
  exit 4
fi
vagrant box add bento/ubuntu-24.04 \
  --box-version "$version" \
  --provider "$provider" \
  --checksum "$checksum" \
  --checksum-type sha256
