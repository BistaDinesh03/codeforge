import * as vscode from "vscode";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Manages ADB connection between VS Code and Android device.
 * Handles device detection, port forwarding, and connection status.
 */
export class AdbManager {
  private _isConnected: boolean = false;
  private _deviceId: string | null = null;

  /**
   * Checks if ADB is installed and available.
   */
  async isAdbAvailable(): Promise<boolean> {
    try {
      await execAsync("adb version");
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Checks if a device is connected via USB.
   */
  async isDeviceConnected(): Promise<boolean> {
    try {
      const { stdout } = await execAsync("adb devices");
      const lines = stdout.trim().split("\n");
      // First line is header, check if any device is listed
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line && !line.includes("offline")) {
          const parts = line.split("\t");
          if (parts.length === 2 && parts[1] === "device") {
            this._deviceId = parts[0];
            return true;
          }
        }
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Sets up port forwarding from localhost to Android device.
   * localhost:8000 -> Android:8000
   */
  async forwardPort(
    localPort: number = 8000,
    remotePort: number = 8000
  ): Promise<void> {
    try {
      await execAsync(`adb forward tcp:${localPort} tcp:${remotePort}`);
      this._isConnected = true;
      vscode.window.showInformationMessage(
        `CodeForge: Connected to Android on port ${localPort}`
      );
    } catch (error) {
      this._isConnected = false;
      throw new Error(
        `Failed to forward port: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  }

  /**
   * Removes port forwarding.
   */
  async removeForward(localPort: number = 8000): Promise<void> {
    try {
      await execAsync(
        `adb forward --remove tcp:${localPort}`
      );
      this._isConnected = false;
    } catch {
      // Port might not be forwarded, ignore
    }
  }

  /**
   * Checks if the backend is reachable on the forwarded port.
   */
  async isBackendReachable(port: number = 8000): Promise<boolean> {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`);
      const data = await response.json() as { status: string };
      return data.status === "healthy";
    } catch {
      return false;
    }
  }

  /**
   * Full connection flow:
   * 1. Check ADB available
   * 2. Check device connected
   * 3. Forward port
   * 4. Verify backend reachable
   */
  async connect(): Promise<boolean> {
    // Step 1: Check ADB
    if (!(await this.isAdbAvailable())) {
      vscode.window.showErrorMessage(
        "CodeForge: ADB is not installed. Run: winget install Google.PlatformTools"
      );
      return false;
    }

    // Step 2: Check device
    if (!(await this.isDeviceConnected())) {
      vscode.window.showErrorMessage(
        "CodeForge: No Android device found. Connect via USB and enable USB debugging."
      );
      return false;
    }

    // Step 3: Forward port
    try {
      await this.forwardPort();
    } catch (error) {
      vscode.window.showErrorMessage(
        `CodeForge: ${error instanceof Error ? error.message : "Connection failed"}`
      );
      return false;
    }

    // Step 4: Verify backend
    if (!(await this.isBackendReachable())) {
      vscode.window.showWarningMessage(
        "CodeForge: Connected to phone, but backend is not running. Start the server in Termux."
      );
      return false;
    }

    return true;
  }

  /**
   * Disconnects and cleans up.
   */
  async disconnect(): Promise<void> {
    await this.removeForward();
    this._isConnected = false;
    this._deviceId = null;
    vscode.window.showInformationMessage(
      "CodeForge: Disconnected from Android"
    );
  }

  /**
   * Returns current connection status.
   */
  get isConnected(): boolean {
    return this._isConnected;
  }
}