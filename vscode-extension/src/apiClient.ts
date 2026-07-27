import * as http from "http";

/**
 * Client for communicating with the CodeForge backend.
 * Sends code operations and receives AI responses.
 */
export class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = "http://127.0.0.1:8000", timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Sends code to backend for explanation.
   */
  async explainCode(code: string, language: string): Promise<string> {
    const prompt = `Explain the following ${language} code in simple terms:\n\n\`\`\`${language}\n${code}\n\`\`\``;
    
    const response = await this.sendChat(prompt);
    return response;
  }

  /**
   * Sends a description to generate code.
   */
  async generateCode(description: string, language: string): Promise<string> {
    const prompt = `Generate ${language} code for the following:\n\n${description}\n\nReturn only the code, no explanation.`;
    
    const response = await this.sendChat(prompt);
    return this.extractCodeBlock(response, language);
  }

  /**
   * Sends code to be rewritten/improved.
   */
  async rewriteCode(code: string, language: string): Promise<string> {
    const prompt = `Rewrite the following ${language} code to be cleaner, more efficient, and follow best practices. Return only the improved code:\n\n\`\`\`${language}\n${code}\n\`\`\``;
    
    const response = await this.sendChat(prompt);
    return this.extractCodeBlock(response, language);
  }

  /**
   * Sends a chat message to the backend.
   */
  private sendChat(message: string): Promise<string> {
    return this.httpPost("/chat", { message });
  }

  /**
   * Checks if the backend is reachable.
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.httpGet("/health");
      const data = JSON.parse(response);
      return data.status === "healthy";
    } catch {
      return false;
    }
  }

  /**
   * Extracts code from markdown code blocks in AI response.
   */
  private extractCodeBlock(text: string, language: string): string {
    // Try to extract code between ``` blocks
    const codeBlockRegex = new RegExp(
      `\`\`\`(?:${language})?\\s*\\n?([\\s\\S]*?)\`\`\``,
      "i"
    );
    const match = text.match(codeBlockRegex);

    if (match && match[1]) {
      return match[1].trim();
    }

    // If no code block found, return the whole response
    return text.trim();
  }

  /**
   * HTTP GET request.
   */
  private httpGet(path: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const url = new URL(path, this.baseUrl);

      const options: http.RequestOptions = {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: "GET",
        timeout: this.timeout,
      };

      const req = http.request(options, (res) => {
        let body = "";
        res.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        res.on("end", () => {
          if (res.statusCode === 200) {
            resolve(body);
          } else {
            reject(new Error(`HTTP ${res.statusCode}`));
          }
        });
      });

      req.on("error", reject);
      req.on("timeout", () => {
        req.destroy();
        reject(new Error("Request timed out"));
      });
      req.end();
    });
  }

  /**
   * HTTP POST request with JSON body.
   */
  private httpPost(path: string, data: object): Promise<string> {
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify(data);
      const url = new URL(path, this.baseUrl);

      const options: http.RequestOptions = {
        hostname: url.hostname,
        port: url.port,
        path: url.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(postData),
        },
        timeout: this.timeout,
      };

      const req = http.request(options, (res) => {
        let body = "";
        res.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        res.on("end", () => {
          if (res.statusCode === 200) {
            try {
              const parsed = JSON.parse(body);
              resolve(parsed.response || body);
            } catch {
              resolve(body);
            }
          } else {
            reject(new Error(`Backend returned status ${res.statusCode}`));
          }
        });
      });

      req.on("error", (error) => {
        reject(new Error(`Cannot reach backend: ${error.message}`));
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new Error("Request timed out — is the phone server running?"));
      });

      req.write(postData);
      req.end();
    });
  }
}