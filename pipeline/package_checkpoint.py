"""Build a transferable authoring checkpoint from explicit, credential-free inputs."""

import hashlib
import datetime
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    files = {ROOT / name for name in tracked if name}
    files.add(ROOT / "SourceAssets/Cleveland-Reconstruction.blend")
    files.add(ROOT / "SourceAssets/Cleveland-Landscape-v3.blend")
    files.update((ROOT / "SourceAssets/Landscape-v3").rglob("*"))
    files.add(ROOT / ".local/realism-assets.blend")
    files.add(ROOT / ".local/broadleaf-source.blend")
    files.update((ROOT / ".local/model-assets").rglob("*"))
    files = sorted(p for p in files if p.is_file())
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith(".local/") and not (
            relative.startswith(".local/model-assets/")
            or relative in [".local/realism-assets.blend", ".local/broadleaf-source.blend"]
        ):
            raise ValueError(f"Local account/runtime state cannot enter the package: {relative}")
        if ".env" in path.name or ".runtime" in path.parts or ".git" in path.parts:
            raise ValueError(f"Unexpected private state in package input: {relative}")
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / ".local/release-payload" / stamp
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "cleveland-reconstruction-checkpoint.zip"
    manifest = {
        "kind": "Editable authoring checkpoint; not a packaged Unreal application",
        "sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
        .decode()
        .strip(),
        "requires": [
            "Blender 4.5 LTS to open the scene",
            "NVIDIA OptiX GPU to run the render script",
            "Unreal 5.8 and supported MSVC/Windows SDK to compile the separate runtime",
        ],
        "files": [],
    }
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for path in files:
            data = path.read_bytes()
            relative = path.relative_to(ROOT).as_posix()
            package.writestr("cleveland-unreal/" + relative, data)
            manifest["files"].append(
                {"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            )
        package.writestr(
            "cleveland-unreal/checkpoint-manifest.json", json.dumps(manifest, indent=2)
        )
    with zipfile.ZipFile(archive) as package:
        bad = package.testzip()
        if bad:
            raise RuntimeError(f"Archive CRC verification failed: {bad}")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "checkpoint-manifest.json").write_text(json.dumps(manifest, indent=2))
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n")
    print(
        json.dumps(
            {
                "archive": str(archive),
                "bytes": archive.stat().st_size,
                "sha256": digest,
                "files": len(files),
            }
        )
    )


if __name__ == "__main__":
    main()
