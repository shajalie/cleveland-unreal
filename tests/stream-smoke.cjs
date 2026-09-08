const assert = require("node:assert/strict");
const http = require("node:http");
const path = require("node:path");
const { createRequire } = require("node:module");
const upstream = createRequire(
  path.resolve(
    __dirname,
    "../.local/pixel-streaming-infrastructure/package.json",
  ),
);
const WebSocket = upstream("ws");

async function main() {
  const health = await (await fetch("http://127.0.0.1:5190/health")).json();
  assert.equal(health.mode, "authenticated-proxies");
  assert.equal((await fetch("http://127.0.0.1:5190/")).status, 200);
  const blockedHost = await new Promise((resolve, reject) => {
    http
      .get(
        "http://127.0.0.1:5190/",
        { headers: { Host: "untrusted.example" } },
        (res) => {
          res.resume();
          resolve(res.statusCode);
        },
      )
      .on("error", reject);
  });
  assert.equal(blockedHost, 403);
  assert.equal(
    (
      await fetch("http://127.0.0.1:5190/api/runtime/save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Origin: "https://untrusted.example",
        },
        body: "{}",
      })
    ).status,
    403,
  );
  await new Promise((resolve, reject) => {
    const ws = new WebSocket("ws://127.0.0.1:5190", {
      origin: "https://untrusted.example",
    });
    const timer = setTimeout(() => {
      ws.terminate();
      reject(Error("Origin rejection timed out"));
    }, 3000);
    ws.on("open", () => {
      clearTimeout(timer);
      ws.close();
      reject(Error("Untrusted origin accepted"));
    });
    ws.on("unexpected-response", (_, res) => {
      clearTimeout(timer);
      res.resume();
      ws.terminate();
      try {
        assert.equal(res.statusCode, 401);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
    ws.on("error", () => {});
  });
  await new Promise((resolve, reject) => {
    const ws = new WebSocket("ws://127.0.0.1:5190", {
      origin: "http://127.0.0.1:5190",
    });
    const timer = setTimeout(() => {
      ws.terminate();
      reject(Error("Signalling config timed out"));
    }, 3000);
    ws.on("message", (data) => {
      const message = JSON.parse(data.toString());
      if (message.type !== "config") return;
      clearTimeout(timer);
      ws.close();
      resolve();
    });
    ws.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });
  console.log(
    "Preview health, page, host restriction and WebSocket origin/config checks passed.",
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
