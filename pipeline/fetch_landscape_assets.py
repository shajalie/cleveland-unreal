"""Versioned CC0 landscape source downloads, verified against upstream checksums."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from fetch_assets import ROOT, download_asset
from landscape.grass_source import fetch as fetch_lawn

MODELS = [
    "grass_bermuda_01",
    "shrub_04",
    "fern_02",
    "periwinkle_plant",
    "flower_gazania",
    "planter_pot_clay",
]
TEXTURES = ["leafy_grass", "pebble_embedded_pavement", "slate_floor_02"]


def texture(asset):
    response = requests.get("https://api.polyhaven.com/files/" + asset, timeout=40)
    response.raise_for_status()
    sources = response.json()
    files = []
    for channel in ("diff", "nor_gl", "rough"):
        source = sources[{"diff": "Diffuse", "rough": "Rough"}.get(channel, channel)]["2k"]["jpg"]
        path = ROOT / "reference/materials/landscape" / f"{asset}_{channel}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest() != source["md5"]:
            data = requests.get(source["url"], timeout=120)
            data.raise_for_status()
            if hashlib.md5(data.content).hexdigest() != source["md5"]:
                raise ValueError("Upstream checksum mismatch: " + source["url"])
            path.write_bytes(data.content)
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "url": source["url"],
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "id": asset,
        "source": "https://polyhaven.com/a/" + asset,
        "license": "CC0",
        "files": files,
    }


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(download_asset, MODELS)) + list(pool.map(texture, TEXTURES))
    # glTF base-color JPGs do not carry alpha. Fetch the separate source opacity.
    for record in records[: len(MODELS)]:
        asset = record["id"]
        data = requests.get("https://api.polyhaven.com/files/" + asset, timeout=40).json()
        for channel, resolutions in data.items():
            if not any(key in channel.lower() for key in ("alpha", "opacity")):
                continue
            source = resolutions.get("1k", resolutions.get("2k", {})).get("png")
            if not source:
                continue
            path = (
                ROOT / ".local/model-assets" / asset / "textures" / f"{asset}_{channel}_alpha.png"
            )
            result = requests.get(source["url"], timeout=120)
            result.raise_for_status()
            if hashlib.md5(result.content).hexdigest() != source["md5"]:
                raise ValueError("Opacity checksum mismatch")
            path.write_bytes(result.content)
            record["files"].append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "url": source["url"],
                    "sha256": hashlib.sha256(result.content).hexdigest(),
                }
            )
        record["selectionStatus"] = (
            "Representative scanned leaves/ground cover; species not surveyed. Placement follows saved listing photos."
        )
    records.append(fetch_lawn(ROOT))
    (ROOT / "design/landscape-sources.json").write_text(json.dumps(records, indent=2))
    print(
        json.dumps(
            {
                "models": len(MODELS),
                "textures": len(TEXTURES),
                "files": sum(len(r["files"]) for r in records),
            }
        )
    )


if __name__ == "__main__":
    main()
