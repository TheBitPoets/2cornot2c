ARG DEBIAN_BASE_IMAGE=debian:bookworm-slim@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818
FROM ${DEBIAN_BASE_IMAGE}

ARG DEBIAN_BASE_IMAGE
ARG DEBIAN_SNAPSHOT
ARG GCC_VERSION
ARG LIBC6_DEV_VERSION
ARG NODEJS_VERSION
ARG PYTHON3_VERSION
ARG SQLITE3_VERSION
ARG THEBITLAB_TOOLCHAIN_VERSION
ARG THEBITLAB_WORKER_SCHEMA_VERSION
ARG SOURCE_REVISION
# BuildKit normalizza i timestamp dei layer a SOURCE_DATE_EPOCH: il digest resta riproducibile.
ARG SOURCE_DATE_EPOCH

LABEL org.opencontainers.image.title="TheBitLab assignment runner" \
      org.opencontainers.image.version="${THEBITLAB_TOOLCHAIN_VERSION}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      io.thebitlab.grading.base-image="${DEBIAN_BASE_IMAGE}" \
      io.thebitlab.grading.debian-snapshot="${DEBIAN_SNAPSHOT}" \
      io.thebitlab.grading.worker-schema="${THEBITLAB_WORKER_SCHEMA_VERSION}"

# Lo snapshot e le versioni arrivano dal manifest validato: nessun repository mobile.
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s/ bookworm main\n' "${DEBIAN_SNAPSHOT}" > /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends \
        "gcc=${GCC_VERSION}" \
        "libc6-dev=${LIBC6_DEV_VERSION}" \
        "nodejs=${NODEJS_VERSION}" \
        "python3=${PYTHON3_VERSION}" \
        "sqlite3=${SQLITE3_VERSION}" \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin runner

COPY scripts/grade_activity.py /opt/thebitlab/grade_activity.py

WORKDIR /submission

USER runner

ENTRYPOINT ["python3", "/opt/thebitlab/grade_activity.py"]
