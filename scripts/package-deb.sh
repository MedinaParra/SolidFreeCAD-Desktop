#!/usr/bin/env bash
set -euo pipefail

mkdir -p build/logs
exec > >(tee build/logs/package-deb.log) 2>&1

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <freecad-build-dir> [output-dir]" >&2
    exit 2
fi

BUILD_DIR="$(realpath "$1")"
OUTPUT_DIR="$(realpath -m "${2:-build/packages}")"
PACKAGE_NAME="solidfreecad-ubuntu"
ARCHITECTURE="amd64"
SOURCE_SHA="${SOLIDFREECAD_SOURCE_SHA:-$(git rev-parse HEAD)}"
SOURCE_BRANCH="${SOLIDFREECAD_SOURCE_BRANCH:-$(git branch --show-current)}"
SOURCE_SHA_SHORT="${SOURCE_SHA:0:12}"
VERSION="0.1.0+git${SOURCE_SHA_SHORT}"
PACKAGE_ROOT="$(realpath -m build/deb-root)"
INSTALL_ROOT="${PACKAGE_ROOT}/opt/solidfreecad"

if [[ -z "${SOURCE_BRANCH}" ]]; then
    SOURCE_BRANCH="agent/bootstrap-freecad-1.1.1"
fi
if [[ ! "${SOURCE_SHA}" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "Invalid source commit SHA: ${SOURCE_SHA}" >&2
    exit 1
fi
if ! command -v patchelf >/dev/null 2>&1; then
    echo "patchelf is required to remove non-relocatable build RUNPATH entries" >&2
    exit 1
fi
if [[ ! -x "${BUILD_DIR}/bin/FreeCAD" ]]; then
    echo "FreeCAD executable not found: ${BUILD_DIR}/bin/FreeCAD" >&2
    exit 1
fi
if [[ ! -f "${BUILD_DIR}/lib/libFreeCADGui.so" ]]; then
    echo "libFreeCADGui.so not found in ${BUILD_DIR}/lib" >&2
    exit 1
fi

required_runtime_paths=(
    "Mod/PartDesign/Init.py"
    "Mod/PartDesign/InitGui.py"
    "Mod/Sketcher/Init.py"
    "Mod/Sketcher/InitGui.py"
    "Mod/Part/Init.py"
    "Mod/Part/InitGui.py"
)
for required_path in "${required_runtime_paths[@]}"; do
    if [[ ! -f "${BUILD_DIR}/${required_path}" ]]; then
        echo "Required FreeCAD runtime resource is missing: ${BUILD_DIR}/${required_path}" >&2
        exit 1
    fi
done

for module_pattern in \
    "Mod/PartDesign/PartDesignGui*.so" \
    "Mod/Sketcher/SketcherGui*.so" \
    "Mod/Part/PartGui*.so"; do
    if ! compgen -G "${BUILD_DIR}/${module_pattern}" >/dev/null; then
        echo "Required FreeCAD GUI module is missing: ${BUILD_DIR}/${module_pattern}" >&2
        exit 1
    fi
done

rm -rf "${PACKAGE_ROOT}"
mkdir -p "${INSTALL_ROOT}" "${PACKAGE_ROOT}/DEBIAN" "${PACKAGE_ROOT}/usr/bin" \
    "${PACKAGE_ROOT}/usr/share/applications" "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}" \
    "${OUTPUT_DIR}"

# Preserve FreeCAD's build-tree runtime layout while excluding compiler objects.
for runtime_entry in bin lib Mod Ext Gui share data translations; do
    if [[ -e "${BUILD_DIR}/${runtime_entry}" ]]; then
        cp -a "${BUILD_DIR}/${runtime_entry}" "${INSTALL_ROOT}/"
    fi
done

find "${INSTALL_ROOT}" -type f \( -name '*.a' -o -name '*.la' -o -name '*.o' -o -name '*.obj' \) -delete
find "${INSTALL_ROOT}" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "${INSTALL_ROOT}" -type d -name 'CMakeFiles' -prune -exec rm -rf {} +

for required_path in "${required_runtime_paths[@]}"; do
    test -f "${INSTALL_ROOT}/${required_path}"
done

# FreeCAD build-tree modules depend on sibling module libraries and carry absolute
# GitHub runner RUNPATH entries. Expose every packaged module library from the
# private lib directory and remove those non-relocatable paths.
while IFS= read -r -d '' module_library; do
    library_name="$(basename "${module_library}")"
    library_link="${INSTALL_ROOT}/lib/${library_name}"
    relative_target="$(realpath --relative-to="${INSTALL_ROOT}/lib" "${module_library}")"

    if [[ -e "${library_link}" || -L "${library_link}" ]]; then
        if [[ "$(readlink -f "${library_link}")" != "$(readlink -f "${module_library}")" ]]; then
            echo "Conflicting packaged module library name: ${library_name}" >&2
            exit 1
        fi
        continue
    fi

    ln -s "${relative_target}" "${library_link}"
done < <(find "${INSTALL_ROOT}/Mod" -type f \( -name '*.so' -o -name '*.so.*' \) -print0)

while IFS= read -r -d '' elf_file; do
    if file -Lb "${elf_file}" | grep -q '^ELF'; then
        patchelf --remove-rpath "${elf_file}"
        if [[ -n "$(patchelf --print-rpath "${elf_file}")" ]]; then
            echo "Could not remove RUNPATH from ${elf_file}" >&2
            exit 1
        fi
    fi
done < <(
    find "${INSTALL_ROOT}/bin" "${INSTALL_ROOT}/lib" "${INSTALL_ROOT}/Mod" \
        -type f \( -perm /111 -o -name '*.so' -o -name '*.so.*' \) -print0
)

cat > "${PACKAGE_ROOT}/usr/bin/solidfreecad" <<'LAUNCHER'
#!/bin/sh
set -eu
SOLIDFREECAD_HOME=/opt/solidfreecad
export LD_LIBRARY_PATH="${SOLIDFREECAD_HOME}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export PYTHONPATH="${SOLIDFREECAD_HOME}/lib:${SOLIDFREECAD_HOME}/Ext:${SOLIDFREECAD_HOME}/Mod${PYTHONPATH:+:${PYTHONPATH}}"
exec "${SOLIDFREECAD_HOME}/bin/FreeCAD" "$@"
LAUNCHER
chmod 0755 "${PACKAGE_ROOT}/usr/bin/solidfreecad"
ln -s solidfreecad "${PACKAGE_ROOT}/usr/bin/SolidFreeCAD"

cat > "${PACKAGE_ROOT}/usr/share/applications/solidfreecad.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=SolidFreeCAD
Comment=Mechanical CAD interface built on FreeCAD 1.1.1
Exec=solidfreecad %F
Icon=applications-engineering
Terminal=false
Categories=Graphics;Engineering;Science;
MimeType=application/x-extension-fcstd;model/step;model/stl;
StartupNotify=true
StartupWMClass=FreeCAD
DESKTOP

cat > "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian" <<EOF
SolidFreeCAD Ubuntu development package
========================================

This package contains the latest validated development build from commit
${SOURCE_SHA} on branch ${SOURCE_BRANCH}.

Launch it from the application menu or run:

    solidfreecad

Classic FreeCAD recovery mode:

    SOLIDFREECAD_CLASSIC_MODE=1 solidfreecad

This is a development package, not a stable workshop release.
EOF

gzip -9n -c "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian" \
    > "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian.gz"
rm "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian"

# Derive runtime dependencies from executable and shared-library ELF files.
declare -A dependency_set=()
while IFS= read -r -d '' elf_file; do
    if ! file -Lb "${elf_file}" | grep -q '^ELF'; then
        continue
    fi
    while IFS= read -r library_path; do
        [[ -n "${library_path}" && -e "${library_path}" ]] || continue
        resolved_path="$(readlink -f "${library_path}")"
        if [[ "${resolved_path}" == "${INSTALL_ROOT}/"* ]]; then
            continue
        fi
        owner_package="$(dpkg-query -S "${resolved_path}" 2>/dev/null | head -n 1 | sed 's/: .*//' || true)"
        if [[ -n "${owner_package}" && "${owner_package}" != *-dev ]]; then
            dependency_set["${owner_package}"]=1
        fi
    done < <(
        env LD_LIBRARY_PATH="${INSTALL_ROOT}/lib" ldd "${elf_file}" 2>/dev/null | awk '
            $2 == "=>" && $3 ~ /^\// { print $3 }
            $1 ~ /^\// { print $1 }
        '
    )
done < <(
    find "${INSTALL_ROOT}/bin" "${INSTALL_ROOT}/lib" "${INSTALL_ROOT}/Mod" \
        -type f \( -perm /111 -o -name '*.so' -o -name '*.so.*' \) -print0
)

for required_package in python3 python3-pyside2.qtcore python3-pyside2.qtgui python3-pyside2.qtwidgets; do
    if dpkg-query -W -f='${Status}' "${required_package}" 2>/dev/null | grep -q 'install ok installed'; then
        dependency_set["${required_package}"]=1
    fi
done

DEPENDENCIES="$(printf '%s\n' "${!dependency_set[@]}" | LC_ALL=C sort | paste -sd, - | sed 's/,/, /g')"
if [[ -z "${DEPENDENCIES}" ]]; then
    DEPENDENCIES="libc6, libstdc++6, python3"
fi

INSTALLED_SIZE="$(du -sk "${PACKAGE_ROOT}" | awk '{print $1}')"
cat > "${PACKAGE_ROOT}/DEBIAN/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: Exequiel Medina <exemdn@gmail.com>
Installed-Size: ${INSTALLED_SIZE}
Depends: ${DEPENDENCIES}
Provides: solidfreecad
Description: SolidFreeCAD mechanical CAD development build
 SolidFreeCAD is a Qt/C++ mechanical-design interface integrated with the
 official FreeCAD 1.1.1 document system, geometry kernel and 3D viewer.
 This package is generated from the latest validated Ubuntu development branch.
EOF

cat > "${PACKAGE_ROOT}/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi
exit 0
POSTINST
chmod 0755 "${PACKAGE_ROOT}/DEBIAN/postinst"

# Validate linkage after RUNPATH removal, using only packaged private libraries
# plus the clean runner's system libraries.
while IFS= read -r -d '' elf_file; do
    linkage="$(env LD_LIBRARY_PATH="${INSTALL_ROOT}/lib" ldd "${elf_file}" 2>/dev/null || true)"
    if grep -q 'not found' <<<"${linkage}"; then
        printf '%s\n' "${linkage}"
        echo "Unresolved library in staged package file: ${elf_file}" >&2
        exit 1
    fi
done < <(
    find "${INSTALL_ROOT}/bin" "${INSTALL_ROOT}/lib" "${INSTALL_ROOT}/Mod" \
        -type f \( -perm /111 -o -name '*.so' -o -name '*.so.*' \) -print0
)

DEB_PATH="${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
dpkg-deb --build --root-owner-group "${PACKAGE_ROOT}" "${DEB_PATH}"
dpkg-deb --info "${DEB_PATH}"
dpkg-deb --contents "${DEB_PATH}" >/dev/null
sha256sum "${DEB_PATH}" | tee "${DEB_PATH}.sha256"

echo "SOLIDFREECAD_DEB_OK path=${DEB_PATH} source_sha=${SOURCE_SHA}"
