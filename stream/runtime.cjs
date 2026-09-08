const fs = require("node:fs/promises");
const path = require("node:path");
const { execFile } = require("node:child_process");
const { promisify } = require("node:util");
const exec = promisify(execFile);
const ranges = {
  texturePoolMB: [256, 24576],
  nanitePoolMB: [64, 4096],
  rayTracingPoolMB: [256, 8192],
  width: [640, 3840],
  height: [360, 2160],
  screenPercentage: [25, 100],
  maxFPS: [15, 120],
  maxBitrateMbps: [2, 80],
  lightingQuality: [2, 3],
};

class RuntimeController {
  constructor(root) {
    this.root = root;
    this.job = { busy: false, message: "Ready", error: "" };
  }
  async catalog() {
    return JSON.parse(
      await fs.readFile(
        path.join(this.root, "Config/gpu-profiles.json"),
        "utf8",
      ),
    ).profiles;
  }
  async settings() {
    let saved = {};
    try {
      saved = JSON.parse(
        await fs.readFile(
          path.join(this.root, ".local/gpu-settings.json"),
          "utf8",
        ),
      );
    } catch {}
    return this.validate(saved);
  }
  async validate(input) {
    const catalog = await this.catalog();
    const profile = input.profile || "Laptop";
    if (!Object.hasOwn(catalog, profile)) throw Error("Unknown GPU preset");
    const result = { ...catalog[profile], profile };
    for (const [key, [min, max]] of Object.entries(ranges)) {
      if (input[key] !== undefined) result[key] = input[key];
      if (
        !Number.isInteger(result[key]) ||
        result[key] < min ||
        result[key] > max
      )
        throw Error(`Invalid ${key}`);
    }
    return result;
  }
  async save(input) {
    const settings = await this.validate(input);
    await fs.mkdir(path.join(this.root, ".local"), { recursive: true });
    const file = path.join(this.root, ".local/gpu-settings.json");
    await fs.writeFile(file + ".tmp", JSON.stringify(settings, null, 2));
    await fs.rename(file + ".tmp", file);
    return settings;
  }
  async command(action) {
    const { stdout } = await exec(
      "powershell.exe",
      [
        "-NoProfile",
        "-File",
        path.join(this.root, "pipeline/runtime-control.ps1"),
        "-Action",
        action,
      ],
      { cwd: this.root, windowsHide: true, timeout: 45000, maxBuffer: 20000 },
    );
    return stdout;
  }
  run(action, settings) {
    if (this.job.busy)
      throw Error("The rendering PC is already applying a change");
    this.job = {
      busy: true,
      message:
        action === "stop"
          ? "Stopping walkthrough"
          : "Starting walkthrough; first load may take a minute",
      error: "",
    };
    Promise.resolve()
      .then(async () => {
        if (settings) await this.save(settings);
        if (action !== "start") await this.command("Stop");
        if (action !== "stop") await this.command("Start");
        this.job.message =
          action === "stop" ? "Walkthrough stopped" : "Waiting for video";
      })
      .catch((error) => {
        this.job.error = error.message;
        this.job.message = "Could not apply change";
      })
      .finally(() => {
        this.job.busy = false;
      });
  }
}
module.exports = { RuntimeController, ranges };
