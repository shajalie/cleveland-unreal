# Garden v3 review — September 8, 2026

The PNGs are unedited Chrome captures of the actual packaged Unreal video stream,
rendered on the RTX 2060 at 1920 × 1080. They are not generated concept images or
offline path-traced stills. The narrow browser viewport demonstrates the phone UI.

- `front-lawn.png`: individual blades, flowering entrance border and blue-gray path.
- `rear-lawn.png`: layered shrubs/ferns and pool-side planting.
- `pool-11am.png`: September 8 at 11 AM DC time; retained sky and water detail.
- `driveway.png`: surfaced driveway and its connection to the entrance.
- `interior.png`: indoor exposure retained with the new garden layer.
- `phone-settings.png`: lighting and geometry controls in the dashboard.
- `garden-before.png`: qualitative view from the earlier build. Its camera/time do
  not match the new captures, so this is not a controlled side-by-side comparison.

`physics.json` is emitted by the packaged game with `-ClevelandLandscapeVerify`.
All 837 floor samples and six capsule walks passed, with no accidental recovery.
The forced fall returned the pawn to safe ground. The same run switched four grass
clusters, 25 planting clusters and 40 wind material instances, verified the lighting
switches, rejected invalid settings, checked disk persistence and restored settings.

The Chrome test disabled all five effects, selected Cinematic lighting, 768 × 432
video with 50% internal resolution and a 2 FPS cap, and used Apply and restart.
The stream resumed at the requested video size and retained the disabled switches.
All effects were then enabled and the original full-HD/High quality settings restored.
Windows High performance was used for testing; the original power plan was restored.

This is a substantial landscape iteration, with estimated planting and grades.
Neighbor buildings remain simple masses and tree silhouettes, fences and house details
still differ from the photos. No claim of measured lighting accuracy or a finished
photoreal reconstruction is made. The 5090 preset has not been tested on a 5090.
