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
curl -fsSL -o "/tmp/${MICRO_TARBALL}" "${MICRO_URL}"
echo "${MICRO_SHA256}  /tmp/${MICRO_TARBALL}" | sha256sum -c
tar -xzf "/tmp/${MICRO_TARBALL}" -C /tmp "micro-${MICRO_VERSION}/micro"
install -m 755 "/tmp/micro-${MICRO_VERSION}/micro" /usr/local/bin/micro
rm -rf "/tmp/${MICRO_TARBALL}" "/tmp/micro-${MICRO_VERSION}"
