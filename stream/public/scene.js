const zone = "America/New_York";
const formatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: zone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

export function localParts(seconds) {
  const p = Object.fromEntries(
    formatter
      .formatToParts(new Date(seconds * 1000))
      .map((x) => [x.type, x.value]),
  );
  return {
    date: `${p.year}-${p.month}-${p.day}`,
    minute: Number(p.hour) * 60 + Number(p.minute),
  };
}

// Resolve DC wall-clock time independently of the phone/host's timezone.
// The slider covers 05:00–22:00, outside the ambiguous DST transition hour.
export function studyUtc(date, minutes) {
  if (
    !/^20\d{2}-\d{2}-\d{2}$/.test(date) ||
    !Number.isInteger(minutes) ||
    minutes < 300 ||
    minutes > 1320
  )
    throw Error("Choose a valid date and a time between 5 AM and 10 PM.");
  const target = Date.parse(`${date}T00:00:00Z`) / 1000 + minutes * 60;
  let guess = target;
  for (let i = 0; i < 3; i++) {
    const p = localParts(guess);
    const actual = Date.parse(`${p.date}T00:00:00Z`) / 1000 + p.minute * 60;
    guess += target - actual;
  }
  const actual = localParts(guess);
  if (actual.date !== date || actual.minute !== minutes)
    throw Error("That local time does not exist.");
  return guess;
}

export const rooms = [
  [
    "Main floor",
    [
      ["living", "Living room"],
      ["foyer", "Foyer"],
      ["dining", "Dining room"],
      ["kitchen", "Kitchen"],
      ["breakfast", "Breakfast area"],
      ["study", "Study"],
      ["powder", "Powder room"],
    ],
  ],
  [
    "Upstairs",
    [
      ["primary", "Primary bedroom"],
      ["sunroom", "Sunroom"],
      ["yellow", "Yellow bedroom"],
      ["blue", "Blue bedroom"],
      ["primary-bath", "Primary bath"],
      ["hall-bath", "Hall bath"],
    ],
  ],
  [
    "Lower floor & garden",
    [
      ["lower", "Recreation room"],
      ["porch", "Front porch"],
      ["garden", "Back garden"],
      ["pool", "Pool terrace"],
    ],
  ],
];

export function installSceneControls({ stream, container, say }) {
  container.innerHTML = `
    <label for="room">Jump to a room or viewpoint</label><select id="room"></select>
    <button id="go-room">Go to viewpoint</button>
    <label for="study-date">Date</label><input id="study-date" type="date" min="2020-01-01" max="2030-12-31">
    <div class="row seasons"><button data-day="03-20">Spring</button><button data-day="06-21">Summer</button><button data-day="09-22">Autumn</button><button data-day="12-21">Winter</button></div>
    <label for="study-time">Time in Washington, DC · <output id="time-label"></output></label>
    <input id="study-time" type="range" min="300" max="1320" step="15" value="780">
    <div class="row times"><button data-time="540">9 AM</button><button data-time="720">Noon</button><button data-time="900">3 PM</button><button data-time="1080">6 PM</button></div>
    <p id="sun-status" class="hint" role="status">Waiting for scene controls…</p>
    <p id="lighting-version" class="hint"></p>
    <details><summary>View brightness</summary><label for="exposure">Exposure compensation · <output id="exposure-label">−0.5 stops</output></label><input id="exposure" type="range" min="-3" max="3" value="-0.5" step="0.25"></details>
    <p class="hint">Clear-sky lighting preview. Date and time move the sun; trees currently retain their modeled foliage. The reconstruction is still being checked against the photos.</p>`;
  const $ = (id) => document.getElementById(id);
  const names = new Map(rooms.flatMap((x) => x[1]));
  for (const [label, options] of rooms) {
    const group = document.createElement("optgroup");
    group.label = label;
    for (const [value, name] of options) group.append(new Option(name, value));
    $("room").append(group);
  }
  let ready = false,
    editingUntil = 0,
    pendingUtc = null,
    lastState;
  const send = (action, args = {}) => {
    if (action !== "status" && !ready) {
      say("Wait for the live scene to connect.");
      return;
    }
    stream.emitUIInteraction({
      protocol: "cleveland.scene.v1",
      action,
      ...args,
    });
  };
  const labelTime = () => {
    const m = Number($("study-time").value),
      hour = Math.floor(m / 60);
    $("time-label").textContent =
      `${hour % 12 || 12}:${String(m % 60).padStart(2, "0")} ${hour < 12 ? "AM" : "PM"}`;
  };
  const applyTime = () => {
    try {
      editingUntil = Date.now() + 2000;
      pendingUtc = studyUtc(
        $("study-date").value,
        Number($("study-time").value),
      );
      send("time", {
        utc: pendingUtc,
      });
      labelTime();
    } catch (error) {
      say(error.message);
    }
  };
  const initial = localParts(Date.now() / 1000);
  $("study-date").value = initial.date;
  labelTime();
  $("go-room").onclick = () => send("room", { room: $("room").value });
  $("study-date").onchange = applyTime;
  $("study-time").oninput = labelTime;
  $("study-time").onchange = applyTime;
  for (const button of container.querySelectorAll("[data-day]"))
    button.onclick = () => {
      $("study-date").value =
        `${$("study-date").value.slice(0, 4)}-${button.dataset.day}`;
      applyTime();
    };
  for (const button of container.querySelectorAll("[data-time]"))
    button.onclick = () => {
      $("study-time").value = button.dataset.time;
      applyTime();
    };
  $("exposure").oninput = () =>
    ($("exposure-label").textContent = `${$("exposure").value} stops`);
  $("exposure").onchange = () =>
    send("exposure", { value: Number($("exposure").value) });
  // Form keystrokes must not also walk the character through the SDK listener.
  container.addEventListener("keydown", (event) => event.stopPropagation());
  container.addEventListener("keyup", (event) => event.stopPropagation());
  stream.addResponseEventListener("cleveland-scene", (descriptor) => {
    let state;
    try {
      state = JSON.parse(descriptor);
    } catch {
      return;
    }
    if (state.protocol !== "cleveland.scene.v1") return;
    ready = true;
    $("lighting-version").textContent =
      state.lightingVersion === 2 && state.extendedExposureRange
        ? "Lighting v2 · automatic indoor/outdoor brightness"
        : "";
    $("location").textContent = names.get(state.room) || "Walkthrough";
    if (state.error) say(state.error);
    else if (lastState && lastState.room !== state.room)
      say(`Viewing ${names.get(state.room) || state.room}.`);
    else if (pendingUtc !== null && state.utc === pendingUtc) {
      say("Lighting updated on the rendering PC.");
      pendingUtc = null;
    }
    if (
      Date.now() >= editingUntil &&
      document.activeElement !== $("study-date") &&
      document.activeElement !== $("study-time")
    ) {
      const local = localParts(state.utc);
      $("study-date").value = local.date;
      $("study-time").value = local.minute;
      labelTime();
    }
    if (document.activeElement !== $("exposure")) {
      $("exposure").value = state.exposure;
      $("exposure-label").textContent = `${state.exposure} stops`;
    }
    $("sun-status").textContent =
      state.elevation > 0
        ? `Sun elevation ${state.elevation.toFixed(1)}° · azimuth ${state.azimuth.toFixed(1)}°`
        : "The sun is below the horizon.";
    lastState = state;
  });
  stream.addEventListener("webRtcDisconnected", () => {
    ready = false;
  });
  setInterval(() => {
    if (!document.hidden) send("status");
  }, 3000);
  return {
    get state() {
      return lastState;
    },
  };
}
