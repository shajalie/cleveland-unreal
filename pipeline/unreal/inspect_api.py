"""Inspect the installed engine's API before generating its scene assets."""

import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]


def main():
    names = [
        "UsdStageImportFactory",
        "UsdStageImportOptions",
        "UsdStageActor",
        "UsdCollisionType",
        "EditorLevelLibrary",
        "EditorActorSubsystem",
        "StaticMeshEditorSubsystem",
        "BlueprintEditorLibrary",
        "SubobjectDataSubsystem",
        "MaterialEditingLibrary",
        "EditorAssetLibrary",
        "AssetImportTask",
    ]
    report = {}
    for name in names:
        cls = getattr(unreal, name, None)
        report[name] = {
            "available": cls is not None,
            "documentation": cls.__doc__ if cls else None,
            "members": [member for member in dir(cls) if not member.startswith("_")] if cls else [],
        }
    target = ROOT / ".local/unreal-api.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2))
    unreal.log(f"Cleveland engine API report saved to {target}")


if __name__ == "__main__":
    main()
