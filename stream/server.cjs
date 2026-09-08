const http = require("node:http");
const path = require("node:path");
const { createRequire } = require("node:module");
const { pathToFileURL } = require("node:url");
const { execFile } = require("node:child_process");
const { promisify } = require("node:util");
const { createHash } = require("node:crypto");
const { RuntimeController } = require("./runtime.cjs");
const { createAccess } = require("./access.cjs");
const { TurnRelay } = require("./turn.cjs");
const root = path.resolve(__dirname, "..");
const instance = createHash("sha256")
  .update(root.toLowerCase())
  .digest("hex")
  .slice(0, 16);
const infrastructure = path.join(root, ".local/pixel-streaming-infrastructure");
const upstream = createRequire(path.join(infrastructure, "package.json"));
const express = upstream("express");
const { SignallingServer, InitLogging } = upstream(
  "@epicgames-ps/lib-pixelstreamingsignalling-ue5.8",
);
const playerPort = Number(process.env.CLEVELAND_PLAYER_PORT || 5190);
const streamerPort = Number(process.env.CLEVELAND_STREAMER_PORT || 5191);
for (const port of [playerPort, streamerPort])
  if (!Number.isInteger(port) || port < 1024 || port > 65535)
    throw Error("Invalid preview port");

async function main() {
  const { SharingManager } = await import(
    pathToFileURL(path.join(__dirname, "cloudflare/sharing.mjs"))
  );
  const { createAccessVerifier } = await import(
    pathToFileURL(path.join(__dirname, "cloudflare/sharing-auth.mjs"))
  );
  const connections = new Map();
  const sharing = await new SharingManager(root, {
    originPort: playerPort,
    onChange: () => {
      for (const [socket, identity] of connections)
        if (identity.kind === "cloudflare") socket.destroy();
    },
  }).init();
  const access = createAccess(
    root,
    playerPort,
    sharing,
    createAccessVerifier(() => sharing.config),
  );
  const runtime = new RuntimeController(root);
  const relay = new TurnRelay(sharing);
  await relay.refresh();
  setInterval(() => relay.refresh(), 3600000).unref();
  InitLogging({
    logLevelConsole: "info",
    logLevelFile: "info",
    logDir: path.join(root, ".local/pixel-streaming-logs"),
  });
  const app = express();
  app.disable("x-powered-by");
  app.use((req, res, next) => {
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Referrer-Policy", "same-origin");
    next();
  });
  app.use(async (req, res, next) => {
    try {
      req.identity = await access.authenticate(req);
      next();
    } catch {
      res
        .status(403)
        .send(
          "Sign in with an allowed email or open this PC’s local dashboard.",
        );
    }
  });
  app.use(express.json({ limit: "16kb" }));
  app.use((req, res, next) => {
    if (req.method !== "GET" && !access.sameOrigin(req))
      return res.sendStatus(403);
    next();
  });
  const server = http.createServer(app);
  const signalling = new SignallingServer({
    httpServer: server,
    streamerPort,
    streamerWsOptions: { host: "127.0.0.1" },
    peerOptions: { iceServers: [] },
    peerOptionsProvider: () => relay.options,
    maxSubscribers: 4,
    playerKeepaliveTimeout: 30000,
    playerWsOptions: {
      verifyClient: (info, done) => {
        if (!access.sameOrigin(info.req)) return done(false, 401);
        access
          .authenticate(info.req)
          .then((identity) => {
            connections.set(info.req.socket, identity);
            let expiry;
            if (identity.expires)
              expiry = setTimeout(
                () => info.req.socket.destroy(),
                Math.max(1, identity.expires * 1000 - Date.now()),
              ).unref();
            info.req.socket.once("close", () => {
              connections.delete(info.req.socket);
              if (expiry) clearTimeout(expiry);
            });
            done(true);
          })
          .catch(() => done(false, 401));
      },
    },
  });
  app.get("/health", (req, res) =>
    res.json({
      service: "Cleveland Unreal preview",
      instance,
      mode: "authenticated-proxies",
      playerPort,
      streamerPort,
    }),
  );
  app.get("/api/status", async (req, res, next) => {
    try {
      const share = sharing.status();
      res.json({
        settings: await runtime.settings(),
        profiles: await runtime.catalog(),
        power: await runtime
          .power()
          .catch(() => ({ name: "Unavailable", canRestore: false })),
        rendererConnected: !signalling.streamerRegistry.empty(),
        viewers: signalling.playerRegistry.count(),
        job: runtime.job,
        owner: req.identity.owner,
        transport: req.identity.kind,
        sharing: req.identity.owner
          ? share
          : { enabled: share.enabled, url: share.url },
        tailscale: {
          enabled: access.tailConfig().enabled,
          url: access.tailConfig().url,
        },
        relay: { ready: relay.ready, error: relay.error },
      });
    } catch (error) {
      next(error);
    }
  });
  app.post("/api/runtime/:action", async (req, res, next) => {
    try {
      if (!req.identity.owner) return res.sendStatus(403);
      const action = req.params.action;
      if (!["start", "stop", "restart", "save"].includes(action))
        return res.sendStatus(400);
      if (action === "save")
        return res.json({ settings: await runtime.save(req.body) });
      if (req.body.settings) await runtime.validate(req.body.settings);
      runtime.run(action, req.body.settings);
      res.status(202).json({ accepted: true });
    } catch (error) {
      next(error);
    }
  });
  app.post("/api/power/:mode", async (req, res, next) => {
    try {
      if (!req.identity.owner) return res.sendStatus(403);
      const actions = {
        balanced: "Balanced",
        performance: "Performance",
        restore: "Restore",
      };
      if (!Object.hasOwn(actions, req.params.mode)) return res.sendStatus(400);
      res.json(await runtime.power(actions[req.params.mode]));
    } catch {
      next(
        Error(
          "Windows could not change the power plan. Check the rendering PC.",
        ),
      );
    }
  });
  app.post("/api/sharing/:action", async (req, res, next) => {
    try {
      if (!req.identity.owner) return res.sendStatus(403);
      switch (req.params.action) {
        case "emails":
          sharing.run(() => sharing.updateEmails(req.body.emails));
          break;
        case "enable":
          sharing.run(async () => {
            sharing.config.enabled = true;
            await sharing.save();
            await sharing.resume();
          });
          break;
        case "disable":
          sharing.run(() => sharing.disable());
          break;
        case "configure":
          sharing.run(() => sharing.configure(req.body));
          break;
        case "relay":
          sharing.run(async () => {
            await sharing.configureRelay(req.body);
            await relay.refresh();
            if (!relay.ready) throw Error(relay.error);
          });
          break;
        default:
          return res.sendStatus(400);
      }
      res.status(202).json({ accepted: true });
    } catch (error) {
      next(error);
    }
  });
  app.post("/api/tailscale/:action", async (req, res, next) => {
    try {
      if (!req.identity.owner) return res.sendStatus(403);
      if (!["enable", "disable"].includes(req.params.action))
        return res.sendStatus(400);
      const { stdout } = await promisify(execFile)(
        "powershell.exe",
        [
          "-NoProfile",
          "-File",
          path.join(root, "pipeline/phone-access.ps1"),
          "-Action",
          req.params.action,
        ],
        { windowsHide: true, timeout: 30000 },
      );
      res.json(JSON.parse(stdout));
    } catch (error) {
      next(error);
    }
  });
  app.use(
    "/vendor",
    express.static(path.join(infrastructure, "SignallingWebServer/www"), {
      dotfiles: "deny",
    }),
  );
  app.use(
    express.static(path.join(__dirname, "public"), {
      index: "index.html",
      dotfiles: "deny",
    }),
  );
  app.use((error, req, res, next) => {
    res.status(400).json({ error: error.message });
  });
  server.listen(playerPort, "127.0.0.1", () =>
    console.log(`Cleveland dashboard: http://127.0.0.1:${playerPort}`),
  );
  await sharing.resume();
  for (const signal of ["SIGINT", "SIGTERM"])
    process.on(signal, async () => {
      await sharing.stopProcess();
      server.close();
      process.exit(0);
    });
}
main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
