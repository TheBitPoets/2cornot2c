#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if [ "${1:-}" = "up" ]; then
  shift
  VAGRANT_DOTFILE_PATH=.vagrant-vmware \
    vagrant up --provider=vmware_desktop "$@"
else
  VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant "$@"
fi
