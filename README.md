# Cleveland Real — independent reconstruction

This folder is a new reconstruction of 3014 Cleveland Avenue NW. It does not
replace the preserved Cleveland Sun Study build, running host, or published site.

**Current checkpoint:** editable Blender authoring scene and four GPU-rendered
review views. Unreal is **not installed**, and this folder does not yet contain
a working Unreal application or a replacement phone stream. The review renders
are not yet photographically faithful enough to call this finished.

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
- `pipeline/unreal/`, `Source/ClevelandReal/`: reserved for the Unreal integration;
  not implemented in this checkpoint.
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
python -m unittest discover -s tests -v
blender -b --python-exit-code 1 --python pipeline/build_scene.py -- --samples 128
blender -b --python-exit-code 1 --python pipeline/validate_scene.py
./pipeline/doctor.ps1
```

The build requires an NVIDIA OptiX device and explicitly excludes CPU rendering.
The editable result is `SourceAssets/Cleveland-Reconstruction.blend`. Open that
file in Blender to inspect collections, materials and door pivots. Camera views
are saved in `reports/*-review.png`; this is not a packaged walkthrough.

The sky is a review setup, not a calibrated date/time simulation. Interior views
use +2.1 exposure stops; the rear view uses -0.2. Photograph exposure and measured
daylight must not be confused. The current geometry tests do not establish
lighting accuracy or validate an Unreal runtime.
