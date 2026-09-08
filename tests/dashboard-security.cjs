const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { RuntimeController } = require("../stream/runtime.cjs");
const { createAccess } = require("../stream/access.cjs");

async function main() {
  const { generateKeyPair, SignJWT } =
    await import("../stream/node_modules/jose/dist/webapi/index.js");
  const { createAccessVerifier, normalizeEmails } =
    await import("../stream/cloudflare/sharing-auth.mjs");
  const { studyUtc, localParts } = await import("../stream/public/scene.js");
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "cleveland-security-"));
  try {
    await fs.mkdir(path.join(root, "Config"));
    await fs.copyFile(
      path.resolve(__dirname, "../Config/gpu-profiles.json"),
      path.join(root, "Config/gpu-profiles.json"),
    );
    const runtime = new RuntimeController(root);
    for (const input of [
      { profile: "Other" },
      { texturePoolMB: -1 },
      { maxFPS: NaN },
      { width: 640.5 },
      { nanitePoolMB: 50000 },
      { rayTracingPoolMB: 0 },
      { maxFPS: 1 },
      { lightingQuality: 5 },
      { virtualShadows: "false" },
    ])
      await assert.rejects(runtime.validate(input));
    const settings = await runtime.save({
      profile: "RTX5090",
      maxFPS: 15,
      rayTracingPoolMB: 1536,
    });
    assert.equal(settings.virtualShadows, true);
    assert.equal((await runtime.settings()).maxFPS, 15);
    assert.equal((await runtime.settings()).rayTracingPoolMB, 1536);
    const cinematic = await runtime.save({
      profile: "Laptop",
      maxFPS: 2,
      lightingQuality: 4,
      virtualShadows: true,
      width: 768,
      height: 432,
    });
    assert.equal(cinematic.lightingQuality, 4);
    assert.equal(cinematic.virtualShadows, true);
    assert.equal((await runtime.settings()).maxFPS, 2);
    assert.equal((await runtime.settings()).width, 768);

    assert.deepEqual(
      normalizeEmails("OWNER@example.test; owner@example.test"),
      ["owner@example.test"],
    );
    for (const emails of ["*@example.test", "example.test", ""])
      assert.throws(() => normalizeEmails(emails));
    const config = {
      enabled: true,
      hostname: "house.example.test",
      authDomain: "team.cloudflareaccess.com",
      audience: "this-app",
      emails: ["owner@example.test"],
      ownerEmail: "owner@example.test",
    };
    const { privateKey, publicKey } = await generateKeyPair("RS256");
    const verify = createAccessVerifier(() => config, {
      resolveKeys: publicKey,
    });
    const token = async (overrides = {}) =>
      new SignJWT({ email: "owner@example.test", ...overrides })
        .setProtectedHeader({ alg: "RS256" })
        .setSubject("test-user")
        .setIssuedAt()
        .setIssuer("https://team.cloudflareaccess.com")
        .setAudience("this-app")
        .setExpirationTime("1h")
        .sign(privateKey);
    const request = (jwt) => ({
      headers: { host: "house.example.test", "cf-access-jwt-assertion": jwt },
      socket: { remoteAddress: "127.0.0.1" },
    });
    const valid = await token();
    assert.equal((await verify(request(valid))).email, "owner@example.test");
    await assert.rejects(verify(request("malformed")));
    await assert.rejects(
      verify(request(await token({ email: "intruder@example.test" }))),
    );
    await assert.rejects(
      verify({
        ...request(valid),
        headers: { ...request(valid).headers, host: "another.example.test" },
      }),
    );
    config.audience = "another-app";
    await assert.rejects(verify(request(valid)));
    config.audience = "this-app";
    const access = createAccess(root, 5190, { config }, verify);
    assert.equal((await access.authenticate(request(valid))).owner, true);
    await assert.rejects(
      access.authenticate({
        ...request(valid),
        socket: { remoteAddress: "192.168.1.8" },
      }),
    );
    const local = {
      headers: { host: "127.0.0.1:5190", origin: "http://127.0.0.1:5190" },
      socket: { remoteAddress: "127.0.0.1" },
    };
    assert.equal(access.sameOrigin(local), true);
    assert.equal(
      access.sameOrigin({
        ...local,
        headers: { ...local.headers, origin: "https://evil.example" },
      }),
      false,
    );
    assert.equal(
      access.sameOrigin({ ...local, headers: { host: "127.0.0.1:5190" } }),
      false,
    );
    config.emails = [];
    await assert.rejects(access.authenticate(request(valid)));
    config.emails = ["owner@example.test"];
    config.enabled = false;
    await assert.rejects(access.authenticate(request(valid)));

    for (const [date, minute, expected] of [
      ["2026-01-15", 720, "2026-01-15T17:00:00.000Z"],
      ["2026-07-15", 720, "2026-07-15T16:00:00.000Z"],
      ["2026-03-08", 540, "2026-03-08T13:00:00.000Z"],
      ["2026-11-01", 540, "2026-11-01T14:00:00.000Z"],
    ]) {
      const utc = studyUtc(date, minute);
      assert.equal(new Date(utc * 1000).toISOString(), expected);
      assert.deepEqual(localParts(utc), { date, minute });
    }
    assert.throws(() => studyUtc("2026-02-30", 720));
    console.log(
      "Dashboard settings, signed access, revocation, origins and DC/DST time checks passed.",
    );
  } finally {
    if (!root.startsWith(path.join(os.tmpdir(), "cleveland-security-")))
      throw Error("Unsafe test cleanup");
    await fs.rm(root, { recursive: true, force: true });
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
