class TurnRelay {
  constructor(sharing) {
    this.sharing = sharing;
    this.options = { iceServers: [{ urls: "stun:stun.cloudflare.com:3478" }] };
    this.ready = false;
    this.error = "";
  }
  async refresh() {
    try {
      const secrets = await this.sharing.readSecrets();
      if (!secrets.turnKeyId || !secrets.turnKey) {
        this.error = "Cloudflare video relay has not been connected";
        return;
      }
      const response = await fetch(
        `https://rtc.live.cloudflare.com/v1/turn/keys/${secrets.turnKeyId}/credentials/generate-ice-servers`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${secrets.turnKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ttl: 86400 }),
          signal: AbortSignal.timeout(15000),
        },
      );
      if (!response.ok) throw Error("Video relay credential request failed");
      const result = await response.json();
      if (!Array.isArray(result.iceServers))
        throw Error("Invalid video relay response");
      this.options = { iceServers: result.iceServers };
      this.ready = true;
      this.error = "";
    } catch (error) {
      this.ready = false;
      this.error = error.message;
    }
  }
}
module.exports = { TurnRelay };
