# Cleveland Real — independent reconstruction

This folder is a new reconstruction of 3014 Cleveland Avenue NW. It does not
replace the preserved Cleveland Sun Study build, running host, or published site.

**Current checkpoint:** Unreal Engine **5.8.2 is installed** on the authoring PC.
The C++ walking, hinged-door and ceiling-fan module compiles successfully.
The editable Blender scene now contains kitchen appliances and cabinetry,
four bathrooms/laundry fixtures, three furnished bedrooms, the sunroom office
and a populated lower library. GPU review renders remain approximations, with
photo matching still in progress. This is not a finished photoreal walkthrough.

The scene import now succeeds: 11,516 mesh components, 11 operable door
assemblies, three fan assemblies, native glass/water and 14 cutout tree-material
assignments. A DPI-aware child-process launch fixes the narrow logical screen
reported by a scaled phone RDP session. Windows network access is allowed.

The corrected native runtime renders and completed a short grounded walk. Chrome
decoded 272 H.264 frames at 960x540 with no dropped frames in a 23-second local
sample. It ran at approximately 11 FPS on the RTX 2060, below the 30 FPS target.
This is not yet a working remote walkthrough. See `reports/local-stream-verification.json`
and `reports/unreal-living-review.png`; excessive brightness and photo matching need work.

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
./pipeline/build-runtime.ps1
blender -b --python-exit-code 1 --python pipeline/export_unreal.py
blender -b --python-exit-code 1 --python pipeline/verify_usd.py
./pipeline/import-runtime.ps1
```

The build requires an NVIDIA OptiX device and explicitly excludes CPU rendering.
The editable result is `SourceAssets/Cleveland-Reconstruction.blend`. Open that
file in Blender to inspect collections, materials and door pivots. Camera views
are saved in `reports/*-review.png`; this is not a packaged walkthrough.

`build-runtime.ps1` uses an installed VS2022 toolchain, or a supplied portable
MSVC directory through Unreal's supported AutoSDK discovery. Compiler packages
and account state stay in ignored local storage. See `reports/toolchain.json`.
Generated Unreal Content, binaries and large scene files are excluded from Git;
they must accompany a source checkpoint archive or be regenerated.

After a successful scene import, `pipeline/launch.ps1 -Walk` requests DirectX 12
and the NVIDIA adapter. A short native walk and local video decode are verified;
whole-house circulation, interactive input and remote access remain pending.
The walking controls are WASD/mouse or gamepad, E to interact, B to toggle subtle
camera sway. Phone touch controls and authenticated streaming are pending.

The sky is a review setup, not a calibrated date/time simulation. Interior views
use +2.1 exposure stops; the rear view uses -0.2. Photograph exposure and measured
daylight must not be confused. The current geometry tests do not establish
lighting accuracy or validate an Unreal runtime.

## Local video preview

Install Node.js and run `pipeline/setup-streaming.ps1` to build the pinned Epic
UE5.8 streaming dependency. After a completed import, `pipeline/stream.ps1`
starts an offscreen Unreal process and a loopback-only video player at
http://127.0.0.1:5190/. Use Chrome. The browser receives WebRTC video; it does
not load or render the house geometry. Local decoded frames are verified. Epic's
internal backbuffer capture avoids the MediaCapture GPU-fence timeouts seen here.

The current preview is local only. Cloudflare allow-list access and the new
phone link remain unfinished. The original Sun Study host and site are untouched.
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
