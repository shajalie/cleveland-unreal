# Lighting v2

This version fixes daylight exposure in the native Unreal walkthrough. The
previous downloadable build remains under the
[September 8 streaming checkpoint](https://github.com/shajalie/cleveland-unreal/releases/tag/streamed-walkthrough-2026-09-08).
The original Sun Study site is a separate preserved application.

## Cause and correction

The scene uses a directional sun in physical lux, but the project did not opt
into extended exposure. Inspection of the installed Unreal 5.8.2 source found
that the bare-engine console-variable default is still zero: legacy camera
defaults limit metering to 8 cd/m², with a histogram maximum of log₂ 4. That
range cannot meter a sunlit terrace. The 11 AM pool and sky reproduced the
reported white clipping at the unchanged −0.5-stop compensation.

`DefaultEngine.ini` now enables extended luminance. `DaylightExposure` sets the
walking camera to histogram metering from −4 to 20 EV100 and a histogram range
of −8 to 20 EV100. This covers dim interiors and daylight; the user’s exposure
compensation remains available. Epic describes the relationship between
[physical lighting and EV100 exposure](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-physical-lighting-units-in-unreal-engine)
and the [exposure controls](https://dev.epicgames.com/documentation/unreal-engine/auto-exposure-in-unreal-engine).

Brightness adapts at 6 stops/second toward a brighter scene and 2 stops/second
toward a darker one. Room teleports and date/time jumps reset the exposure
history using Unreal’s camera-cut API, rather than carrying a dark room’s
exposure into the backyard. Normal walking keeps continuous adaptation.

The outdoor review also exposed Unreal’s warning about float16 lighting-cache
clipping. `r.EyeAdaptation.CachedLightingPreExposure=8` uses the engine’s
documented physical-lighting cache scale (approximately −4 to +16 EV of safe
view exposure). Lumen and the real-time sky capture apply/invert this scale;
it preserves the lighting values instead of suppressing the warning.

The time controls no longer discard a scene edit that arrives immediately
after a status poll or another edit. The browser confirms a time change only
after receiving that exact UTC time from the renderer.

Sun position, estimated clear-sky illuminance, atmosphere scattering, material
albedo, ray tracing, geometry, bloom, and the saved GPU profile are unchanged.
The camera adjustment affects the displayed image, not the lighting simulation.
The dashboard only shows “Lighting v2” after the native renderer reports both
the new version and the active extended exposure setting.

## Review and limitations

Review images and the measured comparison are recorded in `reports/lighting-v2`.
They are actual Chrome captures of the PC-rendered video, with the same 2060
More FPS settings (768×432 output, 50% internal screen percentage).

This correction does not establish measured daylight accuracy or finish the
architectural/material reconstruction. The sun remains an estimated clear-sky
model, seasonal foliage is not simulated, and streamed Lumen rendering is not
a converged offline path trace. The portable 5090 profile still needs testing
on that GPU.

## Reproduce and roll back

Build the native game with `pipeline/build-runtime.ps1 -Game`, then package it
with `pipeline/package-runtime.ps1 -SkipBuild -SkipCook` if the existing scene
is already cooked. Config and C++ changes need new staging; changed scene
assets require cooking again. The portable packager records file hashes.

For rollback, extract the previous release ZIP to another folder, stop the
current renderer/server, and start that copy. Keep hosting credentials on the
rendering PC; they are not in either ZIP. The previous cooked and portable
build directories are also retained locally. Do not run both versions on the
same streaming ports simultaneously.
