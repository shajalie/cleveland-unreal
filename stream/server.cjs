// Local preview bridge using Epic's version-matched signalling implementation.
const http = require('node:http');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '..');
const infrastructure = path.join(root, '.local', 'pixel-streaming-infrastructure');
const upstreamRequire = createRequire(path.join(infrastructure, 'package.json'));
const express = upstreamRequire('express');
const { SignallingServer, InitLogging } = upstreamRequire('@epicgames-ps/lib-pixelstreamingsignalling-ue5.8');
const playerPort = Number(process.env.CLEVELAND_PLAYER_PORT || 5190);
const streamerPort = Number(process.env.CLEVELAND_STREAMER_PORT || 5191);
for (const port of [playerPort, streamerPort]) {
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw Error('Invalid preview port');
}
InitLogging({ logLevelConsole: 'info', logLevelFile: 'info', logDir: path.join(root, '.local', 'pixel-streaming-logs') });
const app = express();
app.disable('x-powered-by');
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Cache-Control', 'no-store');
  if (!['localhost', '127.0.0.1'].includes(req.hostname)) return res.sendStatus(403);
  next();
});
app.get('/health', (req, res) => res.json({ service: 'Cleveland Unreal preview', mode: 'loopback-only', playerPort, streamerPort }));
app.use(express.static(path.join(infrastructure, 'SignallingWebServer', 'www'), { index: 'player.html', dotfiles: 'deny' }));
const server = http.createServer(app);
new SignallingServer({
  httpServer: server,
  streamerPort,
  streamerWsOptions: { host: '127.0.0.1' },
  playerWsOptions: {
    verifyClient: ({ origin }) => {
      try {
        const url = new URL(origin);
        return url.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(url.hostname) && url.port === String(playerPort);
      } catch { return false; }
    },
  },
  peerOptions: { iceServers: [] },
  maxSubscribers: 2,
  playerKeepaliveTimeout: 30000,
});
server.listen(playerPort, '127.0.0.1', () => console.log(`Cleveland preview: http://127.0.0.1:${playerPort}`));
