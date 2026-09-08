import { installControls } from "./controls.js";
import { installSceneControls } from "./scene.js";
document.body.onload = null;
const $ = (id) => document.getElementById(id);
const sdk = window["epicgames-frontend"];
const config = new sdk.Config({
  useUrlParams: true,
  initialSettings: {
    AutoPlayVideo: true,
    AutoConnect: true,
    StartVideoMuted: true,
    WaitForStreamer: true,
    MaxReconnectAttempts: 100,
    HoveringMouse: true,
    MatchViewportRes: false,
    TouchInput: false,
    FakeMouseWithTouches: false,
    UseMic: false,
    UseCamera: false,
    SuppressBrowserKeys: false,
  },
});
const stream = new sdk.PixelStreaming(config, {
  videoElementParent: $("video"),
});
window.clevelandStream = stream;
const say = (message) => {
  $("notice").textContent = message;
};
const relaySetup = document.createElement("details");
relaySetup.innerHTML =
  '<summary>Video relay for phones without Tailscale</summary><p>Connect a Cloudflare Realtime TURN key for reliable video across different networks. Cloudflare includes a free allowance and bills additional usage.</p><label for="turnKeyId">TURN key ID</label><input id="turnKeyId" autocomplete="off"><label for="turnKey">TURN API token</label><input id="turnKey" type="password" autocomplete="off"><button id="save-relay">Connect video relay</button><p id="relay-status" role="status"></p>';
$("cloudflare-status").after(relaySetup);
let current,
  initialized = false,
  connected = false,
  draft,
  lastDecoded = 0,
  lastFrameAt = 0;
