import * as dgram from "dgram";
import { EventEmitter } from "events";

export interface DiscoveredServer {
  host: string;
  port: number;
  version: string;
  name: string;
}

const BROADCAST_PORT = 45678;

/**
 * Listens for CodeForge server broadcasts on the local network.
 * Emits 'found' event when a server is discovered.
 */
export class ServerDiscovery extends EventEmitter {
  private socket: dgram.Socket | null = null;
  private listening: boolean = false;

  /**
   * Start listening for server broadcasts.
   * Resolves with the first discovered server, or rejects after timeout.
   */
  async discover(timeoutMs: number = 10000): Promise<DiscoveredServer> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.stop();
        reject(new Error(
          "No CodeForge server found on your network.\n\n" +
          "Make sure:\n" +
          "1. The server is running on another computer\n" +
          "2. Both computers are on the same WiFi network\n" +
          "3. No firewall is blocking UDP port " + BROADCAST_PORT
        ));
      }, timeoutMs);

      this.once("found", (server: DiscoveredServer) => {
        clearTimeout(timeout);
        this.stop();
        resolve(server);
      });

      this.start();
    });
  }

  /**
   * Start listening without promise (continuous mode).
   */
  start(): void {
    if (this.listening) return;

    this.socket = dgram.createSocket({ type: "udp4", reuseAddr: true });

    this.socket.on("message", (msg: Buffer, rinfo: dgram.RemoteInfo) => {
      try {
        const data = JSON.parse(msg.toString());
        if (data.service === "codeforge") {
          const server: DiscoveredServer = {
            host: data.host,
            port: data.port,
            version: data.version,
            name: data.name,
          };
          this.emit("found", server);
        }
      } catch {
        // Ignore malformed packets
      }
    });

    this.socket.on("error", (err: Error) => {
      console.log("Discovery error:", err.message);
    });

    this.socket.bind(BROADCAST_PORT, () => {
      this.listening = true;
      console.log("Discovery: listening for CodeForge servers...");
    });
  }

  /**
   * Stop listening.
   */
  stop(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.listening = false;
  }
}