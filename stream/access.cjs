const fs = require("node:fs");
const path = require("node:path");
const loopback = (address) =>
  ["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(address);

function createAccess(root, port, sharing, verifyCloudflare) {
  function tailConfig() {
    try {
      return JSON.parse(
        fs.readFileSync(path.join(root, ".local/tailscale.json"), "utf8"),
      );
    } catch {
      return { enabled: false };
    }
  }
  async function authenticate(req) {
    if (!loopback(req.socket.remoteAddress))
      throw Error("Local proxy required");
    const host = req.headers.host || "";
    if ([`127.0.0.1:${port}`, `localhost:${port}`].includes(host))
      return { kind: "local", owner: true };
    const tail = tailConfig();
    if (tail.enabled && host === new URL(tail.url).host) {
      const email = String(
        req.headers["tailscale-user-login"] || "",
      ).toLowerCase();
      if (!tail.emails?.includes(email))
        throw Error("Tailscale identity is not allowed");
      return { kind: "tailscale", email, owner: true };
    }
    const identity = await verifyCloudflare(req);
    return {
      ...identity,
      kind: "cloudflare",
      owner: identity.email === sharing.config.ownerEmail,
    };
  }
  function sameOrigin(req) {
    try {
      const origin = new URL(req.headers.origin);
      return (
        origin.host === req.headers.host &&
        (origin.protocol === "https:" ||
          (origin.protocol === "http:" &&
            ["localhost", "127.0.0.1"].includes(origin.hostname)))
      );
    } catch {
      return false;
    }
  }
  return { authenticate, sameOrigin, tailConfig };
}
module.exports = { createAccess };
