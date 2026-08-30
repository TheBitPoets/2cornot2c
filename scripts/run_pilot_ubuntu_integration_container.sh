#!/usr/bin/env bash
# Run the destructive effective deployment integration only inside a dedicated systemd container.
set -Eeuo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repository_root="$(cd -- "$script_directory/.." && pwd -P)"
dockerfile="$repository_root/deploy/pilot/ci/Dockerfile.ubuntu-systemd"
package_baseline="$repository_root/deploy/pilot/ci/ubuntu-systemd-package-baseline.json"
package_baseline_host="$package_baseline"
build_context="$repository_root"
mount_source="$repository_root"
integration_arguments=(--ephemeral-host)
private_runtime_poc=false
if (( $# == 1 )) && [[ "$1" == "--bootstrap-adversarial-only" ]]; then
    integration_arguments+=(--bootstrap-adversarial-only)
elif (( $# == 1 )) && [[ "$1" == "--executor-lease-gate-only" ]]; then
    integration_arguments+=(--executor-lease-gate-only)
elif (( $# == 1 )) && [[ "$1" == "--private-runtime-gate-only" ]]; then
    integration_arguments+=(--private-runtime-gate-only)
elif (( $# == 1 )) && [[ "$1" == "--private-runtime-start-diagnostic-only" ]]; then
    integration_arguments+=(--private-runtime-start-diagnostic-only)
elif (( $# == 1 )) && [[ "$1" == "--executor-lease-timing-diagnostic-only" ]]; then
    integration_arguments+=(--executor-lease-timing-diagnostic-only)
elif (( $# == 1 )) && [[ "$1" == "--fence-race-only" ]]; then
    integration_arguments+=(--fence-race-only)
elif (( $# == 1 )) && [[ "$1" == "--generator-orchestrator-gate-only" ]]; then
    integration_arguments+=(--generator-orchestrator-gate-only)
elif (( $# == 1 )) && [[ "$1" == "--runtime-directory-authority-only" ]]; then
    integration_arguments+=(--runtime-directory-authority-only)
elif (( $# == 1 )) && [[ "$1" == "--shard-f-only" ]]; then
    integration_arguments+=(--shard-f-only)
elif (( $# == 1 )) && [[ "$1" == "--private-runtime-poc" ]]; then
    private_runtime_poc=true
elif (( $# != 0 )); then
    echo "ERRORE: argomento integrazione inatteso" >&2
    exit 2
fi

# Git Bash otherwise rewrites Linux container paths before invoking the Windows Docker CLI.
if [[ -n "${MSYSTEM:-}" ]] && command -v cygpath >/dev/null 2>&1; then
    mount_source="$(cygpath -w "$repository_root")"
    build_context="$(cygpath -w "$build_context")"
    dockerfile="$(cygpath -w "$dockerfile")"
    package_baseline_host="$(cygpath -w "$package_baseline")"
    export MSYS_NO_PATHCONV=1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERRORE: Docker non disponibile" >&2
    exit 2
fi

identity="${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-0}-$$"
identity="$(printf '%s' "$identity" | tr -c '[:alnum:]_.-' '-')"
image="thebitlab-pilot-ubuntu-systemd-integration:${identity,,}"
container="thebitlab-pilot-ubuntu-systemd-integration-${identity,,}"
image_built=false
container_may_exist=false

cleanup() {
    local original_status=$?
    local cleanup_status=0
    trap - EXIT INT TERM

    if [[ "$container_may_exist" == "true" ]] \
        && ! docker rm --force "$container" >/dev/null; then
        cleanup_status=1
    fi
    if [[ "$image_built" == "true" ]] \
        && ! docker image rm "$image" >/dev/null; then
        cleanup_status=1
    fi
    if (( cleanup_status != 0 )); then
        echo "ERRORE: cleanup container/image CI fallita" >&2
    fi

    if (( original_status != 0 )); then
        exit "$original_status"
    fi
    exit "$cleanup_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

baseline_snapshot="$(python -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["ubuntu_snapshot"])' "$package_baseline_host")"
baseline_sha256="$(python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$package_baseline_host")"
baseline_inventory_sha256="$(python -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["stages"]["runtime"]["installed_package_inventory_sha256"])' "$package_baseline_host")"

docker build --pull --no-cache --tag "$image" --file "$dockerfile" "$build_context"
image_built=true
container_may_exist=true
image_snapshot="$(docker image inspect --format '{{index .Config.Labels "org.thebitlab.pilot.ubuntu-snapshot"}}' "$image")"
image_baseline_sha256="$(docker image inspect --format '{{index .Config.Labels "org.thebitlab.pilot.package-baseline-sha256"}}' "$image")"
image_inventory_sha256="$(docker image inspect --format '{{index .Config.Labels "org.thebitlab.pilot.package-inventory-sha256"}}' "$image")"
[[ "$image_snapshot" == "$baseline_snapshot" \
    && "$image_baseline_sha256" == "$baseline_sha256" \
    && "$image_inventory_sha256" == "$baseline_inventory_sha256" ]] || {
    echo "ERRORE: identity package baseline image divergente" >&2
    exit 2
}
echo "EVIDENCE: package baseline snapshot=$baseline_snapshot manifest=$baseline_sha256 inventory=$baseline_inventory_sha256"

docker run --detach \
    --name "$container" \
    --hostname thebitlab-pilot-ci \
    --label org.thebitlab.purpose=pilot-ubuntu-systemd-integration \
    --privileged \
    --cgroupns=private \
    --tmpfs /run:rw,nosuid,nodev,mode=755 \
    --tmpfs /run/lock:rw,nosuid,nodev,mode=755 \
    --mount "type=bind,source=$mount_source,target=/workspace,readonly" \
    "$image" >/dev/null

system_state=""
for _attempt in $(seq 1 45); do
    if [[ "$(docker inspect --format '{{.State.Running}}' "$container")" != "true" ]]; then
        echo "ERRORE: systemd container terminato durante readiness" >&2
        docker logs --tail 100 "$container" >&2
        exit 2
    fi
    candidate_state="$(docker exec "$container" systemctl is-system-running 2>/dev/null || true)"
    if [[ "$candidate_state" == "running" ]]; then
        system_state="$candidate_state"
        break
    fi
    sleep 1
done
if [[ "$system_state" != "running" ]]; then
    echo "ERRORE: systemd non ha raggiunto lo stato running (ultimo=$candidate_state)" >&2
    docker exec "$container" systemctl --failed --no-pager >&2 || true
    docker logs --tail 100 "$container" >&2
    exit 2
fi

pid1_comm="$(docker exec "$container" ps -p 1 -o comm= | tr -d '[:space:]')"
pid1_exe="$(docker exec "$container" readlink -f /proc/1/exe)"
systemd_version="$(docker exec "$container" systemctl --version | awk 'NR == 1 {print $2}')"
cgroup_entry="$(docker exec "$container" cat /proc/1/cgroup | tr -d '\r')"
cgroup_filesystem="$(docker exec "$container" stat -fc %T /sys/fs/cgroup)"
container_boot_id="$(docker exec "$container" cat /proc/sys/kernel/random/boot_id)"

[[ "$pid1_comm" == "systemd" && "$pid1_exe" == */systemd ]] || {
    echo "ERRORE: PID 1 container non è systemd ($pid1_comm, $pid1_exe)" >&2
    exit 2
}
[[ "$systemd_version" == "255" ]] || {
    echo "ERRORE: versione systemd Ubuntu inattesa: $systemd_version" >&2
    exit 2
}
[[ "$cgroup_entry" == "0::/init.scope" && "$cgroup_filesystem" == "cgroup2fs" ]] || {
    echo "ERRORE: cgroup v2 PID 1 non canonico: $cgroup_entry ($cgroup_filesystem)" >&2
    exit 2
}

privileged="$(docker inspect --format '{{.HostConfig.Privileged}}' "$container")"
cgroup_mode="$(docker inspect --format '{{.HostConfig.CgroupnsMode}}' "$container")"
pid_mode="$(docker inspect --format '{{.HostConfig.PidMode}}' "$container")"
network_mode="$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$container")"
port_bindings="$(docker inspect --format '{{json .HostConfig.PortBindings}}' "$container")"
mount_count="$(docker inspect --format '{{len .Mounts}}' "$container")"
mounted_destinations="$(
    docker inspect --format '{{range .Mounts}}{{.Destination}}{{end}}' "$container"
)"
[[ "$privileged" == "true" && "$cgroup_mode" == "private" && -z "$pid_mode" ]] || {
    echo "ERRORE: isolamento Docker inatteso" >&2
    exit 2
}
[[ "$network_mode" != "host" && "$port_bindings" == "{}" ]] || {
    echo "ERRORE: network namespace/port binding non isolati" >&2
    exit 2
}
[[ "$mount_count" == "1" && "$mounted_destinations" == "/workspace" ]] || {
    printf 'ERRORE: mount container inattesi: %s (%s)\n' \
        "$mounted_destinations" "$mount_count" >&2
    exit 2
}

container_pid_namespace="$(docker exec "$container" readlink /proc/1/ns/pid)"
container_cgroup_namespace="$(docker exec "$container" readlink /proc/1/ns/cgroup)"
container_mount_namespace="$(docker exec "$container" readlink /proc/1/ns/mnt)"
container_network_namespace="$(docker exec "$container" readlink /proc/1/ns/net)"
if [[ -L /proc/self/ns/pid ]]; then
    host_pid_namespace="$(readlink /proc/self/ns/pid)"
    host_cgroup_namespace="$(readlink /proc/self/ns/cgroup)"
    host_mount_namespace="$(readlink /proc/self/ns/mnt)"
    host_network_namespace="$(readlink /proc/self/ns/net)"
    [[ "$container_pid_namespace" != "$host_pid_namespace" \
        && "$container_cgroup_namespace" != "$host_cgroup_namespace" \
        && "$container_mount_namespace" != "$host_mount_namespace" \
        && "$container_network_namespace" != "$host_network_namespace" ]] || {
        echo "ERRORE: namespace container condiviso con il runner" >&2
        exit 2
    }
    echo "EVIDENCE: host/container pid,cgroup,mount,network namespaces differ"
elif [[ "$(uname -s)" == "Linux" ]]; then
    echo "ERRORE: namespace host non attestabili sul runner Linux" >&2
    exit 2
else
    echo "INFO: namespace host non esposti dalla shell locale; config Docker verificata"
fi

echo "EVIDENCE: container PID1=$pid1_comm exe=$pid1_exe systemd=$systemd_version state=$system_state"
echo "EVIDENCE: container boot_id=$container_boot_id PID1_cgroup=$cgroup_entry cgroup_fs=$cgroup_filesystem"
echo "EVIDENCE: private /run+/run/lock; private bridge network; no published ports; only /workspace read-only bind"
docker exec "$container" systemctl show nginx.service \
    --property=FragmentPath --property=UnitFileState --property=ControlGroup --no-pager
docker exec "$container" dpkg-query -W \
    -f='${binary:Package}=${Version}\n' \
    acl apt base-files dbus e2fsprogs libnginx-mod-http-geoip2 logrotate nginx openssl procps python3 python3-jsonschema systemd systemd-sysv wget

docker exec --interactive --workdir /workspace "$container" python3 - <<'PY'
from scripts import pilot_ubuntu_activation as activation
from scripts import pilot_ubuntu_integration as integration

unit_roots = activation._systemd_path(activation.SYSTEMD_UNIT_SEARCH_PATH_NAME)
generator_roots = activation._systemd_path(activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
integration._reject_unmanaged_ephemeral_unit_artifacts(unit_roots)
candidates = integration._ephemeral_generator_candidates(generator_roots)
if candidates:
    raise RuntimeError(f"dedicated container has {len(candidates)} ambient generator artifact(s)")
print("EVIDENCE: pre-integration dedicated systemd surface baseline PASS (0 ambient artifacts)")
PY

if [[ "$private_runtime_poc" == "true" ]]; then
    docker exec \
        --workdir /workspace \
        --env PYTHONUNBUFFERED=1 \
        "$container" \
        python3 scripts/pilot_private_runtime_poc.py
else
    docker exec \
        --workdir /workspace \
        --env "GITHUB_SHA=${GITHUB_SHA:-cccccccccccccccccccccccccccccccccccccccc}" \
        --env "GITHUB_RUN_ID=${GITHUB_RUN_ID:-local}" \
        --env PYTHONUNBUFFERED=1 \
        "$container" \
        python3 scripts/pilot_ubuntu_integration.py "${integration_arguments[@]}"
fi

docker rm --force "$container" >/dev/null
container_may_exist=false
docker image rm "$image" >/dev/null
image_built=false
if docker inspect "$container" >/dev/null 2>&1 || docker image inspect "$image" >/dev/null 2>&1; then
    echo "ERRORE: cleanup witness container/image non terminale" >&2
    exit 2
fi
if [[ "$private_runtime_poc" == "false" ]]; then
    printf 'PRIVATE_RUNTIME_CLEANUP_EVIDENCE {"candidate_sha":"%s","container_absent":true,"created_unix_ns":%s,"image_absent":true,"run_id":"%s","schema_version":"thebitlab.private-runtime-cleanup-evidence.v1"}\n' \
        "${GITHUB_SHA:-cccccccccccccccccccccccccccccccccccccccc}" \
        "$(python -c 'import time; print(time.time_ns())')" \
        "${GITHUB_RUN_ID:-local}"
fi
