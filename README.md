# Cleveland Real — independent reconstruction

This folder is a new reconstruction of 3014 Cleveland Avenue NW. It does not
replace the preserved Cleveland Sun Study build, running host, or published site.

**Current checkpoint:** a packaged Unreal 5.8.2 walkthrough and mobile streaming
dashboard are running. The UI includes room shortcuts, Washington, DC date/time,
exposure, touch movement, quality/FPS and memory settings. Chrome has decoded
roughly 18–24 FPS with the 2060 More FPS preset. Furniture, photo matching,
lighting calibration and full circulation still need work. This is an early
furnished reconstruction, not a finished photoreal digital twin.

The scene import now succeeds: 11,516 mesh components, 11 operable door
assemblies, three fan assemblies, native glass/water and 14 cutout tree-material
assignments. A DPI-aware child-process launch fixes the narrow logical screen
reported by a scaled phone RDP session. Windows network access is allowed.

Use the standalone Windows ZIP for another PC; it needs neither Blender nor the
Unreal editor. Extract it and double-click `Start-Walkthrough.cmd`. Tailscale phone
streaming is working. Cloudflare email protection is configured, but reliable
video without Tailscale still needs the separately billed TURN service activated
and verified. See [streaming setup and limitations](docs/streaming.md).

The new runtime target is Unreal Engine 5.8. Native Path Tracer output is the
reference for stills and pre-rendered sequences; the navigable version uses the
engine's interactive lighting, geometry, foliage and animation systems. Lumen is
not synonymous with a converged full path trace. Both outputs must use the same
spatial model, materials, solar orientation and explicit exposure.

The primary work is architectural reconstruction: traversable rear doors,
consistent floor and terrace levels, sensible stairs and driveways, correctly
oriented furniture, and photographic room composition. Surface detail is assessed
after silhouettes and layout match the evidence. More triangles cannot repair an
incorrect layout, and a renderer cannot infer missing measurements.

## Organization

- `reference/`: the actual listing photos (0–55), 2025 DC aerial and provenance.
- `design/`: room dimensions, opening and circulation graph, evidence decisions.
- `pipeline/geometry/`: modular Blender geometry and asset preparation.
- `pipeline/unreal/`: USD import, native transmission materials and motion setup.
- `runtime/ClevelandReal/`: Unreal project, input/render configuration and C++.
- `SourceAssets/`: generated editable source geometry, excluded from Git.
- `reports/`: measured validation and comparison results only.

Status and important unresolved assumptions are recorded in `design/decisions.md`.
The Unreal engine itself is obtained through Epic and is not redistributed in
this repository. No Epic, Cloudflare or other account credentials belong here.

## Rebuild and inspect

Use Python 3.13 and Blender 4.5 LTS. `pipeline/fetch_assets.py` downloads the
listed CC0 models to `.local/model-assets`. The checkpoint asset archive also
contains the prepared CC0 vegetation library at `.local/realism-assets.blend`.
That library is copied from the preserved build without changing it.

```powershell
python -m pip install -r requirements.txt
python pipeline/fetch_assets.py
blender -b --python-exit-code 1 --python pipeline/prepare_vegetation.py
python -m unittest discover -s tests -v
blender -b --python-exit-code 1 --python pipeline/build_scene.py -- --samples 128
blender -b --python-exit-code 1 --python pipeline/validate_scene.py
./pipeline/doctor.ps1
python pipeline/prepare_encoder.py --engine C:/Unreal/UE_5.8
./pipeline/build-runtime.ps1
blender -b --python-exit-code 1 --python pipeline/export_unreal.py
blender -b --python-exit-code 1 --python pipeline/verify_usd.py
./pipeline/import-runtime.ps1
```

The build requires an NVIDIA OptiX device and explicitly excludes CPU rendering.
The editable result is `SourceAssets/Cleveland-Reconstruction.blend`. Open that
file in Blender to inspect collections, materials and door pivots. Blender camera
reviews are saved in `reports/*-review.png`; the standalone game is packaged separately.

`build-runtime.ps1` uses an installed VS2022 toolchain, or a supplied portable
MSVC directory through Unreal's supported AutoSDK discovery. Compiler packages
and account state stay in ignored local storage. See `reports/toolchain.json`.
Generated Unreal Content, binaries and large scene files are excluded from Git;
they must accompany a source checkpoint archive or be regenerated.

After importing the scene, `pipeline/stream.ps1` runs the game offscreen and serves
the dashboard at http://127.0.0.1:5190/. Use Chrome. The sun follows the selected
Washington, DC date/time and the saved plan orientation. Intensity and seasonal
foliage remain approximations. See [streaming architecture, access setup and
encoder stability](docs/streaming.md). The original study remains separate.

`pipeline/import-runtime.ps1 -Resume` retries native material/motion setup from
the latest saved staging map without repeating the mesh import. Completed maps
are selected by reports/unreal-import.json, preserving previous map versions.

## GPU and memory settings

Double-click `Start-Walkthrough.cmd` to choose the rendering PC, adjust memory
pools/resolution/frame-rate/bitrate, and save or start the stream. Settings apply
on the next launch. Both presets keep the same complete source models and hardware
ray tracing; neither permanently reduces the exported tree or house geometry.

| Preset | Texture pool | Geometry pool | Video | FPS cap |
| --- | ---: | ---: | --- | ---: |
| RTX 2060 / 6 GB | 768 MB | 128 MB | 960x540, 67% internal resolution | 30 |
| RTX 5090 / 32 GB | 8192 MB | 1024 MB | 1920x1080, 100% internal resolution | 60 |

These are streaming-pool budgets, **not total VRAM limits**. Acceleration structures,
render targets, drivers and other apps also consume memory. The 5090 preset is
an untested starting configuration, not a performance guarantee. The laptop uses
High Lumen quality and ray-traced shadows; the 5090 preset uses Epic Lumen quality
and virtual shadows. FPS caps are targets, not measured performance.

Per-PC choices stay in ignored `.local/gpu-settings.json` and are excluded from
transfer archives. On the other computer, select the RTX 5090 preset. CLI usage:

```powershell
./pipeline/gpu-settings.ps1 -Profile RTX5090 -Save
./pipeline/gpu-settings.ps1 -TexturePoolMB 6144 -NanitePoolMB 512 -Save
./pipeline/stream.ps1
```

`pipeline/package-runtime.ps1` builds/cooks a standalone Windows application.
Source checkpoint ZIPs remain authoring archives; only a successfully packaged
and tested application can be run without installing Unreal and a compiler.
