from __future__ import annotations

import os
from pathlib import Path

import FreeCAD as App
import Part


ARTIFACT_DIR = Path(
    os.environ.get("SOLIDFREECAD_M3_ARTIFACT_DIR", "m3-partdesign-artifacts")
).resolve()
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def assert_valid_solid(feature, label: str) -> float:
    shape = feature.Shape
    if shape.isNull() or not shape.isValid():
        raise RuntimeError(f"{label} did not create a valid shape")
    volume = float(shape.Volume)
    if volume <= 0.0:
        raise RuntimeError(f"{label} did not create a positive solid volume")
    return volume


def test_revolution() -> None:
    document = App.newDocument("SolidFreeCADM3Revolution")
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 10.0
    box.Width = 10.0
    box.Height = 10.0
    document.recompute()

    revolution = document.addObject("PartDesign::Revolution", "Revolution")
    revolution.Profile = (box, ["Face6"])
    revolution.ReferenceAxis = (document.Y_Axis, [""])
    revolution.Angle = 180.0
    revolution.Reversed = True
    revolution.Midplane = False
    body.addObject(revolution)
    document.recompute()

    volume = assert_valid_solid(revolution, "Revolution")
    if abs(float(revolution.Angle) - 180.0) > 1e-9:
        raise RuntimeError("Revolution angle was not preserved")
    document.saveAs(str(ARTIFACT_DIR / "m3-revolution.FCStd"))
    print(
        f"SOLIDFREECAD_M3_REVOLUTION_OK volume_mm3={volume:.6f} angle_deg={float(revolution.Angle):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)


def build_fillet_document():
    document = App.newDocument("SolidFreeCADM3Fillet")
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 20.0
    box.Width = 20.0
    box.Height = 20.0
    document.recompute()

    fillet = document.addObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (box, ["Face" + str(index + 1) for index in range(6)])
    fillet.Radius = 2.0
    fillet.UseAllEdges = False
    body.addObject(fillet)
    document.recompute()
    return document, body, box, fillet


def test_fillet_and_step_roundtrip() -> None:
    document, _body, _box, fillet = build_fillet_document()
    source_volume = assert_valid_solid(fillet, "Fillet")
    if source_volume >= 20.0 * 20.0 * 20.0:
        raise RuntimeError("Fillet did not remove material from the source box")

    source_fcstd = ARTIFACT_DIR / "m3-fillet.FCStd"
    step_path = ARTIFACT_DIR / "m3-fillet-roundtrip.step"
    imported_fcstd = ARTIFACT_DIR / "m3-step-imported.FCStd"
    document.saveAs(str(source_fcstd))
    Part.export([fillet], str(step_path))
    if not step_path.exists() or step_path.stat().st_size < 500:
        raise RuntimeError("STEP export did not create a usable file")

    print(
        f"SOLIDFREECAD_M3_FILLET_OK volume_mm3={source_volume:.6f} radius_mm={float(fillet.Radius):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)

    imported = App.newDocument("SolidFreeCADM3StepImported")
    Part.insert(str(step_path), imported.Name)
    imported.recompute()
    shape_objects = [
        obj
        for obj in imported.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull() and obj.Shape.isValid()
    ]
    if not shape_objects:
        raise RuntimeError("STEP import did not create a valid shape object")
    imported_feature = max(shape_objects, key=lambda obj: float(obj.Shape.Volume))
    imported_volume = float(imported_feature.Shape.Volume)
    tolerance = max(1e-5, source_volume * 1e-6)
    if abs(imported_volume - source_volume) > tolerance:
        raise RuntimeError(
            "STEP round trip changed the solid volume: "
            f"source={source_volume} imported={imported_volume} tolerance={tolerance}"
        )
    imported.saveAs(str(imported_fcstd))
    print(
        "SOLIDFREECAD_STEP_ROUNDTRIP_OK "
        f"step={step_path} source_volume_mm3={source_volume:.6f} "
        f"imported_volume_mm3={imported_volume:.6f}",
        flush=True,
    )
    App.closeDocument(imported.Name)


def test_chamfer() -> None:
    document = App.newDocument("SolidFreeCADM3Chamfer")
    body = document.addObject("PartDesign::Body", "Body")
    box = document.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length = 20.0
    box.Width = 20.0
    box.Height = 20.0
    document.recompute()

    chamfer = document.addObject("PartDesign::Chamfer", "Chamfer")
    chamfer.Base = (box, ["Face" + str(index + 1) for index in range(6)])
    chamfer.Size = 2.0
    chamfer.UseAllEdges = False
    body.addObject(chamfer)
    document.recompute()

    volume = assert_valid_solid(chamfer, "Chamfer")
    if volume >= 20.0 * 20.0 * 20.0:
        raise RuntimeError("Chamfer did not remove material from the source box")
    document.saveAs(str(ARTIFACT_DIR / "m3-chamfer.FCStd"))
    print(
        f"SOLIDFREECAD_M3_CHAMFER_OK volume_mm3={volume:.6f} size_mm={float(chamfer.Size):.3f}",
        flush=True,
    )
    App.closeDocument(document.Name)


def main() -> None:
    test_revolution()
    test_fillet_and_step_roundtrip()
    test_chamfer()
    print(f"SOLIDFREECAD_M3_PARTDESIGN_SMOKE_OK artifacts={ARTIFACT_DIR}", flush=True)


if __name__ == "__main__":
    main()
