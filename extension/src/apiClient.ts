/**
 * API Client for CodeForge server communication.
 * Handles all HTTP requests with retry, timeout, and error handling.
 */

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

export class ApiClient {
  private config: ServerConfig;

  constructor(config: Partial<ServerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  updateConfig(config: Partial<ServerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /** Check if server is reachable */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.fetchWithTimeout(
        `${this.config.serverUrl}/health`,
        { timeout: 5000 }
      );
      const data = await response.json() as { status: string };
      return data.status === "healthy";
    } catch {
      return false;
    }
  }

  /** Get server version */
  async getVersion(): Promise<string> {
    const response = await this.fetchWithTimeout(
      `${this.config.serverUrl}/version`
    );
    const data = await response.json() as { version: string };
    return data.version;
  }

  /** Send chat message */
  async chat(message: string, signal?: AbortSignal): Promise<string> {
    const response = await this.fetchWithTimeout(
      `${this.config.serverUrl}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          max_tokens: this.config.maxTokens,
          temperature: this.config.temperature,
        }),
        signal,
      }
    );

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Server error ${response.status}: ${err}`);
    }

    const data = await response.json() as { response: string };
    return data.response;
  }

  /** Explain code */
  async explainCode(code: string, language: string, signal?: AbortSignal): Promise<string> {
    const message = `Explain this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
    return this.chat(message, signal);
  }

  /** Generate code from description */
  async generateCode(description: string, language: string, signal?: AbortSignal): Promise<string> {
    const message = `Write ${language} code that: ${description}\nReturn only the code.`;
    return this.chat(message, signal);
  }

  /** Rewrite/improve code */
  async rewriteCode(code: string, language: string, signal?: AbortSignal): Promise<string> {
    const message = `Rewrite this ${language} code to be cleaner and follow best practices:\n\`\`\`${language}\n${code}\n\`\`\`\nReturn only the improved code.`;
    return this.chat(message, signal);
  }

  /** Fetch with timeout */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit & { timeout?: number } = {}
  ): Promise<Response> {
    const { timeout = 30000, ...fetchOptions } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: fetchOptions.signal || controller.signal,
      });
      return response;
    } finally {
      clearTimeout(id);
    }
  }
}