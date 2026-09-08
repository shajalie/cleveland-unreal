# Garden v3

This separate version fills the missing outdoor ground and adds a photo-referenced
landscape layer. Lighting v2 and the original Sun Study remain available.

## Changes

- A closed ground mesh spans the property and its immediate surroundings. Explicit
  excavations preserve the house's lower floor, basement areaway and pool.
- The lawn has 693 shared patches with 256 tapered, bent blades each, following the
  local slope. Scanned ground texture remains visible beyond the blade draw distance.
- Layered scanned shrubs, ferns and low ground cover fill the side/rear borders.
  Flowering masses frame the front entrance. Pots and flowers follow the pool edge.
- The approach follows a curved stone path beside a widened concrete driveway.
  Concrete joints, roughness/normal textures, aggregate pool paving and rounded
  stucco planting beds replace featureless surfaces.
- Every new plant is nonblocking. A character that falls below the modeled world
  returns to its last verified standing position, retaining its streaming controls.
  The dashboard also offers **Return to safe ground** and three outdoor viewpoints.

The additional plants use hierarchical mesh instances and bounded draw distances.
Short grass has real geometry; larger plants preserve scanned cutout textures,
two-sided foliage shading and a small breeze. The phone continues to decode the
PC's video and send controls. GPU presets and all saved quality settings still apply.

## Phone controls

**Lighting & geometry** provides independent live switches for individual grass
blades, shrubs/leaves/flowers, breeze (including trees), ray-traced sun shadows and
Lumen reflections. They default to on and persist on the rendering PC across restarts.
Turning plants off preserves terrain collision, paving, pots and the house.

**Resolution & lighting quality** separates the video preset from High, Epic or
Cinematic indirect lighting/reflections. Resolution never switches off geometry.
The dashboard exposes frame limits from 2 to 120 FPS, internal rendering resolution,
video dimensions, bitrate, memory pools and optional virtual fallback shadow maps.
These settings use **Apply and restart renderer**. All viewers share one scene.

The owner can select an available Windows Balanced or High performance power plan
and restore the previous plan from the phone. This changes the Windows plan, not
thermal protections or GPU clock/voltage limits. The 2060 laptop was tested using
High performance; its prior plan is restored after testing.

Cinematic means Unreal's Lumen quality setting; it is not a converged offline path
trace or a measured lighting calibration. The 2060 may render slowly at high settings.
Lower the resolution independently or disable selected effects when desired.

## Evidence and limits

Placement is based on the saved listing photos, especially 00–03, 45, 47, 49 and 51,
and the March 27, 2025 DC OCTO orthophoto. The front flowering border, dense planting
beside the terraces, curved retaining beds and pool-edge pots come from those photos.
The CC0 scan provenance and hashes are in `design/landscape-sources.json`.

These are representative plant assets, not a botanical survey or a scan of the actual
garden. Unmeasured grades and obscured planting boundaries remain estimates. Foliage
and flowers retain their listing-photo appearance across the date controls. Neighbor
facades, some tree silhouettes and further house details still need reconstruction.
This improves the garden substantially without establishing photometric accuracy or
claiming a finished photoreal digital twin.

See `reports/landscape-v3` for actual runtime review. Collision verification uses the
packaged game's physics, not editor-only traces. It samples the outdoor floor grid,
walks six routes with the character capsule, and deliberately drops the pawn to test
automatic recovery. This does not exhaustively test every indoor circulation path.
The packaged probe also switches the actual vegetation components, wind material
parameters and lighting variables, checks invalid-setting rejection and persistence,
and restores the previous choices.

## Rebuild

Use the same Blender 4.5 and Unreal 5.8 setup as the base reconstruction:

```powershell
python pipeline/fetch_landscape_assets.py
blender -b --python-exit-code 1 --python pipeline/landscape/build.py
pipeline/build-runtime.ps1 -EngineRoot C:/Unreal/UE_5.8
# Run pipeline/unreal/import_landscape.py with Unreal's Python commandlet.
pipeline/build-runtime.ps1 -EngineRoot C:/Unreal/UE_5.8 -Game
pipeline/package-runtime.ps1 -EngineRoot C:/Unreal/UE_5.8 -SkipBuild
```

The importer duplicates the completed base map into a versioned map and gives this
layer its own asset package. It overrides old surface components without editing
the original imported meshes/materials. `reports/landscape-base-map.json` records
the preserved base; the selected map is in `reports/unreal-import.json`.

For the packaged physics check, launch the game with `-NullRHI -RenderOffscreen
-ForceRes -ResX=768 -ResY=432 -ClevelandLandscapeVerify` and
`-ClevelandLandscapeProbe="<absolute path>/Config/landscape-probes.json"`.
Set `__COMPAT_LAYER=HIGHDPIAWARE` on the child process, as the normal launcher does.
The result is saved under the game's `Saved/ClevelandReview/landscape-probe.json`.

## Transfer and rollback

The portable ZIP needs Windows and an NVIDIA driver; Blender and Unreal Editor are
unnecessary. Extract it and open `Start-Walkthrough.cmd`, then select the receiving
PC's GPU preset. The 5090 preset still needs testing on that hardware.

The separate editable checkpoint contains the base Blender scene, the landscape
Blender layer, its USD/texture/placement export, the CC0 source models and tracked
source files. Host credentials, email lists and runtime state are excluded.

To roll back, stop the current renderer/server and start the preserved Lighting v2
ZIP from its own folder. Both versions use the same local ports, so run one at a time.
