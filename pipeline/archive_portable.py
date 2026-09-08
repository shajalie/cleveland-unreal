"""Archive only the verified manifest, excluding state created during testing."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = Path((ROOT / ".local/latest-portable-build.txt").read_text().strip()).resolve()
    if not folder.is_relative_to(ROOT / "Builds"):
        raise ValueError("Portable build is outside the project output directory")
    manifest_file = folder / "portable-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    output = folder.parent / "cleveland-unreal-windows.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for entry in manifest["files"]:
            relative = entry["path"]
            file = (folder / relative).resolve()
            if not file.is_relative_to(folder) or file.is_symlink():
                raise ValueError(f"Unexpected portable input: {relative}")
            if relative.startswith(".local/") and not relative.startswith(".local/pixel-streaming-infrastructure/"):
                raise ValueError(f"Private PC state in manifest: {relative}")
            if file.suffix.lower() in {".dpapi", ".pem", ".key"} or file.name.startswith(".env"):
                raise ValueError(f"Credential-shaped input: {relative}")
            with file.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            if digest != entry["sha256"] or file.stat().st_size != entry["bytes"]:
                raise ValueError(f"File changed after staging: {relative}")
            archive.write(file, "cleveland-unreal/" + relative)
        archive.write(manifest_file, "cleveland-unreal/portable-manifest.json")
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP checksum failure: {bad}")
    with output.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    (output.parent / "SHA256SUMS.txt").write_text(f"{digest}  {output.name}\n")
    result = {"archive": str(output), "bytes": output.stat().st_size, "sha256": digest, "files": len(manifest["files"]) + 1}
    (ROOT / ".local/latest-portable-archive.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
