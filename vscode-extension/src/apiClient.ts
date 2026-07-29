/**
 * Backend configuration interface.
 */
export interface BackendConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  retryDelay: number;
}

/**
 * Default backend configuration.
 */
export const DEFAULT_BACKEND_CONFIG: BackendConfig = {
  baseUrl: "http://127.0.0.1:8000",
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
};

/**
 * Client for communicating with the CodeForge backend.
 * Uses fetch with AbortController and retry logic.
 */
export class ApiClient {
  private config: BackendConfig;

  constructor(config: Partial<BackendConfig> = {}) {
    this.config = { ...DEFAULT_BACKEND_CONFIG, ...config };
  }

  updateConfig(config: Partial<BackendConfig>): void {
    this.config = { ...this.config, ...config };
  }

  get baseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Explains code in plain English.
   */
  async explainCode(code: string, language: string, signal?: AbortSignal): Promise<string> {
    const prompt = `Explain the following ${language} code in simple terms:\n\n\`\`\`${language}\n${code}\n\`\`\``;
    return this.sendChat(prompt, signal);
  }

  /**
   * Generates code from a description.
   */
  async generateCode(description: string, language: string, signal?: AbortSignal): Promise<string> {
    const prompt = `Generate ${language} code for the following:\n\n${description}\n\nReturn only the code, no explanation.`;
    const response = await this.sendChat(prompt, signal);
    return this.extractCodeBlock(response, language);
  }

  /**
   * Rewrites code to be cleaner and more efficient.
   */
  async rewriteCode(code: string, language: string, signal?: AbortSignal): Promise<string> {
    const prompt = `Rewrite the following ${language} code to be cleaner, more efficient, and follow best practices. Return only the improved code:\n\n\`\`\`${language}\n${code}\n\`\`\``;
    const response = await this.sendChat(prompt, signal);
    return this.extractCodeBlock(response, language);
  }

  /**
   * Sends a chat message with retry logic.
   */
  async sendChat(message: string, signal?: AbortSignal): Promise<string> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retries; attempt++) {
      try {
        return await this._sendChatRequest(message, signal);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // Don't retry on client errors (4xx)
        if (lastError.message.includes("Backend error 4")) {
          throw lastError;
        }

        // Don't retry if cancelled
        if (signal?.aborted) {
          throw lastError;
        }

        // Last attempt — give up
        if (attempt === this.config.retries) {
          throw new Error(
            `Failed after ${this.config.retries + 1} attempts: ${lastError.message}`
          );
        }

        // Wait with exponential backoff before retry
        const delay = this.config.retryDelay * Math.pow(2, attempt);
        await this._sleep(delay);
      }
    }

    throw lastError || new Error("Unknown error");
  }

  /**
   * Single chat request (no retry).
   */
  private async _sendChatRequest(message: string, signal?: AbortSignal): Promise<string> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    if (signal) {
      signal.addEventListener("abort", () => controller.abort());
    }

    try {
      const response = await fetch(`${this.config.baseUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Backend error ${response.status}: ${errorBody}`);
      }

      const data = await response.json() as { response?: string };
      return data.response || "";
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Checks if the backend is reachable.
   */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${this.config.baseUrl}/health/simple`, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) return false;
      const data = await response.json() as { status?: string };
      return data.status === "ok";
    } catch {
      return false;
    }
  }

  /**
   * Extracts code from markdown code blocks.
   */
  private extractCodeBlock(text: string, language: string): string {
    const codeBlockRegex = new RegExp(
      `\`\`\`(?:${language})?\\s*\\n?([\\s\\S]*?)\`\`\``,
      "i"
    );
    const match = text.match(codeBlockRegex);

    if (match && match[1]) {
      return match[1].trim();
    }

    return text.trim();
  }

  /**
   * Sleep for a given number of milliseconds.
   */
  private _sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}