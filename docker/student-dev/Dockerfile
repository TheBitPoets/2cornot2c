ARG UBUNTU_BASE_IMAGE=ubuntu:24.04@sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90
FROM ${UBUNTU_BASE_IMAGE}

ARG UBUNTU_BASE_IMAGE
ARG UBUNTU_SNAPSHOT
ARG BUILD_ESSENTIAL_VERSION
ARG CA_CERTIFICATES_VERSION
ARG GCC_VERSION
ARG GDB_VERSION
ARG GIT_VERSION
ARG MAKE_VERSION
ARG NODEJS_VERSION
ARG PYTHON3_VERSION
ARG SQLITE3_VERSION
ARG VIM_TINY_VERSION
ARG STUDENT_DEV_VERSION
ARG SOURCE_REVISION

LABEL org.opencontainers.image.title="2cornot2c student development environment" \
      org.opencontainers.image.description="Ambiente Ubuntu leggero per i laboratori 2cornot2c" \
      org.opencontainers.image.source="https://github.com/TheBitPoets/2cornot2c" \
      org.opencontainers.image.version="${STUDENT_DEV_VERSION}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      io.2cornot2c.student-dev.base-image="${UBUNTU_BASE_IMAGE}" \
      io.2cornot2c.student-dev.ubuntu-snapshot="${UBUNTU_SNAPSHOT}"

ENV DEBIAN_FRONTEND=noninteractive

# ubuntu:24.04-minimal non include ancora il bundle CA. Il primo accesso allo
# snapshot disabilita soltanto la verifica TLS; firme Release e pacchetti APT
# restano verificate tramite ubuntu-keyring già presente nell'immagine base.
RUN printf '%s\n' \
      'Types: deb' \
      "URIs: https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}" \
      'Suites: noble noble-updates noble-backports noble-security' \
      'Components: main universe restricted multiverse' \
      'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg' \
      > /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get \
      -o Acquire::https::Verify-Peer=false \
      -o Acquire::https::Verify-Host=false \
      update \
    && apt-get \
      -o Acquire::https::Verify-Peer=false \
      -o Acquire::https::Verify-Host=false \
      install -y --no-install-recommends \
      "build-essential=${BUILD_ESSENTIAL_VERSION}" \
      "ca-certificates=${CA_CERTIFICATES_VERSION}" \
      "gcc=${GCC_VERSION}" \
      "gdb=${GDB_VERSION}" \
      "git=${GIT_VERSION}" \
      "make=${MAKE_VERSION}" \
      "nodejs=${NODEJS_VERSION}" \
      "python3=${PYTHON3_VERSION}" \
      "sqlite3=${SQLITE3_VERSION}" \
      "vim-tiny=${VIM_TINY_VERSION}" \
    && ln -s /usr/bin/vim.tiny /usr/local/bin/vim \
    && rm -rf /var/lib/apt/lists/*

# L'immagine Ubuntu ufficiale contiene già l'utente ubuntu (UID/GID 1000).
# Lo rinominiamo per conservare UID 1000: i file montati dal computer dello
# studente restano utilizzabili anche su host Linux.
RUN groupmod --new-name student ubuntu \
    && usermod --login student \
      --comment "2cornot2c student" \
      --home /home/student \
      --move-home \
      --shell /bin/bash \
      ubuntu \
    && install -d -o student -g student -m 0755 /workspace

ENV HOME=/home/student
WORKDIR /workspace
USER student

CMD ["/bin/bash"]
