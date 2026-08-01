export interface ServerConfig {
  serverUrl: string;
  maxTokens: number;
  temperature: number;
}

const DEFAULT_CONFIG: ServerConfig = {
  serverUrl: "http://127.0.0.1:8000",
  maxTokens: 2048,
  temperature: 0.7,
};

export interface ChatResponse {
  response: string;
  tokens_generated: number;
  tokens_per_second: number;
  model_used: string;
}

export class ApiClient {
  private config: ServerConfig;

  constructor(config: Partial<ServerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  updateConfig(config: Partial<ServerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  get serverUrl(): string {
    return this.config.serverUrl;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.fetchWithTimeout(`${this.config.serverUrl}/health`, { timeout: 5000 });
      const data = await response.json() as { status: string };
      return data.status === "healthy";
    } catch { return false; }
  }

  async fetchJson(path: string, body: object): Promise<any> {
    const r = await fetch(`${this.config.serverUrl}${path}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    return r.json();
  }

  private async fetchWithTimeout(url: string, options: RequestInit & { timeout?: number } = {}): Promise<Response> {
    const { timeout = 60000, ...fetchOptions } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
      return await fetch(url, { ...fetchOptions, signal: fetchOptions.signal || controller.signal });
    } finally {
      clearTimeout(id);
    }
  }
}