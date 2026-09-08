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

Unreal Engine 5.8.2 was installed through Epic Games Launcher at
`C:/Unreal/UE_5.8`. The native project module compiles with Microsoft MSVC
14.44.35228 and Windows SDK 10.0.26100.0. Microsoft packages were downloaded
from their CDN, checksum-verified and extracted to a task-owned tools directory.
Unreal AutoSDK junctions discover that toolchain without engine/registry changes.
The standard VS2022 bootstrapper previously exited 1602; it is not the successful
compiler installation. No account state or compiler redistribution is in Git.

The original USD import created geometry assets but failed at native water
material construction. The corrected water material passed an isolated Unreal
Python probe. A subsequent full import exited during Windows PlatformPreInit
with ResolutionTooLow before Python ran. Do not infer success from its zero
process exit code. No final Unreal map, GPU view, walking test or phone stream
has passed verification yet.

## Current review findings

The generated scene now has a real upper stairwell opening, consistent stair
heights, individually hinged exterior door leaves, a paneled front entry,
three garden elevations, foundation walls, a separate carport route, rounded
furnishings, folded curtains, woven patio seats, barrel roof tiles, GIS neighbor
masses and scanned vegetation. Main-stair headroom and door transformations are
checked against evaluated mesh geometry, not just the connection graph.

The current renders remain visibly incomplete compared with the listing:
mantel carving and chimney breast, artwork, patterned rugs, lamps, detailed
upholstered shapes and exact window joinery require further work. The new kitchen
and bathroom assemblies include cabinets, sinks, appliances and sanitary fixtures. The study recliner currently uses a representative brown scanned asset;
the photograph shows green leather. Upper rooms and the basement now have their principal furnishings, but exact
textiles, artwork, small objects and some fitted cabinetry remain incomplete. Wind, circulation animation, Unreal import, runtime
navigation and the new authenticated phone stream are not implemented.

The pool's aerial trace is larger than the approximate 20-by-10-foot listing
label. Its current review placement has not yet been reconciled to the new
unwarped GIS transform. The courtyard's individual stair counts and levels are
inferred. Do not treat these as surveyed measurements or use these review views
as validated quantitative daylight predictions.

## Room reconstruction decisions in the second checkpoint

All 56 saved Compass photographs were viewed in contact sheets; kitchen,
bathroom and bedroom views were also inspected individually. The kitchen has
hardwood flooring, white casement frames, paneled/glazed cupboards, range and
microwave, apron sink, dishwasher, refrigerator and breakfast furniture.
Four bathrooms have separate shower, vanity, toilet and laundry assemblies.
The primary, blue and yellow bedrooms, office sunroom and lower library now
have distinct furniture rather than empty shells. Surfaces and motifs remain
representative; object presence is not proof of a photographic match.

The old trace's secondary primary-bath opening intersected the photographed
shower and was removed; the bedroom-side entrance remains. Lower bathroom
partitions were inferred from photos 42�44 and plan 55, not a measured survey.
Sunroom glass doors are now built despite being an internal opening.

Review rendering exposed and corrected a stale transform evaluation that
magnified fixture knobs, vanity/basin overlap, incorrect plaid on plain bedding,
and duvet/mattress intersection. A rotated vegetation anchor was corrected.
Revalidate these changes in the final saved scene and in Unreal.

## Foliage opacity and crown correction

The imported broadleaf material connected the alpha output of a JPG base-color
image to opacity. JPG carries no alpha, so whole leaf polygons were visible.
The reconstruction now uses Poly Haven's original grayscale leaf/needle masks,
with non-color sampling and the original UV coordinates. Source URLs, CC0
licenses and checksums are in reference/materials/foliage/sources.json.

Tree height scaling had also enlarged crown widths beyond the aerial estimates.
Height and crown width are now constrained separately. Crown radius is limited
to leave 0.25 m building clearance; this is an explicit geometry assumption,
not a statement about surveyed pruning or exact real-world canopy dimensions.
The representative tree species still require reference matching.

The prior source-library preparation also decimated the broadleaf mesh to
110,000 polygons. This can collapse leaf cards and their UV boundaries. The
new prepare_vegetation.py preserves the original mesh/UVs in a separate packed
library. It does not change the old project's asset library.


## Final room-detail review in the furnished checkpoint

Photos 15 and 23 informed the dining hutch's north-wall position, adjacent
kitchen doorway and powder-room window position. These are photographic
inferences, not surveyed coordinates. The dining table is oval and a modeled
fabric drum pendant hangs above it. The powder blind has individual slats.
Three pictures use UV regions from the unmodified listing photos (15, 23, 35).
These retain photographed illumination and are appearance proxies, not measured
surface reflectance. Final dining, kitchen, powder and blue-bedroom review
images were rendered after these changes. Other views predate this detail pass.

The blue-bedroom window/bed orientation still requires multi-view registration.
The primary bathroom still needs the reference's two-drawer flat-basin vanity,
two side sconces, green marble/mosaic appearance and shutters. Rug motifs,
chairs, bedding and smaller domestic objects remain representative.

The nearby public street-tree inventory is saved as additional evidence only.
Its records have not been registered to the modeled crowns, and its species
and height fields have not been applied to private garden trees.
