"""Check exported instance placement and foliage opacity against the saved source."""

import json
from pathlib import Path
import bpy
from pxr import Usd, UsdGeom, Tf

ROOT = Path(__file__).resolve().parents[1]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "SourceAssets/Cleveland-Reconstruction.blend"))
    bpy.context.view_layer.update()
    stage = Usd.Stage.Open(str(ROOT / "SourceAssets/UnrealTransfer/Cleveland.usdc"))
    if not stage:
        raise RuntimeError("USD could not be opened")
    cache = UsdGeom.XformCache()
    checks = []
    for obj in bpy.context.scene.objects:
        if "tree_id" not in obj:
            continue
        prim = stage.GetPrimAtPath("/Cleveland/" + Tf.MakeValidIdentifier(obj.name))
        if not prim:
            raise RuntimeError(f"Tree missing from USD: {obj.name}")
        actual = cache.GetLocalToWorldTransform(prim)
        error = max(abs(actual[i][j] - obj.matrix_world[j][i]) for i in range(4) for j in range(4))
        checks.append(
            {
                "check": "tree_instance_transform",
                "tree": obj.name,
                "maximumMatrixError": error,
                "pass": error < 0.00001,
            }
        )
    masks = []
    for prim in stage.Traverse():
        if (
            "leaves" not in str(prim.GetPath()).lower()
            and "twig" not in str(prim.GetPath()).lower()
        ):
            continue
        if prim.GetAttribute("info:id").Get() != "UsdPreviewSurface":
            continue
        connections = prim.GetAttribute("inputs:opacity").GetConnections()
        masks.append(
            {"shader": str(prim.GetPath()), "opacityConnections": [str(p) for p in connections]}
        )
        checks.append(
            {
                "check": "foliage_opacity_exported",
                "shader": str(prim.GetPath()),
                "pass": bool(connections),
            }
        )
    if not masks:
        raise RuntimeError("No foliage shaders were found in USD")
    report = {
        "checks": checks,
        "passed": sum(c["pass"] for c in checks),
        "failed": sum(not c["pass"] for c in checks),
        "foliageShaders": masks,
        "scope": "USD data validation; Unreal rendering remains unverified",
    }
    (ROOT / "reports/usd-validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"passed": report["passed"], "failed": report["failed"]}), flush=True)
    if report["failed"]:
        raise RuntimeError("USD instance or foliage validation failed")


if __name__ == "__main__":
    main()
