"""Stage a portable Windows game and its local video server, excluding PC state."""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_tree(source, destination):
    # Materialize npm workspace junctions. Absolute links to this authoring PC
    # must never be required on the receiving computer.
    shutil.copytree(
        source,
        destination,
        symlinks=False,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git", ".env", ".env.*", "*.log", "*.pdb", "Saved", "Crashes"
        ),
    )


def main():
    cooked = Path((ROOT / ".local/latest-cooked-build.txt").read_text().strip()).resolve()
    if not cooked.is_relative_to(ROOT / "Builds"):
        raise ValueError("Cooked build must be inside this project's Builds directory")
    if not (cooked / "Windows/ClevelandReal.exe").is_file():
        raise FileNotFoundError("No packaged Unreal executable")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = ROOT / "Builds" / f"portable-{stamp}" / "cleveland-unreal"
    target.mkdir(parents=True)
    copy_tree(cooked / "Windows", target / "runtime/Windows")
    files = [
        "Start-Walkthrough.cmd",
        "Config/gpu-profiles.json",
        "Config/scene-views.json",
        "Config/landscape-probes.json",
        "pipeline/gpu-settings.ps1",
        "pipeline/settings-ui.ps1",
        "pipeline/open-dashboard.ps1",
        "pipeline/runtime-control.ps1",
        "pipeline/power-mode.ps1",
        "pipeline/phone-access.ps1",
        "pipeline/launch.ps1",
        "pipeline/stream.ps1",
        "stream/server.cjs",
        "stream/runtime.cjs",
        "stream/access.cjs",
        "stream/turn.cjs",
        "stream/package.json",
        "stream/package-lock.json",
        "stream/dependency.json",
        "reports/unreal-import.json",
        "reports/local-stream-verification.json",
        "reports/dashboard-verification.json",
        "docs/streaming.md",
        "docs/lighting-v2.md",
        "docs/landscape-v3.md",
    ]
    for name in files:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    for name in [
        "stream/public",
        "stream/cloudflare",
        "stream/node_modules/jose",
        "reports/lighting-v2",
        "reports/landscape-v3",
    ]:
        copy_tree(ROOT / name, target / name)
    (target / "tools").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "tools/cloudflared.exe", target / "tools/cloudflared.exe")
    shutil.copy2(ROOT / ".local/cloudflared-LICENSE", target / "tools/cloudflared-LICENSE")

    upstream = ROOT / ".local/pixel-streaming-infrastructure"
    bundled = target / ".local/pixel-streaming-infrastructure"
    bundled.mkdir(parents=True)
    for name in ["package.json", "LICENSE.md"]:
        shutil.copy2(upstream / name, bundled / name)
    copy_tree(upstream / "SignallingWebServer/www", bundled / "SignallingWebServer/www")
    packages = subprocess.check_output(
        [
            shutil.which("npm.cmd"),
            "ls",
            "--omit=dev",
            "--parseable",
            "--all",
            "--workspace",
            "Signalling",
        ],
        cwd=upstream,
        text=True,
    ).splitlines()
    for name in packages:
        package = Path(name)
        if package == upstream:
            continue
        # Validate the lexical location as well as a junction's resolved target.
        relative = package.relative_to(upstream)
        if relative.parts[0] != "node_modules" or not package.resolve().is_relative_to(upstream):
            raise ValueError(f"Unexpected dependency location: {package}")
        copy_tree(package, bundled / relative)

    node = Path(shutil.which("node.exe"))
    node_target = target / "tools/node"
    node_target.mkdir(parents=True)
    shutil.copy2(node, node_target / "node.exe")
    shutil.copy2(ROOT / ".local/node-LICENSE", node_target / "LICENSE")
    (target / "READ-ME-FIRST.txt").write_text(
        "Cleveland Unreal - Garden v3\n\n"
        "1. Extract the whole ZIP to a local folder. Do not run inside the ZIP.\n"
        "2. Double-click Start-Walkthrough.cmd.\n"
        "3. Chrome opens http://127.0.0.1:5190/. The first load can take a minute.\n"
        "4. Choose the GPU preset, video resolution, lighting quality and memory pools.\n"
        "Use Apply and restart for those settings. Live Lighting & geometry switches\n"
        "control grass, plants, breeze, ray-traced sun shadows and Lumen reflections.\n"
        "The PC remembers the live switches. Lower resolution retains scene geometry.\n\n"
        "No Blender, Unreal Editor, compiler, Node installation or account credentials are required.\n"
        "An NVIDIA driver and Windows are required. Epic's prerequisite installer is included\n"
        "under runtime/Windows/Engine/Extras/Redist/en-us if Windows needs runtime libraries.\n"
        "Controls: WASD/mouse, E interact, B optional camera sway.\n\n"
        "Phone access: open Connection options. Tailscale is optional and needs\n"
        "Tailscale signed in on both devices. Its private link is generated on this PC.\n"
        "Cloudflare uses an unused hostname, an account API token and allowed emails.\n"
        "Connect a Realtime TURN key for video across different networks without Tailscale.\n"
        "Cloudflare Realtime requires separate activation and can bill usage.\n"
        "Hosting credentials and email lists are NOT included; connect each new PC once.\n"
        "Moonlight can separately show the PC. Only this app is exposed by its tunnel.\n"
        "The original Sun Study site is unchanged.\n\n"
        "Lighting v2 corrects outdoor exposure and Lumen/sky lighting-cache range.\n"
        "See docs/lighting-v2.md and reports/lighting-v2 for the visual review.\n\n"
        "Garden v3 adds continuous outdoor ground, detailed grass/planting, textured\n"
        "paving and automatic fall recovery. See docs/landscape-v3.md.\n\n"
        "This is a furnished reconstruction in progress, not a photometrically calibrated\n"
        "digital twin. Layout/material/reference matching and full circulation need review.\n"
        "The RTX 5090 preset is untested on that GPU. H.264 video uses a fixed bitrate\n"
        "to avoid an NVENC driver issue; lower the bitrate if your connection stutters.\n"
        "Both presets retain full scene geometry. Memory pools are not total VRAM limits.\n",
        encoding="utf-8",
    )
    manifest = {
        "kind": "Standalone Windows walkthrough with authenticated streaming dashboard",
        "sourceCommit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "nodeVersion": subprocess.check_output([str(node), "--version"], text=True).strip(),
        "files": [],
    }
    for path in sorted(target.rglob("*")):
        if path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            manifest["files"].append(
                {
                    "path": path.relative_to(target).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                }
            )
    (target / "portable-manifest.json").write_text(json.dumps(manifest, indent=2))
    (ROOT / ".local/latest-portable-build.txt").write_text(str(target))
    print(json.dumps({"directory": str(target), "files": len(manifest["files"])}))


if __name__ == "__main__":
    main()
