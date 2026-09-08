# Reconstruction decisions

## Evidence read directly

- Photos 03–04: a raised terracotta porch, stone stair approach, planters, black
  paneled entry with sidelights and transom; the vehicle drive passes under the
  right end of the porch. The stairs and carport are different routes.
- Photos 05–06 and 25–26: a continuous straight timber stair, iron balusters,
  timber handrail, landing and actual upper-floor opening.
- Photos 07–14: a long living room, brown leather sofa opposite the fireplace,
  timber lounge chairs angled toward the seating group, rugs, art, lamps, plants,
  books and tables. The study connects through one full-height arch with smaller
  flanking pass-throughs, and has an operable arched glazed rear door.
- Photos 15–17: dining table, correctly facing chairs, sideboard, rug, and a
  glazed door opening to the front porch. Avoid invented decorative clutter.
- Photos 18–22: galley cabinetry, glazed upper doors, appliances, backsplash,
  runner and breakfast area. The kitchen is not an empty rectangular room.
- Photos 27–41: three bedrooms, sunroom, bathrooms and furnished landing; use
  furnishings and openings visible in each view, with inferred details identified.
- Photos 43–44: the lower level has a long recreation room, piano and shelving.
- Photos 47 and 51–52: upper sitting terrace, lower dining terrace and still-lower
  pool deck are distinct elevations. The arched study door has brick threshold
  steps; decorated risers connect the terraces. A basement exterior door opens
  into the depressed area beside the pool deck. Railings must protect actual drops.
- Photos 49–50: a contained pool with submerged entry steps. Add small wind-driven
  ripples and plausible circulation, not an invented river or waterfall.
- Photo 55: the main plan labels a 25-foot by 13-foot living room and 9-foot
  6-inch main ceiling; the upper ceiling is 9 feet. Printed dimensions are
  approximate. The 630×394 diagram is not a survey and must not be stretched
  independently in ways that break shared walls or stair connections.

## Representation

Meters, right-handed: +X toward the right of the front elevation, +Y toward the
back garden, +Z upward. Main finished floor is Z=0. Unreal import maps to
centimeters and preserves the recorded geospatial orientation explicitly.

Floor heights, door thresholds, terrace surfaces and individual stair risers are
connected constraints. A portal must join two reachable spaces. Furniture
orientation is defined relative to its use (table, television, fireplace), and
must leave a walking route and door-swing clearance.

Physical material detail spans form, millimeter-scale relief, roughness and color.
Do not turn every curved object into a many-sided box or flatten imported normals.
Inspect representative silhouette edges and close views before adding copies.

## Runtime and rendering target

Unreal 5.8 is the current published release as of this work. Epic's installed
engine and final tested version will be recorded separately after installation.
The laptop has an RTX 2060 Max-Q with 6 GB VRAM, below Epic's 8 GB recommended
graphics memory. Optimize to a measured budget; do not promise 60 fps or instant
converged path tracing. Pixel Streaming is the target phone transport, with PC
encoding and the existing build's access design retained as a separate service.

Small breeze motion, pool ripples and soft vegetation response belong in the
interactive scene. For path-traced sequences, sample animation at defined times;
never let changing simulation states contaminate one accumulated still.

References: https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available
and https://dev.epicgames.com/documentation/en-us/unreal-engine/path-tracer-in-unreal-engine

## Installation status

The existing Epic Games Launcher was found. Its log subsequently identified
`FWindowsPlatformMisc::PlatformPreInit.ResolutionTooLow` on the remote display,
and the process exits without exposing a window. Supported window-size arguments
did not resolve it. A command-line client authenticated successfully to the
existing Epic account, but its catalog contained no Unreal engine assets. The
alternate Cosmos session discovery endpoint returned HTTP 404. No authentication
or access protections were disabled. All account state remains in ignored local
storage. Unreal has not been installed or tested. A usable local desktop/launcher
session is needed to proceed with the official installation.
Visual Studio Build Tools 2019 and Windows SDK 19041 were found; a C++ UE5.8
build requires a newer supported toolchain. Geometry preparation can proceed
without those installs.

## Current review findings

The generated scene now has a real upper stairwell opening, consistent stair
heights, individually hinged exterior door leaves, a paneled front entry,
three garden elevations, foundation walls, a separate carport route, rounded
furnishings, folded curtains, woven patio seats, barrel roof tiles, GIS neighbor
masses and scanned vegetation. Main-stair headroom and door transformations are
checked against evaluated mesh geometry, not just the connection graph.

The current renders remain visibly incomplete compared with the listing:
mantel carving and chimney breast, artwork, patterned rugs, lamps, detailed
cabinetry/appliances, upholstered shapes and exact window joinery require further
work. The study recliner currently uses a representative brown scanned asset;
the photograph shows green leather. Upper rooms and the basement interior are
not fully furnished. Wind, circulation animation, Unreal import, runtime
navigation and the new authenticated phone stream are not implemented.

The pool's aerial trace is larger than the approximate 20-by-10-foot listing
label. Its current review placement has not yet been reconciled to the new
unwarped GIS transform. The courtyard's individual stair counts and levels are
inferred. Do not treat these as surveyed measurements or use these review views
as validated quantitative daylight predictions.
