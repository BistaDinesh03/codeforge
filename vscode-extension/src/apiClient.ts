/**
 * Client for communicating with the CodeForge backend.
 * Uses modern fetch API with AbortController for cancellation.
 */
export class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = "http://127.0.0.1:8000", timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
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
   * Sends a chat message to the backend.
   */
  async sendChat(message: string, signal?: AbortSignal): Promise<string> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    // Merge external signal with our timeout
    if (signal) {
      signal.addEventListener("abort", () => controller.abort());
    }

    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
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
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error("Request timed out or was cancelled");
      }
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error("Cannot reach backend. Is the phone server running?");
      }
      throw error;
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

      const response = await fetch(`${this.baseUrl}/health/simple`, {
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
   * Extracts code from markdown code blocks in AI response.
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
}