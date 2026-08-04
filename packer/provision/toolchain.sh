#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  curl \
  gdb \
  git \
  make \
  vim

# Blocca versione e SHA-256 di micro per ogni architettura supportata.
MICRO_VERSION="2.0.14"
MICRO_ARCH=""
MICRO_SHA256=""
case "$(uname -m)" in
  x86_64)
    MICRO_ARCH="linux64"
    MICRO_SHA256="704e96add9b44e0041179f7934338d330e85230af6869f70b88720830f554786"
    ;;
  aarch64)
    MICRO_ARCH="linux-arm64"
    MICRO_SHA256="2e01b3ea62cdea3e62eb3ee99f6bffe84de06f689cf479173c4e7221b6613d06"
    ;;
  *)
    echo "Architettura non supportata per micro: $(uname -m)" >&2
    exit 1
    ;;
esac
MICRO_TARBALL="micro-${MICRO_VERSION}-${MICRO_ARCH}.tar.gz"
MICRO_URL="https://github.com/zyedidia/micro/releases/download/v${MICRO_VERSION}/${MICRO_TARBALL}"
MICRO_TMPDIR="$(mktemp -d)"
trap 'rm -rf "${MICRO_TMPDIR}"' EXIT
curl -fsSL -o "${MICRO_TMPDIR}/${MICRO_TARBALL}" "${MICRO_URL}"
echo "${MICRO_SHA256}  ${MICRO_TMPDIR}/${MICRO_TARBALL}" | sha256sum -c
tar -xzf "${MICRO_TMPDIR}/${MICRO_TARBALL}" -C "${MICRO_TMPDIR}" "micro-${MICRO_VERSION}/micro"
install -m 755 "${MICRO_TMPDIR}/micro-${MICRO_VERSION}/micro" /usr/local/bin/micro
