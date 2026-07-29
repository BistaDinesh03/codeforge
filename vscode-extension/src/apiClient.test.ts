/**
 * Tests for ApiClient.
 * Uses fetch mocking to avoid real network calls.
 */

import { ApiClient, BackendConfig } from "./apiClient";

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

function createMockResponse(body: object, status: number = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("ApiClient", () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient();
    mockFetch.mockReset();
  });

  describe("constructor", () => {
    it("should use default config", () => {
      expect(client.baseUrl).toBe("http://127.0.0.1:8000");
    });

    it("should accept custom config", () => {
      const custom = new ApiClient({ baseUrl: "http://localhost:9000" });
      expect(custom.baseUrl).toBe("http://localhost:9000");
    });
  });

  describe("sendChat", () => {
    it("should return response text on success", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ response: "Hello from AI" })
      );

      const result = await client.sendChat("Hi");
      expect(result).toBe("Hello from AI");
    });

    it("should throw on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ detail: "Bad request" }, 400)
      );

      await expect(client.sendChat("")).rejects.toThrow("Backend error 400");
    });

    it("should throw on network error", async () => {
      const noRetryClient = new ApiClient({ retries: 0 });
      mockFetch.mockRejectedValueOnce(new TypeError("fetch failed"));

      await expect(noRetryClient.sendChat("Hi")).rejects.toThrow("fetch failed");
    });

    it("should retry on server errors", async () => {
      mockFetch
        .mockResolvedValueOnce(createMockResponse({}, 500))
        .mockResolvedValueOnce(createMockResponse({}, 500))
        .mockResolvedValueOnce(createMockResponse({ response: "OK" }));

      const fastClient = new ApiClient({ retries: 2, retryDelay: 10 });
      const result = await fastClient.sendChat("Hi");
      expect(result).toBe("OK");
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });

  describe("healthCheck", () => {
    it("should return true on healthy response", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ status: "ok" })
      );

      const result = await client.healthCheck();
      expect(result).toBe(true);
    });

    it("should return false on error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("fail"));

      const result = await client.healthCheck();
      expect(result).toBe(false);
    });
  });

  describe("generateCode", () => {
    it("should extract code from markdown block", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          response: "```typescript\nconst x = 1;\n```"
        })
      );

      const result = await client.generateCode("create variable", "typescript");
      expect(result).toBe("const x = 1;");
    });

    it("should return raw text if no code block", async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ response: "Here is some code: x = 1" })
      );

      const result = await client.generateCode("create variable", "python");
      expect(result).toBe("Here is some code: x = 1");
    });
  });
});