# Cleveland Real — independent reconstruction

This folder is a new reconstruction of 3014 Cleveland Avenue NW. It does not
replace the preserved Cleveland Sun Study build, running host, or published site.

**Current checkpoint:** Unreal Engine **5.8.2 is installed** on the authoring PC.
The C++ walking, hinged-door and ceiling-fan module compiles successfully.
The editable Blender scene now contains kitchen appliances and cabinetry,
four bathrooms/laundry fixtures, three furnished bedrooms, the sunroom office
and a populated lower library. GPU review renders remain approximations, with
photo matching still in progress. This is not a finished photoreal walkthrough.

The initial Unreal USD import created mesh assets but failed during native
material setup. That material error was fixed in an isolated engine probe.
The next import was stopped by Windows reporting an insufficient display
resolution, before the scene script ran. Full scene integration, actual Unreal
GPU rendering, runtime navigation and the replacement phone stream remain
unverified. The existing Sun Study site is preserved separately.

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
and the NVIDIA adapter. This launch path still needs GPU/runtime verification.
The walking controls are WASD/mouse or gamepad, E to interact, B to toggle subtle
camera sway. Phone touch controls and authenticated streaming are pending.

The sky is a review setup, not a calibrated date/time simulation. Interior views
use +2.1 exposure stops; the rear view uses -0.2. Photograph exposure and measured
daylight must not be confused. The current geometry tests do not establish
lighting accuracy or validate an Unreal runtime.
