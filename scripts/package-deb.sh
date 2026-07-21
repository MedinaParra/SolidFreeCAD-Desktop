#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <freecad-build-dir> [output-dir]" >&2
    exit 2
fi

BUILD_DIR="$(realpath "$1")"
OUTPUT_DIR="$(realpath -m "${2:-build/packages}")"
PACKAGE_NAME="solidfreecad-ubuntu"
ARCHITECTURE="amd64"
VERSION="0.1.0+git$(git rev-parse --short=12 HEAD)"
PACKAGE_ROOT="$(realpath -m build/deb-root)"
INSTALL_ROOT="${PACKAGE_ROOT}/opt/solidfreecad"

if [[ ! -x "${BUILD_DIR}/bin/FreeCAD" ]]; then
    echo "FreeCAD executable not found: ${BUILD_DIR}/bin/FreeCAD" >&2
    exit 1
fi
if [[ ! -f "${BUILD_DIR}/lib/libFreeCADGui.so" ]]; then
    echo "libFreeCADGui.so not found in ${BUILD_DIR}/lib" >&2
    exit 1
fi

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

# Remove files that are useful for development but not for executing SolidFreeCAD.
find "${INSTALL_ROOT}" -type f \( -name '*.a' -o -name '*.la' -o -name '*.o' -o -name '*.obj' \) -delete
find "${INSTALL_ROOT}" -type d \( -name '__pycache__' -o -name 'CMakeFiles' \) -prune -exec rm -rf {} +

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
Terminal=false
Categories=Graphics;Engineering;Science;
MimeType=application/x-extension-fcstd;model/step;model/stl;
StartupNotify=true
DESKTOP

cat > "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian" <<EOF
SolidFreeCAD Ubuntu development package
========================================

This package contains the latest validated development build from commit
$(git rev-parse HEAD) on branch $(git branch --show-current).

Launch it from the application menu or run:

    solidfreecad

Classic FreeCAD recovery mode:

    SOLIDFREECAD_CLASSIC_MODE=1 solidfreecad

This is a development package, not a stable workshop release.
EOF

gzip -9n -c "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian" \
    > "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian.gz"
rm "${PACKAGE_ROOT}/usr/share/doc/${PACKAGE_NAME}/README.Debian"

# Derive runtime package dependencies from every ELF file included in the package.
declare -A dependency_set=()
while IFS= read -r -d '' elf_file; do
    if ! file -Lb "${elf_file}" | grep -q '^ELF'; then
        continue
    fi
    while IFS= read -r library_path; do
        [[ -n "${library_path}" && -e "${library_path}" ]] || continue
        resolved_path="$(readlink -f "${library_path}")"
        owner_package="$(dpkg-query -S "${resolved_path}" 2>/dev/null | head -n 1 | cut -d: -f1 || true)"
        if [[ -n "${owner_package}" && "${owner_package}" != *-dev ]]; then
            dependency_set["${owner_package}"]=1
        fi
    done < <(
        ldd "${elf_file}" 2>/dev/null | awk '
            $2 == "=>" && $3 ~ /^\// { print $3 }
            $1 ~ /^\// { print $1 }
        '
    )
done < <(find "${INSTALL_ROOT}" -type f -print0)

for required_package in python3 python3-pyside2.qtcore python3-pyside2.qtgui python3-pyside2.qtwidgets; do
    if dpkg-query -W -f='${Status}' "${required_package}" 2>/dev/null | grep -q 'install ok installed'; then
        dependency_set["${required_package}"]=1
    fi
done

DEPENDENCIES="$(printf '%s\n' "${!dependency_set[@]}" | LC_ALL=C sort | paste -sd ', ' -)"
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

# Confirm the staged executable can resolve its bundled FreeCAD libraries.
env \
    LD_LIBRARY_PATH="${INSTALL_ROOT}/lib" \
    PYTHONPATH="${INSTALL_ROOT}/lib:${INSTALL_ROOT}/Ext:${INSTALL_ROOT}/Mod" \
    QT_QPA_PLATFORM=offscreen \
    timeout 30s "${INSTALL_ROOT}/bin/FreeCAD" --version

DEB_PATH="${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
dpkg-deb --build --root-owner-group "${PACKAGE_ROOT}" "${DEB_PATH}"
dpkg-deb --info "${DEB_PATH}"
sha256sum "${DEB_PATH}" | tee "${DEB_PATH}.sha256"

echo "SOLIDFREECAD_DEB_OK path=${DEB_PATH}"
