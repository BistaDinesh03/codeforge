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

  async getVersion(): Promise<string> {
    const response = await this.fetchWithTimeout(`${this.config.serverUrl}/version`);
    const data = await response.json() as { version: string };
    return data.version;
  }

  async chat(message: string, signal?: AbortSignal): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.serverUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
      }),
      signal,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server error ${response.status}: ${err}`);
    }
    return response.json() as Promise<ChatResponse>;
  }

  async explainCode(code: string, language: string, signal?: AbortSignal): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.serverUrl}/chat/explain?language=${language}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language }),
      signal,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server error ${response.status}: ${err}`);
    }
    return response.json() as Promise<ChatResponse>;
  }

  async generateCode(description: string, language: string, signal?: AbortSignal): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.serverUrl}/chat/generate?language=${language}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description, language }),
      signal,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server error ${response.status}: ${err}`);
    }
    return response.json() as Promise<ChatResponse>;
  }

  async rewriteCode(code: string, language: string, signal?: AbortSignal): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.serverUrl}/chat/rewrite?language=${language}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language }),
      signal,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server error ${response.status}: ${err}`);
    }
    return response.json() as Promise<ChatResponse>;
  }

  private async fetchWithTimeout(url: string, options: RequestInit & { timeout?: number } = {}): Promise<Response> {
    const { timeout = 30000, ...fetchOptions } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
      return await fetch(url, { ...fetchOptions, signal: fetchOptions.signal || controller.signal });
    } finally {
      clearTimeout(id);
    }
  }
}