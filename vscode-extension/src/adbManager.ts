import * as vscode from "vscode";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Structured result from ADB operations.
 * Never returns silent failures — always has a message.
 */
export interface AdbResult {
  success: boolean;
  errorCode?: "ADB_NOT_FOUND" | "NO_DEVICE" | "UNAUTHORIZED" | "PORT_CONFLICT" | "BACKEND_UNREACHABLE" | "TIMEOUT";
  message: string;
  deviceId?: string;
}

/**
 * Manages ADB connection between VS Code and Android device.
 * Every method returns structured AdbResult — no silent failures.
 */
export class AdbManager {
  private _isConnected: boolean = false;
  private _deviceId: string | null = null;

  /**
   * Checks if ADB is installed and available.
   */
  async isAdbAvailable(): Promise<AdbResult> {
    try {
      const { stdout } = await execAsync("adb version");
      const version = stdout.split("\n")[0].trim();
      return {
        success: true,
        message: `ADB found: ${version}`,
      };
    } catch {
      return {
        success: false,
        errorCode: "ADB_NOT_FOUND",
        message: "ADB is not installed. Run: winget install Google.PlatformTools",
      };
    }
  }

  /**
   * Checks if a device is connected and authorized via USB.
   */
  async isDeviceConnected(): Promise<AdbResult> {
    try {
      const { stdout } = await execAsync("adb devices");
      const lines = stdout.trim().split("\n");

      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        const parts = line.split("\t");
        const deviceId = parts[0];
        const status = parts[1] || "";

        if (status === "device") {
          this._deviceId = deviceId;
          return {
            success: true,
            message: `Device connected: ${deviceId}`,
            deviceId: deviceId,
          };
        }

        if (status === "unauthorized") {
          return {
            success: false,
            errorCode: "UNAUTHORIZED",
            message: "Device found but not authorized. Check your phone and tap 'Allow USB debugging'.",
            deviceId: deviceId,
          };
        }

        if (status === "offline") {
          return {
            success: false,
            errorCode: "NO_DEVICE",
            message: "Device is offline. Reconnect USB cable and try again.",
            deviceId: deviceId,
          };
        }
      }

      return {
        success: false,
        errorCode: "NO_DEVICE",
        message: "No Android device found. Connect via USB and enable USB debugging in Developer Options.",
      };
    } catch (error) {
      return {
        success: false,
        errorCode: "ADB_NOT_FOUND",
        message: `ADB error: ${error instanceof Error ? error.message : "Unknown error"}`,
      };
    }
  }

  /**
   * Sets up port forwarding from localhost to Android device.
   */
  async forwardPort(localPort: number = 8000, remotePort: number = 8000): Promise<AdbResult> {
    try {
      // Check if port is already forwarded
      const { stdout } = await execAsync("adb forward --list");
      if (stdout.includes(`tcp:${localPort}`)) {
        // Already forwarded — that's fine
        this._isConnected = true;
        return {
          success: true,
          message: `Port ${localPort} already forwarded`,
        };
      }

      await execAsync(`adb forward tcp:${localPort} tcp:${remotePort}`);
      this._isConnected = true;
      return {
        success: true,
        message: `Port ${localPort} forwarded to device port ${remotePort}`,
      };
    } catch (error) {
      this._isConnected = false;
      return {
        success: false,
        errorCode: "PORT_CONFLICT",
        message: `Failed to forward port: ${error instanceof Error ? error.message : "Unknown error"}`,
      };
    }
  }

  /**
   * Removes port forwarding.
   */
  async removeForward(localPort: number = 8000): Promise<AdbResult> {
    try {
      await execAsync(`adb forward --remove tcp:${localPort}`);
      this._isConnected = false;
      return { success: true, message: `Port ${localPort} forwarding removed` };
    } catch {
      this._isConnected = false;
      return { success: true, message: "Port forwarding cleaned up" };
    }
  }

  /**
   * Checks if the backend is reachable on the forwarded port.
   */
  async isBackendReachable(port: number = 8000): Promise<AdbResult> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch(`http://127.0.0.1:${port}/health/simple`, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return {
          success: false,
          errorCode: "BACKEND_UNREACHABLE",
          message: `Backend returned status ${response.status}. Start the server on your phone.`,
        };
      }

      const data = await response.json() as { status?: string };
      if (data.status === "ok") {
        return {
          success: true,
          message: "Backend is healthy and responding",
        };
      }

      return {
        success: false,
        errorCode: "BACKEND_UNREACHABLE",
        message: "Backend responded but status is not healthy",
      };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof DOMException && error.name === "AbortError") {
        return {
          success: false,
          errorCode: "TIMEOUT",
          message: "Backend did not respond within 5 seconds. Check if server is running on your phone.",
        };
      }
      return {
        success: false,
        errorCode: "BACKEND_UNREACHABLE",
        message: `Cannot reach backend: ${error instanceof Error ? error.message : "Connection failed"}`,
      };
    }
  }

  /**
   * Full connection flow with clear error messages at each step.
   */
  async connect(): Promise<AdbResult> {
    // Step 1: Check ADB
    const adbCheck = await this.isAdbAvailable();
    if (!adbCheck.success) {
      vscode.window.showErrorMessage(`CodeForge: ${adbCheck.message}`);
      return adbCheck;
    }

    // Step 2: Check device
    const deviceCheck = await this.isDeviceConnected();
    if (!deviceCheck.success) {
      vscode.window.showErrorMessage(`CodeForge: ${deviceCheck.message}`);
      return deviceCheck;
    }

    // Step 3: Forward port
    const forwardResult = await this.forwardPort();
    if (!forwardResult.success) {
      vscode.window.showErrorMessage(`CodeForge: ${forwardResult.message}`);
      return forwardResult;
    }

    // Step 4: Verify backend
    const backendCheck = await this.isBackendReachable();
    if (!backendCheck.success) {
      vscode.window.showWarningMessage(`CodeForge: ${backendCheck.message}`);
      return backendCheck;
    }

    vscode.window.showInformationMessage("CodeForge: Connected! Your phone AI server is ready.");
    return { success: true, message: "Fully connected to Android AI server", deviceId: this._deviceId || undefined };
  }

  /**
   * Disconnects and cleans up.
   */
  async disconnect(): Promise<AdbResult> {
    const result = await this.removeForward();
    this._isConnected = false;
    this._deviceId = null;

    if (result.success) {
      vscode.window.showInformationMessage("CodeForge: Disconnected from Android");
    }
    return result;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  get deviceId(): string | null {
    return this._deviceId;
  }
}