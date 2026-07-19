#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="https://github.com/FreeCAD/FreeCAD.git"
UPSTREAM_TAG="1.1.1"
DESTINATION="${1:-${PWD}/build/freecad-source}"

log() {
    printf '[SolidFreeCAD] %s\n' "$*"
}

fail() {
    printf '[SolidFreeCAD] ERROR: %s\n' "$*" >&2
    exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"

if [[ -e "${DESTINATION}" ]]; then
    fail "destination already exists: ${DESTINATION}"
fi

mkdir -p "$(dirname "${DESTINATION}")"

log "cloning official FreeCAD tag ${UPSTREAM_TAG}"
git clone \
    --branch "${UPSTREAM_TAG}" \
    --depth 1 \
    --recurse-submodules \
    --shallow-submodules \
    "${UPSTREAM_URL}" \
    "${DESTINATION}"

ACTUAL_TAG="$(git -C "${DESTINATION}" describe --tags --exact-match 2>/dev/null || true)"
[[ "${ACTUAL_TAG}" == "${UPSTREAM_TAG}" ]] \
    || fail "expected tag ${UPSTREAM_TAG}, got ${ACTUAL_TAG:-none}"

COMMIT="$(git -C "${DESTINATION}" rev-parse HEAD)"
printf '%s\n' "${UPSTREAM_TAG}" > "${DESTINATION}/SOLIDFREECAD_UPSTREAM_TAG"
printf '%s\n' "${COMMIT}" > "${DESTINATION}/SOLIDFREECAD_UPSTREAM_COMMIT"

log "official source ready"
log "path: ${DESTINATION}"
log "tag: ${ACTUAL_TAG}"
log "commit: ${COMMIT}"
