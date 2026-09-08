"""Fetch named CC0 models with upstream checksums; no account is required."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    "sofa_02",
    "sofa_03",
    "modern_arm_chair_01",
    "mid_century_lounge_chair",
    "outdoor_table_chair_set_01",
    "potted_plant_04",
    "throw_pillows_01",
    "book_encyclopedia_set_01",
    "Rockingchair_01",
    "dining_chair_02",
]


def download_asset(asset):
    response = requests.get("https://api.polyhaven.com/files/" + asset, timeout=40)
    response.raise_for_status()
    entry = response.json()["gltf"]["1k"]["gltf"]
    folder = ROOT / ".local/model-assets" / asset
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for name, info in {asset + "_1k.gltf": entry, **entry.get("include", {})}.items():
        destination = (folder / name).resolve()
        assert destination.is_relative_to(folder.resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        if (
            not destination.exists()
            or hashlib.md5(destination.read_bytes()).hexdigest() != info["md5"]
        ):
            result = requests.get(info["url"], timeout=120)
            result.raise_for_status()
            assert hashlib.md5(result.content).hexdigest() == info["md5"]
            destination.write_bytes(result.content)
        files.append(
            {
                "path": destination.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "url": info["url"],
            }
        )
    return {
        "id": asset,
        "license": "CC0",
        "source": "https://polyhaven.com/a/" + asset,
        "files": files,
        "selectionStatus": "Needs comparison with house photographs",
    }


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(download_asset, ASSETS))
    (ROOT / "design/asset-sources.json").write_text(json.dumps(records, indent=2))
    print(
        json.dumps(
            {"downloadedModels": len(records), "files": sum(len(x["files"]) for x in records)}
        )
    )