const fieldSpec = {
  texturePoolMB: ["Texture pool (MB)", 256, 24576],
  nanitePoolMB: ["Geometry pool (MB)", 64, 4096],
  rayTracingPoolMB: ["Ray-tracing pool (MB)", 256, 8192],
  width: ["Video width", 640, 3840],
  height: ["Video height", 360, 2160],
  screenPercentage: ["Internal resolution (%)", 25, 100],
  maxBitrateMbps: ["Bitrate limit (Mbps)", 2, 80],
};
for (const [key, [label, min, max]] of Object.entries(fieldSpec)) {
  const name = document.createElement("label");
  name.htmlFor = key;
  name.textContent = label;
  const input = document.createElement("input");
  input.id = key;
  input.type = "number";
  input.min = min;
  input.max = max;
  input.step = 1;
  $("advanced").append(name, input);
}
function showSettings(settings) {
  draft = { ...settings };
  $("profile").value = settings.profile;
  $("maxFPS").value = settings.maxFPS;
  $("lightingQuality").value = settings.lightingQuality;
  $("virtualShadows").checked = settings.virtualShadows;
  for (const key of Object.keys(fieldSpec)) $(key).value = settings[key];
  $("quality").value =
    settings.width === 768 && settings.screenPercentage === 50
      ? "performance"
      : settings.width === 1920 && settings.screenPercentage === 100
        ? "detail"
        : settings.width === 960 && settings.screenPercentage === 67
          ? "balanced"
          : "custom";
}
function values() {
  const settings = {
    ...draft,
    profile: $("profile").value,
    maxFPS: Number($("maxFPS").value),
    lightingQuality: Number($("lightingQuality").value),
    virtualShadows: $("virtualShadows").checked,
  };
  for (const key of Object.keys(fieldSpec))
    settings[key] = Number($(key).value);
  return settings;
}
async function api(route, body = {}) {
  const response = await fetch("/api/" + route, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw Error(result.error || "This action is unavailable");
  return result;
}
function action(id, work) {
  $(id).onclick = async () => {
    try {
      await work();
      await refresh();
    } catch (error) {
      say(error.message);
    }
  };
}
async function refresh() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok)
      throw Error("Your session needs an allowed email or Tailscale sign-in.");
    current = await response.json();
    $("gpu").textContent = current.settings.label + " · hardware ray tracing";
    if (!initialized) {
      showSettings(current.settings);
      initialized = true;
    }
    if (current.job.error) say(current.job.error);
    else if (current.job.busy) say(current.job.message);
    $("start").disabled = current.job.busy;
    $("apply").disabled = current.job.busy || !current.owner;
    $("stop").disabled = !current.owner;
    $("power-status").textContent =
      `Windows power plan: ${current.power?.name || "Unavailable"}`;
    $("power-balanced").disabled = !current.owner || current.power?.balanced;
    $("power-performance").disabled =
      !current.owner ||
      !current.power?.performanceAvailable ||
      current.power?.performance;
    $("power-restore").hidden = !current.power?.canRestore;
    $("power-restore").disabled = !current.owner;
    $("power-restore").textContent =
      `Restore ${current.power?.previousName || "previous plan"}`;
    if (!connected)
      $("waiting-message").textContent = current.rendererConnected
        ? "Connecting the video…"
        : "The rendering PC is ready. Start the walkthrough below.";
    const share = current.sharing;
    $("cloudflare-link").textContent =
      share.url || "Website sharing is not connected";
    $("cloudflare-link").href = share.url || "#";
    $("tail-link").textContent = current.tailscale.enabled
      ? current.tailscale.url
      : "Tailscale sharing is off";
    $("tail-link").href = current.tailscale.enabled
      ? current.tailscale.url
      : "#";
    $("cloudflare-status").textContent =
      share.job?.error ||
      share.job?.message ||
      (share.connected ? "Connected" : "Sharing is off");
    $("relay-status").textContent = current.relay.ready
      ? "Video relay connected"
      : current.relay.error;
    for (const key of ["accountId", "zoneId", "hostname"])
      if (document.activeElement !== $(key) && !$(key).value)
        $(key).value = share[key] || "";
    if (document.activeElement !== $("emails") && !$("emails").value)
      $("emails").value = (share.emails || []).join("\n");
    for (const id of [
      "save-emails",
      "enable-cloudflare",
      "disable-cloudflare",
      "configure-cloudflare",
      "enable-tail",
      "disable-tail",
      "save-relay",
    ])
      $(id).disabled = !current.owner;
  } catch (error) {
    say(error.message);
  }
}
stream.addEventListener("statsReceived", (event) => {
  const v = event.data.aggregatedStats.inboundVideoStats;
  if (v.framesDecoded !== lastDecoded) {
    lastDecoded = v.framesDecoded;
    lastFrameAt = Date.now();
  }
  if (v.framesDecoded > 0) {
    connected = true;
    $("waiting").hidden = true;
    $("stream-stats").textContent =
      `${Math.round(v.framesPerSecond || 0)} FPS · ${v.frameWidth}×${v.frameHeight} · ${v.framesDecoded} frames decoded`;
  }
});
stream.addEventListener("webRtcDisconnected", () => {
  connected = false;
  lastDecoded = 0;
  lastFrameAt = 0;
  $("waiting").hidden = false;
});
setInterval(() => {
  if (connected && lastFrameAt && Date.now() - lastFrameAt > 12000) {
    $("waiting").hidden = false;
    $("waiting-message").textContent =
      "Video has paused. Tap to resume, or reload to reconnect.";
    $("stream-stats").textContent = "Waiting for new video frames…";
  }
}, 3000);
stream.addEventListener("playStreamRejected", () => {
  $("waiting").hidden = false;
  $("waiting-message").textContent = "Tap to play the video.";
});
action("play", () => stream.play());
action("start", async () => {
  await api("runtime/start");
  stream.play();
  say("Starting the rendering PC. First load can take a minute.");
});
action("stop", () => api("runtime/stop"));
action("apply", async () => {
  await api("runtime/restart", { settings: values() });
  say("Applying settings and restarting the renderer…");
});
action("power-balanced", async () => {
  await api("power/balanced", {});
  say("Windows is using Balanced power.");
});
action("power-restore", async () => {
  await api("power/restore", {});
  say("The previous Windows power plan is restored.");
});
action("power-performance", async () => {
  await api("power/performance", {});
  say("Windows is using High performance power.");
});
$("profile").onchange = () => {
  showSettings({
    ...current.profiles[$("profile").value],
    profile: $("profile").value,
  });
};
$("quality").onchange = () => {
  const preset = $("quality").value;
  if (preset === "custom") return;
  const fast = preset === "performance",
    detail = preset === "detail";
  $("width").value = detail ? 1920 : fast ? 768 : 960;
  $("height").value = detail ? 1080 : fast ? 432 : 540;
  $("screenPercentage").value = detail ? 100 : fast ? 50 : 67;
};
action("fullscreen", () => $("stage").requestFullscreen?.());
$("connections").onclick = () => $("sharing").showModal();
$("close-sharing").onclick = () => $("sharing").close();
$("sharing").addEventListener("keydown", (event) => event.stopPropagation());
action("save-emails", () =>
  api("sharing/emails", { emails: $("emails").value }),
);
action("enable-cloudflare", () => api("sharing/enable"));
action("disable-cloudflare", () => api("sharing/disable"));
action("enable-tail", () => api("tailscale/enable"));
action("disable-tail", () => api("tailscale/disable"));
action("configure-cloudflare", async () => {
  await api("sharing/configure", {
    accountId: $("accountId").value,
    zoneId: $("zoneId").value,
    hostname: $("hostname").value,
    apiToken: $("apiToken").value,
    emails: $("emails").value,
  });
  $("apiToken").value = "";
});
action("save-relay", async () => {
  await api("sharing/relay", {
    turnKeyId: $("turnKeyId").value,
    turnKey: $("turnKey").value,
  });
  $("turnKey").value = "";
});
installControls({
  video: $("video"),
  look: $("look"),
  interact: $("interact"),
  sway: $("sway"),
  stream,
});
installSceneControls({ stream, container: $("scene-controls"), say });
for (const input of document.querySelectorAll(
  ".controls input,.controls select",
)) {
  input.addEventListener("keydown", (event) => event.stopPropagation());
  input.addEventListener("keyup", (event) => event.stopPropagation());
}
for (const key of Object.keys(fieldSpec))
  $(key).addEventListener("input", () => {
    $("quality").value = "custom";
  });
await refresh();
setInterval(refresh, 5000);
