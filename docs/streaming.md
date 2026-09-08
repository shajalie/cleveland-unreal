# Streamed walkthrough

The new dashboard uses ports 5190 (HTTP/player signalling) and 5191 (the Unreal
streamer). Both listeners bind only to loopback. The original 5182 site remains
separate. Chrome receives H.264 video and sends movement and scene commands;
it does not download house meshes or run the Unreal renderer on the phone.

`Start-Walkthrough.cmd` opens the local Chrome dashboard. The standalone Windows
ZIP includes the cooked game, Node, pinned Epic signalling/player dependencies,
Cloudflared and the host UI. Blender and the Unreal editor are only required for
authoring, not for running the ZIP. Extract everything before opening the launcher.
Choose a GPU preset and apply changes in the dashboard. A new PC starts with safe
laptop defaults, or the 5090 preset if that adapter is detected. The 5090 remains
untested on actual hardware.

## Connections

Tailscale is optional. Install/sign into Tailscale on the PC and phone, then use
Connection options → Enable private link. The script uses the existing Windows
Tailscale Serve host and owns only HTTPS port 5190. It does not enable Funnel or
alter the old study's mappings. The local server checks the identity header
injected by Serve. Only the configured owner's identity gets host controls.

Cloudflare sharing creates a separate Access application, an exact-email policy,
an application-specific tunnel and an unused DNS hostname. The application checks
Access JWT signatures, issuer, audience, expiry and the current email list again
at the origin. Only the owner can change hosting or GPU settings. All approved
viewers can navigate the shared scene; simultaneous viewers share one camera/time.
Changes to sharing authorization close existing Cloudflare signalling sockets.
WebSocket connections also close when the one-hour Access token expires.

Cloudflare HTTP tunnels carry the website and signalling, not WebRTC UDP media.
A Cloudflare Realtime TURN key is needed for reliable media across networks where
direct connectivity fails. Realtime requires a separately activated subscription
with a free allowance and usage billing. Account activation is still pending owner
approval on the authoring PC. Until configured and tested, use Tailscale for the
working phone stream; the Cloudflare login page alone does not prove video works.

Each receiving PC needs an unused hostname and its own one-time setup. For the
hosting API token, use the account's Access apps/policies/identity-provider,
Cloudflare Tunnel and zone DNS permissions needed by the setup calls. A TURN key
is separate from this hosting token. Configuration forms never return secret values.
Secrets are protected by Windows DPAPI for the hosting Windows user under `.local/`.
Credentials, email lists, tunnel tokens and saved GPU choices are excluded from
the ZIP and Git. Changing the email list requires keeping the hosting owner.

## Encoder stability

On September 8 the default D3D12 H.264 streaming process reached about 72 GB of
private committed memory while its working set remained around 3.6 GB. This
matches the upstream [NVENC rate-reconfiguration issue](https://github.com/EpicGames/PixelStreamingInfrastructure/issues/954).
Epic's CUDA compatibility option streamed successfully on the 2060 with roughly
6.4 GB of private commit in a short local test. It is reported problematic on
50-series hardware, so it is not the portable default.

`pipeline/prepare_encoder.py` copies the installed NVCodecs plugin into ignored
project storage and applies a small, opt-in rate guard. It validates the source
SHA-256 before patching. The installed engine is untouched and Epic source is
excluded from Git/source releases. The game compiles the local plugin and launches
with `-ClevelandStableEncoder`. Once initialized, the guard keeps bitrate, FPS and
derived VBV settings stable; resolution/codec changes still follow normal logic.
This avoids the repeated leaking rate-only `nvEncReconfigureEncoder` calls.
The dashboard applies a new bitrate by restarting the renderer. The tradeoff is
fixed-rate encoding: lower the bitrate setting on a constrained mobile connection.
Short-run measurements are recorded in the release verification report; they do
not establish stability for indefinite sessions or every driver/GPU combination.

## Scene controls

The browser emits a constrained `cleveland.scene.v1` JSON protocol through the
Pixel Streaming data channel. It accepts known room IDs, a bounded UTC timestamp
and exposure compensation. It does not execute arbitrary console commands, file
paths or browser-supplied camera transforms. Room jumps test floor support and
capsule clearance. `Config/scene-views.json` stores editable host-side viewpoints
in model metres (+X right, +Y rear); the runtime converts to Unreal centimetres
and reverses Y. Scene acknowledgements update the UI after the game accepts input.

The sun uses Epic's SunPosition calculator at 38.92485352, -77.06033745 and the
saved plan's north basis. The UI always uses Washington, DC time, including DST.
The sky intensity remains an approximate clear-sky model, not measured lux.
Foliage does not yet change with the selected season. Lumen hardware ray tracing
is used for navigation; it is not a converged full path-traced still render.

## Validation

Run `node tests/dashboard-security.cjs` for settings limits, signed identity,
revocation, origins and DST conversion. Run `node tests/stream-smoke.cjs` against
the local dashboard for HTTP/WebSocket restrictions. Verify decoded video, room
acknowledgements, walking/look input and private commit on the actual GPU before
publishing. For code-only changes after a successful cook,
`pipeline/package-runtime.ps1 -SkipBuild -SkipCook` re-stages the existing content;
changed content or map configuration requires a fresh cook.
