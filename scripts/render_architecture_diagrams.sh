#!/usr/bin/env bash
# Renderizza tutti i diagrammi Mermaid d'architettura in SVG.
# Richiede Node.js 20+, npx e la directory doc/architecture/diagrams/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIAGRAMS_DIR="${SCRIPT_DIR}/../doc/architecture/diagrams"

cd "${DIAGRAMS_DIR}"

MERMAID_CLI_VERSION="$(tr -d '[:space:]' < .mmd-version)"
if [[ ! "${MERMAID_CLI_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Errore: .mmd-version non contiene un semver valido." >&2
    exit 1
fi

command -v node >/dev/null 2>&1 || { echo "Errore: node non trovato. Installa Node.js 20+." >&2; exit 1; }
NODE_MAJOR="$(node -v | cut -d. -f1 | tr -d 'v')"
if [ "${NODE_MAJOR}" -lt 20 ]; then
    echo "Errore: Node.js ${NODE_MAJOR} non supportato. Richiesto Node.js 20+." >&2
    exit 1
fi
command -v npx >/dev/null 2>&1 || { echo "Errore: npx non trovato. Installa Node.js." >&2; exit 1; }

# Rimuove SVG orfani: file .svg senza corrispondente .mmd.
for svg in ./*.svg; do
    [ -e "${svg}" ] || continue
    src="${svg%.svg}.mmd"
    if [ ! -e "${src}" ]; then
        echo "Rimuovo SVG orfano: ${svg}"
        rm -f -- "${svg}"
    fi
done

shopt -s nullglob
for src in ./*.mmd; do
    dest="${src%.mmd}.svg"
    echo "Rendering ${src} -> ${dest}"
    npx -y "@mermaid-js/mermaid-cli@${MERMAID_CLI_VERSION}" -i "${src}" -o "${dest}" -p puppeteer-config.json
    # Assicura newline finale per coerenza POSIX.
    if [ "$(tail -c 1 "${dest}" | wc -l)" -eq 0 ]; then
        printf '\n' >> "${dest}"
    fi
done
shopt -u nullglob

echo "Tutti i diagrammi sono aggiornati."
