export function installControls({ video, look, interact, sway, stream }) {
  const held = new Set();
  function key(code, down) {
    if (down === held.has(code)) return;
    down ? held.add(code) : held.delete(code);
    document.dispatchEvent(
      new KeyboardEvent(down ? "keydown" : "keyup", {
        keyCode: code,
        which: code,
        bubbles: true,
      }),
    );
  }
  function release() {
    for (const code of [...held]) key(code, false);
  }
  for (const button of document.querySelectorAll("[data-key]")) {
    button.onpointerdown = (event) => {
      event.preventDefault();
      button.setPointerCapture(event.pointerId);
      stream.play();
      key(Number(button.dataset.key), true);
    };
    for (const name of ["pointerup", "pointercancel", "lostpointercapture"])
      button.addEventListener(name, () =>
        key(Number(button.dataset.key), false),
      );
  }
  const tap = (code) => {
    key(code, true);
    setTimeout(() => key(code, false), 100);
  };
  interact.onclick = () => tap(69);
  sway.onclick = () => tap(66);
  let last = null;
  look.onpointerdown = (event) => {
    event.preventDefault();
    look.setPointerCapture(event.pointerId);
    last = { x: event.clientX, y: event.clientY };
    video.dispatchEvent(new MouseEvent("mouseenter"));
  };
  look.onpointermove = (event) => {
    if (!last) return;
    const rect = video.getBoundingClientRect();
    video.dispatchEvent(
      new MouseEvent("mousemove", {
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
        movementX: event.clientX - last.x,
        movementY: event.clientY - last.y,
        bubbles: true,
      }),
    );
    last = { x: event.clientX, y: event.clientY };
  };
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"])
    look.addEventListener(name, () => {
      last = null;
    });
  window.addEventListener("blur", release);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) release();
  });
  stream.addEventListener("webRtcDisconnected", release);
}
