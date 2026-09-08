"""Build a project-local NVENC workaround from the user's installed engine.

Epic source stays ignored and is never included in source releases. The installed
engine is unchanged. See docs/streaming.md for the upstream issue and tradeoff.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "1d8c96a9253dd3550af835560cb4d2ac7b197f779993bd27d9d76923b551d2b2"
RELATIVE = "Source/NVENC/Private/Video/Encoders/VideoEncoderNVENC.cpp"
GUARD = """
        // Cleveland: avoid the D3D12 NVENC rate-reconfiguration commit leak.
        // Resolution/codec changes still follow the normal reconfigure path.
        // Bitrate changes in our dashboard restart the encoder explicitly.
        if (IsInitialized() && FParse::Param(FCommandLine::Get(), TEXT("ClevelandStableEncoder")))
        {
            PendingConfig.frameRateNum = AppliedConfig.frameRateNum;
            PendingConfig.frameRateDen = AppliedConfig.frameRateDen;
            auto& Rate = PendingConfig.encodeConfig->rcParams;
            const auto& AppliedRate = AppliedConfig.encodeConfig->rcParams;
            Rate.averageBitRate = AppliedRate.averageBitRate;
            Rate.maxBitRate = AppliedRate.maxBitRate;
            Rate.vbvBufferSize = AppliedRate.vbvBufferSize;
            Rate.vbvInitialDelay = AppliedRate.vbvInitialDelay;
        }
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, type=Path)
    args = parser.parse_args()
    source = args.engine / "Engine/Plugins/Experimental/AVCodecs/NVCodecs"
    raw = (source / RELATIVE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise RuntimeError("NVENC source changed. Review the workaround against this engine version before applying it.")
    target = ROOT / "runtime/ClevelandReal/Plugins/NVCodecs"
    patched = raw.decode("utf-8").replace("\r\n", "\n").replace(
        '#include "Templates/AlignmentTemplates.h"',
        '#include "Templates/AlignmentTemplates.h"\n#include "Misc/CommandLine.h"\n#include "Misc/Parse.h"',
    ).replace("\t\tif (AppliedConfig != PendingConfig)", GUARD + "\t\tif (AppliedConfig != PendingConfig)", 1)
    if (target / RELATIVE).exists() and (target / RELATIVE).read_text(encoding="utf-8") == patched:
        print("Project encoder workaround is ready")
        return
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "NVCodecs.uplugin", target / "NVCodecs.uplugin")
    shutil.copytree(source / "Source", target / "Source", dirs_exist_ok=True)
    (target / RELATIVE).write_text(patched, encoding="utf-8", newline="")
    (ROOT / ".local/encoder-workaround.json").write_text(json.dumps({
        "sourceSha256": EXPECTED,
        "patchedSha256": hashlib.sha256(patched.encode()).hexdigest(),
        "scope": "Project-local NVENC; fixed rates while streaming; no installed engine edits",
    }, indent=2))
    print("Prepared project-local NVENC workaround")


if __name__ == "__main__":
    main()
