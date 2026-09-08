const options = [
  ["grass", "Individual grass blades"],
  ["plants", "Garden shrubs, leaves and flowers"],
  ["breeze", "Breeze in grass, plants and trees"],
  ["rayShadows", "Ray-traced sun shadows"],
  ["reflections", "Lumen reflections"],
];

export function installEffectsControls({ container, send, say }) {
  const controls = new Map();
  const pending = new Map();
  const heading = document.createElement("h3");
  heading.textContent = "Lighting & geometry";
  container.append(heading);
  for (const [key, title] of options) {
    const label = document.createElement("label");
    label.className = "effect-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.id = `effect-${key}`;
    input.checked = true;
    input.disabled = true;
    label.append(input, document.createTextNode(title));
    container.append(label);
    controls.set(key, input);
    input.onchange = () => {
      if (send("effects", { effects: { [key]: input.checked } }) === false)
        return;
      pending.set(key, { value: input.checked, until: Date.now() + 15000 });
      input.disabled = true;
      say("Applying visual settings on the rendering PC…");
    };
  }
  const hint = document.createElement("p");
  hint.className = "hint";
  hint.textContent =
    "These switches change live and are remembered on this PC. All viewers share the same scene. Ground collision stays active when vegetation is hidden.";
  container.append(hint);
  return {
    update(state) {
      for (const [key, input] of controls) {
        if (typeof state?.[key] !== "boolean") {
          input.disabled = true;
          continue;
        }
        const edit = pending.get(key);
        if (edit && edit.value !== state[key] && edit.until > Date.now())
          continue;
        if (edit && edit.value === state[key])
          say("Visual settings updated and saved on the rendering PC.");
        pending.delete(key);
        input.checked = state[key];
        input.disabled = false;
      }
    },
    disconnect() {
      pending.clear();
      for (const input of controls.values()) input.disabled = true;
    },
  };
}
