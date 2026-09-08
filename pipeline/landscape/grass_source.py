"""The denser lawn scan selected against the front-yard photograph."""

import hashlib
import zipfile
import requests

SHA256 = "d7d3f08e8bb1e59aed0c3dbb85ea0b46d5308481f89b6a3fd62c0ec9e862245b"
URL = "https://ambientcg.com/get?file=Grass004_2K-JPG.zip"


def fetch(root):
    archive = root / ".local/Grass004_2K-JPG.zip"
    if not archive.exists():
        response = requests.get(URL, timeout=120)
        response.raise_for_status()
        archive.write_bytes(response.content)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError(
            "Grass004 source archive changed; review it before replacing the pinned scan"
        )
    files = []
    with zipfile.ZipFile(archive) as package:
        for channel, source in [("diff", "Color"), ("nor_gl", "NormalGL"), ("rough", "Roughness")]:
            data = package.read(f"Grass004_2K-JPG_{source}.jpg")
            path = root / "reference/materials/landscape" / f"Grass004_{channel}.jpg"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    return {
        "id": "Grass004",
        "source": "https://ambientcg.com/a/Grass004",
        "license": "CC0",
        "licenseSource": "https://docs.ambientcg.com/license/",
        "repeatMeters": 1.4,
        "archiveUrl": URL,
        "archiveSha256": SHA256,
        "files": files,
    }
